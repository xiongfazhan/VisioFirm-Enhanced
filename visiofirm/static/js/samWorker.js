import {
  env,
  SamModel,
  AutoProcessor,
  RawImage,
  Tensor
} from "https://cdn.jsdelivr.net/npm/@huggingface/transformers/dist/transformers.min.js";

let model = null;
let processor = null;
let cachedEmbeddings = null; // { embeddings, imageId, original_sizes, reshaped_input_sizes }

async function init() {
  console.log('Worker: Initializing SAM model...');
  const model_id = "Xenova/slimsam-77-uniform";

  // Multi-threading for WASM
  if (typeof SharedArrayBuffer !== 'undefined') {
    env.backends.onnx.wasm.numThreads = Math.min(navigator.hardwareConcurrency || 4, 8);
  } else {
    env.backends.onnx.wasm.numThreads = 1; // Fallback
  }
  env.backends.onnx.wasm.simd = true;
  env.backends.onnx.wasm.proxy = true;

  async function isWebGPUSupported() {
    if (!navigator.gpu) return false;
    try {
      const adapter = await navigator.gpu.requestAdapter();
      return !!adapter;
    } catch (e) {
      console.warn('Worker: WebGPU adapter request failed:', e);
      return false;
    }
  }

  const useWebGPU = await isWebGPUSupported();
  const device = useWebGPU ? "webgpu" : "wasm";

  try {
    model = await SamModel.from_pretrained(model_id, { dtype: "fp32", device });
    processor = await AutoProcessor.from_pretrained(model_id);
    postMessage({ status: 'ready' });
    console.log(`Worker: SAM loaded using ${device} backend`);
  } catch (e) {
    postMessage({ status: 'error', message: e.message });
    console.error('Worker: Failed to load SAM:', e);
  }
}

async function precomputeEmbeddings(imageBuffer, width, height, imageId) {
  const startTime = performance.now();
  try {
    // Reconstruct image data
    const pixelData = new Uint8ClampedArray(imageBuffer);
    const imageInput = new RawImage(pixelData, width, height, 4); // RGBA

    console.log('Worker: Pre-computing embeddings for image');
    const imageProcessed = await processor(imageInput);
    const embeddings = await model.get_image_embeddings(imageProcessed);
    cachedEmbeddings = {
      embeddings,
      imageId,
      original_sizes: imageProcessed.original_sizes,
      reshaped_input_sizes: imageProcessed.reshaped_input_sizes
    };

    const endTime = performance.now();
    const duration = (endTime - startTime) / 1000;
    postMessage({
      status: 'precompute-complete',
      imageId,
      duration: duration.toFixed(2)
    });
    console.log(`Worker: Embeddings pre-computed in ${duration.toFixed(2)}s`);
  } catch (e) {
    postMessage({ status: 'error', message: e.message });
    console.error('Worker: Pre-compute failed:', e);
  }
}

async function segment(point, imageBuffer, width, height, imageId, setupType, selectedClass) {
  const startTime = performance.now();

  try {
    // Reconstruct image data
    const pixelData = new Uint8ClampedArray(imageBuffer);
    let imageInput = new RawImage(pixelData, width, height, 4); // RGBA

    let imageProcessedLocal;
    if (!cachedEmbeddings || cachedEmbeddings.imageId !== imageId) {
      console.log('Worker: Computing embeddings (cache miss)');
      imageProcessedLocal = await processor(imageInput);
      cachedEmbeddings = {
        embeddings: await model.get_image_embeddings(imageProcessedLocal),
        imageId,
        original_sizes: imageProcessedLocal.original_sizes,
        reshaped_input_sizes: imageProcessedLocal.reshaped_input_sizes
      };
    } else {
      console.log('Worker: Using cached embeddings');
      imageProcessedLocal = await processor(imageInput); // For sizes
    }

    const reshaped = imageProcessedLocal.reshaped_input_sizes[0];
    const pointsArray = [
      point.x * reshaped[1] / width,
      point.y * reshaped[0] / height
    ];
    const labelsArray = [1n];
    const input_points = new Tensor("float32", pointsArray, [1, 1, 1, 2]);
    const input_labels = new Tensor("int64", labelsArray, [1, 1, 1]);

    const { pred_masks, iou_scores } = await model({
      ...cachedEmbeddings.embeddings,
      input_points,
      input_labels
    });

    const masks = await processor.post_process_masks(
      pred_masks,
      cachedEmbeddings.original_sizes,
      cachedEmbeddings.reshaped_input_sizes
    );

    const maskTensor = masks[0][0]; // [num_masks, h, w]
    const maskData = maskTensor.data;
    const numMasks = iou_scores.dims[1];
    const scores = iou_scores.data;
    let bestIndex = 0;
    for (let i = 1; i < scores.length; i++) {
      if (scores[i] > scores[bestIndex]) bestIndex = i;
    }

    const maskWidth = maskTensor.dims[2];
    const maskHeight = maskTensor.dims[1];
    const maskStride = maskHeight * maskWidth;

    // Compute bbox (for rect/obbox)
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (let y = 0; y < maskHeight; y++) {
      for (let x = 0; x < maskWidth; x++) {
        const pixelIndex = y * maskWidth + x;
        const value = maskData[bestIndex * maskStride + pixelIndex];
        if (value > 0.5) {
          minX = Math.min(minX, x);
          minY = Math.min(minY, y);
          maxX = Math.max(maxX, x);
          maxY = Math.max(maxY, y);
        }
      }
    }

    if (minX === Infinity) {
      postMessage({ status: 'no-mask', score: 0 });
      return;
    }

    let result;
    if (setupType === 'Segmentation') {
      const contour = extractContour(maskData, maskWidth, maskHeight, numMasks, bestIndex);
      if (contour.length > 2) {
        const simplifiedContour = simplifyPolygon(contour, 2);
        result = {
          type: 'polygon',
          points: simplifiedContour,
          closed: true,
          label: selectedClass
        };
      }
    } else {
      result = {
        type: setupType === "Oriented Bounding Box" ? 'obbox' : 'rect',
        x: minX,
        y: minY,
        width: maxX - minX + 1,
        height: maxY - minY + 1,
        rotation: 0,
        label: selectedClass
      };
    }

    const endTime = performance.now();
    const duration = (endTime - startTime) / 1000;
    postMessage({
      status: 'complete',
      result,
      duration: duration.toFixed(2),
      score: scores[bestIndex].toFixed(2)
    });
  } catch (e) {
    postMessage({ status: 'error', message: e.message });
    console.error('Worker: Segmentation failed:', e);
  }
}

