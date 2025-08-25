import { mode, gridEnabled, selectedAnnotation, annotations, undoStack, viewport, currentImageIndex, thumbnailImages, currentImage, setupType, currentAnnotation, currentImageKey, setMode, setGridEnabled, setSelectedAnnotation, setCurrentAnnotation, setAnnotations } from './globals.js';
import { drawImage, resetView } from './annotationDrawing.js';
import { selectImage } from './imageHandling.js';
import { pushToUndoStack } from './annotationCore.js';

export function initToolControls() {
    document.getElementById('rect-mode').addEventListener('click', () => {
        if (setupType === "Segmentation") return;
        setMode('rect'); // Use setter
        updateButtonStates();
    });

    document.getElementById('polygon-mode').addEventListener('click', () => {
        if (setupType !== "Segmentation") return;
        setMode('polygon'); // Use setter
        setSelectedAnnotation(null); // Use setter
        setCurrentAnnotation(null); // Use setter
        updateButtonStates();
    });

    document.getElementById('select-mode').addEventListener('click', () => {
        setMode('select'); // Use setter
        updateButtonStates();
    });

    document.getElementById('reset-view').addEventListener('click', resetView);

    document.getElementById('undo-btn').addEventListener('click', () => {
        if (undoStack[currentImageKey] && undoStack[currentImageKey].length > 0) { // Now defined
            setAnnotations(undoStack[currentImageKey].pop()); // Use setter
            setSelectedAnnotation(annotations.length > 0 ? annotations[annotations.length - 1] : null); // Use setter
            drawImage();
        }
    });

    document.getElementById('delete-btn').addEventListener('click', () => {
        if (selectedAnnotation) {
            pushToUndoStack();
            setAnnotations(annotations.filter(a => a !== selectedAnnotation)); // Use setter
            setSelectedAnnotation(null); // Use setter
            drawImage();
        }
    });

    document.getElementById('zoom-in-btn').addEventListener('click', () => {
        viewport.zoom = Math.min(viewport.maxZoom, viewport.zoom * 1.1);
        drawImage();
    });

    document.getElementById('zoom-out-btn').addEventListener('click', () => {
        viewport.zoom = Math.max(viewport.minZoom, viewport.zoom * 0.9);
        drawImage();
    });

    document.getElementById('duplicate-btn').addEventListener('click', () => {
        if (selectedAnnotation) {
            pushToUndoStack();
            const duplicate = scaleAnnotation(selectedAnnotation, currentImage.width, currentImage.height, currentImage.width, currentImage.height);
            duplicate.x += 0.3 * duplicate.x;
            duplicate.y += 0.3 * duplicate.y;
            annotations.push(duplicate); // Note: Direct push is okay since we're modifying the array, not reassigning it
            setSelectedAnnotation(duplicate); // Use setter
            drawImage();
        }
    });

    document.getElementById('save-btn').addEventListener('click', () => {
        document.getElementById('approve-btn').click();
    });

    document.getElementById('grid-btn').addEventListener('click', () => {
        setGridEnabled(!gridEnabled); // Use setter
        document.getElementById('grid-btn').classList.toggle('active', gridEnabled);
        drawImage();
    });

    document.getElementById('prev-image-btn').addEventListener('click', () => {
        if (currentImageIndex > 0) {
            selectImage(thumbnailImages[currentImageIndex - 1], currentImageIndex - 1);
        }
    });

    document.getElementById('next-image-btn').addEventListener('click', () => {
        if (currentImageIndex < thumbnailImages.length - 1) {
            selectImage(thumbnailImages[currentImageIndex + 1], currentImageIndex + 1);
        }
    });

    // Hide buttons based on setupType
    const polygonModeBtn = document.getElementById('polygon-mode');
    const rectModeBtn = document.getElementById('rect-mode');
    if (setupType === "Bounding Box" || setupType === "Oriented Bounding Box") {
        if (polygonModeBtn) polygonModeBtn.style.display = 'none';
    } else if (setupType === "Segmentation") {
        if (rectModeBtn) rectModeBtn.style.display = 'none';
    }

    updateButtonStates();
}

function updateButtonStates() {
    document.querySelectorAll('.control-btn').forEach(btn => {
        if (btn.id === `${mode}-mode`) {
            btn.classList.add('active');
        } else if (btn.id !== 'grid-btn') {
            btn.classList.remove('active');
        }
    });
}

function scaleAnnotation(annotation, sourceWidth, sourceHeight, targetWidth, targetHeight) {
    const scaleX = targetWidth / sourceWidth;
    const scaleY = targetHeight / sourceHeight;
    const scaled = JSON.parse(JSON.stringify(annotation));
    if (scaled.type === 'rect') {
        scaled.x *= scaleX;
        scaled.y *= scaleY;
        scaled.width *= scaleX;
        scaled.height *= scaleY;
    } else if (scaled.type === 'polygon') {
        scaled.points = scaled.points.map(p => ({
            x: p.x * scaleX,
            y: p.y * scaleY
        }));
    }
    return scaled;
}