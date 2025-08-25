import { viewport, currentImage, currentImageKey, undoStack, annotations, gridEnabled, gridSize } from './globals.js';

export function toImageCoords(x, y) {
    return { x: (x - viewport.x) / viewport.zoom, y: (y - viewport.y) / viewport.zoom };
}

export function toCanvasCoords(x, y) {
    return { x: viewport.x + x * viewport.zoom, y: viewport.y + y * viewport.zoom };
}

export function clampToImageBounds(point) {
    if (!currentImage) return point;
    let snappedPoint = {
        x: Math.max(0, Math.min(point.x, currentImage.width)),
        y: Math.max(0, Math.min(point.y, currentImage.height))
    };
    if (gridEnabled) {
        snappedPoint.x = Math.round(snappedPoint.x / gridSize) * gridSize;
        snappedPoint.y = Math.round(snappedPoint.y / gridSize) * gridSize;
    }
    return snappedPoint;
}

// Calculate the rotated corners of a rectangle
export function getRotatedCorners(annotation) {
    const centerX = annotation.x + annotation.width / 2;
    const centerY = annotation.y + annotation.height / 2;
    const rad = (annotation.rotation || 0) * Math.PI / 180;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    
    const corners = [
        { x: annotation.x, y: annotation.y },
        { x: annotation.x + annotation.width, y: annotation.y },
        { x: annotation.x + annotation.width, y: annotation.y + annotation.height },
        { x: annotation.x, y: annotation.y + annotation.height }
    ];
    
    return corners.map(corner => {
        const dx = corner.x - centerX;
        const dy = corner.y - centerY;
        return {
            x: centerX + (dx * cos - dy * sin),
            y: centerY + (dx * sin + dy * cos)
        };
    });
}

// Clamp annotation to image bounds considering rotation
// In annotationCore.js
export function clampAnnotationToBounds(annotation) {
    if (!currentImage) return;

    if (annotation.type === 'polygon') {
        // For polygons, clamp each point individually
        annotation.points = annotation.points.map(p => clampToImageBounds(p));
        return;
    }

    if (annotation.type !== 'rect' || !annotation.rotation) {
        // For non-rotated rectangles, use simple clamping
        annotation.x = Math.max(0, Math.min(annotation.x, currentImage.width - annotation.width));
        annotation.y = Math.max(0, Math.min(annotation.y, currentImage.height - annotation.height));
        return;
    }

    // For rotated rectangles, we need more sophisticated clamping
    const centerX = annotation.x + annotation.width / 2;
    const centerY = annotation.y + annotation.height / 2;
    const rad = (annotation.rotation || 0) * Math.PI / 180;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);

    // Get current corners
    const corners = getRotatedCorners(annotation);
    
    // Calculate how much we're out of bounds
    let minX = Math.min(...corners.map(c => c.x));
    let maxX = Math.max(...corners.map(c => c.x));
    let minY = Math.min(...corners.map(c => c.y));
    let maxY = Math.max(...corners.map(c => c.y));

    // Calculate needed translation (without resizing)
    let tx = 0, ty = 0;
    if (minX < 0) tx = -minX;
    if (maxX > currentImage.width) tx = currentImage.width - maxX;
    if (minY < 0) ty = -minY;
    if (maxY > currentImage.height) ty = currentImage.height - maxY;

    // First try just translating
    annotation.x += tx;
    annotation.y += ty;

    // Check if we're still out of bounds after translation
    const newCorners = getRotatedCorners(annotation);
    minX = Math.min(...newCorners.map(c => c.x));
    maxX = Math.max(...newCorners.map(c => c.x));
    minY = Math.min(...newCorners.map(c => c.y));
    maxY = Math.max(...newCorners.map(c => c.y));

    const outOfBounds = minX < 0 || maxX > currentImage.width || 
                       minY < 0 || maxY > currentImage.height;

    if (outOfBounds) {
        // If still out of bounds, calculate maximum allowed size
        const currentDiag = Math.sqrt(annotation.width * annotation.width + annotation.height * annotation.height);
        
        // Calculate maximum possible diagonal that fits within image
        const maxDiag = Math.min(
            Math.min(currentImage.width, currentImage.height),
            currentDiag * 0.95 // Slightly smaller to ensure it fits
        );

        // Only scale down if necessary (don't scale up)
        if (maxDiag < currentDiag) {
            const scale = maxDiag / currentDiag;
            
            // Scale while maintaining aspect ratio
            const newWidth = annotation.width * scale;
            const newHeight = annotation.height * scale;
            
            // Update dimensions while keeping center fixed
            annotation.x = centerX - newWidth / 2;
            annotation.y = centerY - newHeight / 2;
            annotation.width = newWidth;
            annotation.height = newHeight;
        }

        // Final adjustment to ensure we're within bounds
        const finalCorners = getRotatedCorners(annotation);
        minX = Math.min(...finalCorners.map(c => c.x));
        maxX = Math.max(...finalCorners.map(c => c.x));
        minY = Math.min(...finalCorners.map(c => c.y));
        maxY = Math.max(...finalCorners.map(c => c.y));

        tx = 0, ty = 0;
        if (minX < 0) tx = -minX;
        if (maxX > currentImage.width) tx = currentImage.width - maxX;
        if (minY < 0) ty = -minY;
        if (maxY > currentImage.height) ty = currentImage.height - maxY;

        annotation.x += tx;
        annotation.y += ty;
    }
}

export function pushToUndoStack() {
    if (!currentImageKey) return;
    if (!undoStack[currentImageKey]) undoStack[currentImageKey] = [];
    const stack = undoStack[currentImageKey];
    if (stack.length >= 50) stack.shift();
    stack.push(JSON.parse(JSON.stringify(annotations)));
}