function extractContour(maskData, width, height, numMasks, bestIndex) {
  let startX = -1, startY = -1;
  const maskStride = height * width;
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (maskData[bestIndex * maskStride + (y * width + x)] > 0.5 && (x === 0 || maskData[bestIndex * maskStride + (y * width + x - 1)] <= 0.5)) {
        startX = x;
        startY = y;
        break;
      }
    }
    if (startX !== -1) break;
  }
  if (startX === -1) return [];

  function getValue(x, y) {
    if (x < 0 || x >= width || y < 0 || y >= height) return 0;
    return maskData[bestIndex * maskStride + (y * width + x)] > 0.5 ? 1 : 0;
  }

  const contour = [];
  const dirDelta = [[1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 1], [1, 1]];
  let x = startX, y = startY;
  let dir = 6; // Start downwards
  contour.push({ x, y });

  while (true) {
    let found = false;
    for (let offset = 0; offset < 8; offset++) {
      const newDir = (dir + offset - 2 + 8) % 8; // Prefer left turns
      const nx = x + dirDelta[newDir][0];
      const ny = y + dirDelta[newDir][1];
      if (getValue(nx, ny) === 1) {
        x = nx;
        y = ny;
        dir = newDir;
        contour.push({ x, y });
        found = true;
        break;
      }
    }
    if (!found || (x === startX && y === startY && contour.length > 1)) break;
  }

  return contour;
}

function simplifyPolygon(points, epsilon) {
  if (points.length < 3) return points;

  function rdp(points, epsilon, start = 0, end = points.length - 1) {
    if (end - start < 2) return [points[start], points[end]];

    let maxDist = 0;
    let index = start + 1;

    const sx = points[start].x;
    const sy = points[start].y;
    const ex = points[end].x;
    const ey = points[end].y;

    for (let i = start + 1; i < end; i++) {
      const px = points[i].x;
      const py = points[i].y;

      const dx = ex - sx;
      const dy = ey - sy;
      const len = Math.sqrt(dx * dx + dy * dy);

      let dist;
      if (len === 0) {
        dist = Math.sqrt((px - sx) * (px - sx) + (py - sy) * (py - sy));
      } else {
        dist = Math.abs((py - sy) * dx - (px - sx) * dy) / len;
      }

      if (dist > maxDist) {
        maxDist = dist;
        index = i;
      }
    }

    if (maxDist > epsilon) {
      const left = rdp(points, epsilon, start, index);
      const right = rdp(points, epsilon, index, end);
      return [...left.slice(0, -1), ...right];
    } else {
      return [points[start], points[end]];
    }
  }

  let simplified = rdp(points, epsilon);
  if (simplified[0].x !== simplified[simplified.length - 1].x || simplified[0].y !== simplified[simplified.length - 1].y) {
    simplified.push(simplified[0]);
  }
  return simplified;
}

self.addEventListener('message', async (event) => {
  const { type, point, imageBuffer, width, height, imageId, setupType, selectedClass } = event.data;
  if (type === 'init') {
    await init();
  } else if (type === 'precompute' && model && processor) {
    await precomputeEmbeddings(imageBuffer, width, height, imageId);
  } else if (type === 'segment' && model && processor) {
    await segment(point, imageBuffer, width, height, imageId, setupType, selectedClass);
  } else {
    postMessage({ status: 'error', message: 'Worker not ready or invalid message' });
  }
});