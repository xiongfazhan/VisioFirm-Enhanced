import {
  env,  // Add env to the import
  SamModel,
  AutoProcessor,
  RawImage,
  Tensor
} from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.3.3/dist/transformers.min.js";

import { currentImage, annotations, selectedClass, setupType, updateTagHighlights, setSelectedAnnotation } from './globals.js';
import { drawImage } from './annotationDrawing.js';
import { pushToUndoStack } from './annotationCore.js';

let model = null;
let processor = null;

export async function initializeSegmentor() {
  console.log('Initializing SAM model...');
  const model_id = "Xenova/slimsam-77-uniform";

  env.backends.onnx.wasm.numThreads = 1; 
  env.backends.onnx.wasm.simd = true; 
  env.backends.onnx.wasm.proxy = true; 

  async function isWebGPUSupported() {
    if (!navigator.gpu) return false;
    try {
      const adapter = await navigator.gpu.requestAdapter();
      return !!adapter;  
    } catch (e) {
      console.warn('WebGPU adapter request failed:', e);
      return false;
    }
  }

  const useWebGPU = await isWebGPUSupported();
  const device = useWebGPU ? "webgpu" : "wasm";

  try {
    model = await SamModel.from_pretrained(model_id, {
      dtype: "fp32",
      device: device,
    });
    processor = await AutoProcessor.from_pretrained(model_id);
    console.log(`SAM model and processor loaded using ${device} backend`);
  } catch (e) {
    console.error('Failed to load SAM model:', e);
  }
}

export async function segmentArea(point) {
  if (!model || !processor) {
    console.error('SAM not ready');
    return;
  }

  const startTime = performance.now();

  try {
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = currentImage.width;
    tempCanvas.height = currentImage.height;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(currentImage, 0, 0);

    console.log('Capturing image');
    const imageInput = await RawImage.fromCanvas(tempCanvas);
    console.log('Processing image');
    const imageProcessed = await processor(imageInput);
    console.log('Generating image embeddings');
    const imageEmbeddings = await model.get_image_embeddings(imageProcessed);

    const reshaped = imageProcessed.reshaped_input_sizes[0];
    const pointsArray = [
      point.x * reshaped[1] / currentImage.width,
      point.y * reshaped[0] / currentImage.height
    ];
    const labelsArray = [1n];
    const input_points = new Tensor("float32", pointsArray, [1, 1, 1, 2]);
    const input_labels = new Tensor("int64", labelsArray, [1, 1, 1]);

    console.log('Running model inference');
    const { pred_masks, iou_scores } = await model({
      ...imageEmbeddings,
      input_points,
      input_labels
    });

    console.log('Post-processing masks');
    const masks = await processor.post_process_masks(
      pred_masks,
      imageProcessed.original_sizes,
      imageProcessed.reshaped_input_sizes
    );

    const maskTensor = masks[0][0]; // [num_masks, h, w]
    const maskData = maskTensor.data;
    const numMasks = iou_scores.dims[1];
    const scores = iou_scores.data;
    let bestIndex = 0;
    for (let i = 1; i < scores.length; i++) {
      if (scores[i] > scores[bestIndex]) bestIndex = i;
    }

    const width = maskTensor.dims[2];
    const height = maskTensor.dims[1];
    const maskStride = height * width;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const pixelIndex = y * width + x;
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
      console.log('No mask generated');
      return;
    }

    if (setupType === 'Segmentation') {
      // Extract contour for polygon
      const contour = extractContour(maskData, width, height, numMasks, bestIndex);
      if (contour.length > 2) {
        const simplifiedContour = simplifyPolygon(contour, 2); // Increased epsilon for more simplification while keeping shape
        const newAnno = {
          type: 'polygon',
          points: simplifiedContour,
          closed: true,
          label: selectedClass
        };
        pushToUndoStack();
        annotations.push(newAnno);
        setSelectedAnnotation(null);
        updateTagHighlights();
        drawImage();
      }
    } else {
      // Create axis-aligned bbox for Bounding Box or Oriented Bounding Box
      const newAnno = {
        type: setupType === "Oriented Bounding Box" ? 'obbox' : 'rect',
        x: minX,
        y: minY,
        width: maxX - minX + 1,
        height: maxY - minY + 1,
        rotation: 0,
        label: selectedClass
      };
      pushToUndoStack();
      annotations.push(newAnno);
      setSelectedAnnotation(null);
      updateTagHighlights();
      drawImage();
    }

    const endTime = performance.now();
    const duration = (endTime - startTime) / 1000;
    console.log(`Segmentation completed in ${duration.toFixed(2)} seconds, score: ${scores[bestIndex].toFixed(2)}`);
  } catch (e) {
    console.error('Segmentation failed:', e);
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
  let dir = 6; // Start searching downwards
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
  // Ramer-Douglas-Peucker algorithm
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
  // Ensure closed
  if (simplified[0].x !== simplified[simplified.length - 1].x || simplified[0].y !== simplified[simplified.length - 1].y) {
    simplified.push(simplified[0]);
  }
  return simplified;
}