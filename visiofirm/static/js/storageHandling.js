import { annotationCache } from './globals.js';
import { setAnnotationCache } from './globals.js';

export function saveCacheToStorage() {
    localStorage.setItem('annotationCache', JSON.stringify(annotationCache));
}

export function loadCacheFromStorage() {
    const cached = localStorage.getItem('annotationCache');
    if (cached) {
        const newCache = JSON.parse(cached);
        Object.keys(newCache).forEach(key => {
            newCache[key] = newCache[key].map(anno => {
                if (anno.type === 'polygon') {
                    return { ...anno, points: anno.points.map(p => ({ x: p.x, y: p.y })) };
                }
                return anno;
            });
        });
        setAnnotationCache(newCache); 
    }
}