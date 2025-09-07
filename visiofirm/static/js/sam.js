import { currentImage, annotations, selectedClass, setupType, updateTagHighlights, setSelectedAnnotation, setWorker, worker } from './globals.js';
import { drawImage } from './annotationDrawing.js';
import { pushToUndoStack } from './annotationCore.js';

export async function initializeSegmentor() {
  console.log('Main: Setting up SAM worker...');
  setWorker(new Worker(new URL('./samWorker.js', import.meta.url), { type: 'module' }));

  return new Promise((resolve, reject) => {
    worker.onmessage = (event) => {
      const { status, message } = event.data;
      if (status === 'ready') {
        console.log('Main: Worker ready');
        resolve();
      } else if (status === 'error') {
        console.error('Main: Worker initialization failed:', message);
        reject(new Error(message));
      }
    };
    worker.postMessage({ type: 'init' });
  });
}

export async function segmentArea(point) {
  if (!worker) {
    console.error('Worker not ready');
    return null;
  }

  const tempCanvas = document.createElement('canvas');
  tempCanvas.width = currentImage.width;
  tempCanvas.height = currentImage.height;
  const tempCtx = tempCanvas.getContext('2d');
  tempCtx.drawImage(currentImage, 0, 0);

  const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
  const imageId = currentImage.src || Date.now().toString(); 

  const buffer = imageData.data.buffer;
  worker.postMessage({
    type: 'segment',
    point,
    imageBuffer: buffer,
    width: tempCanvas.width,
    height: tempCanvas.height,
    imageId,
    setupType: setupType, 
    selectedClass: selectedClass 
  }, [buffer]);

  return new Promise((resolve) => {
    const handler = (event) => {
      const { status, result, duration, score, message } = event.data;
      worker.removeEventListener('message', handler); // Cleanup
      if (status === 'complete' && result) {
        console.log(`Main: Segmentation done in ${duration}s, score: ${score}`);
        pushToUndoStack();
        annotations.push(result);
        setSelectedAnnotation(null);
        updateTagHighlights();
        drawImage();
        resolve(result);
      } else if (status === 'no-mask') {
        console.log('No mask generated');
        resolve(null);
      } else if (status === 'error') {
        console.error('Worker error:', message);
        resolve(null);
      }
    };
    worker.addEventListener('message', handler);
  });
}