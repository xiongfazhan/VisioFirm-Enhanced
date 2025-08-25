const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB
const UPLOAD_TIMEOUT = 5000; // 60 seconds
const MAX_CONCURRENT_UPLOADS = 6; // Max 3 concurrent chunk uploads

// Helper function to upload a chunk with retries and timeout
async function uploadChunkWithRetry(formData, maxRetries = 5) {
    let timeoutCount = 0;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT);
            
            const response = await fetch('/upload_chunk', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            
            const result = await response.json();
            if (result.success) {
                return result;
            }
            throw new Error(`Chunk upload failed: ${result.error || 'Unknown error'}`);
        } catch (error) {
            if (error.name === 'AbortError') {
                timeoutCount++;
                console.warn(`Chunk upload timed out on attempt ${attempt + 1} after ${UPLOAD_TIMEOUT/1000} seconds`);
                if (timeoutCount >= maxRetries) {
                    throw new Error('Upload failed after multiple timeouts. Server may be slow or unreachable.');
                }
            } else {
                console.warn(`Chunk upload error on attempt ${attempt + 1}: ${error.message}`);
            }
            if (attempt === maxRetries - 1) {
                throw error;
            }
            // Exponential backoff: 500ms, 1s, 2s
            await new Promise(resolve => setTimeout(resolve, 500 * Math.pow(2, attempt)));
            console.warn(`Retrying chunk upload, attempt ${attempt + 2}`);
        }
    }
}

export async function uploadFiles(files, endpoint, formDataExtras = {}, onProgress = () => {}) {
    const uploadId = generateUUID();
    const fileProgress = new Map();

    // Initialize progress tracking
    for (const file of files) {
        fileProgress.set(file.name, { uploaded: 0, total: file.size });
    }

    // Process files sequentially
    for (const file of files) {
        const fileId = generateUUID();
        const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
        let startChunk = 0;

        // Check upload status to resume if possible
        try {
            const statusResponse = await fetch('/check_upload_status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ upload_id: uploadId, file_id: fileId })
            });
            const status = await statusResponse.json();
            startChunk = status.uploaded_chunks;
            console.log(`Resuming upload for ${file.name} at chunk ${startChunk}`);
        } catch (error) {
            console.error(`Error checking upload status for ${file.name}:`, error);
            throw error;
        }

        // Upload chunks with limited concurrency
        const chunkPromises = [];
        for (let i = startChunk; i < totalChunks; i++) {
            const start = i * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, file.size);
            const chunk = file.slice(start, end);
            const formData = new FormData();
            formData.append('chunk', chunk, file.name);
            formData.append('upload_id', uploadId);
            formData.append('file_id', fileId);
            formData.append('chunk_index', i);
            formData.append('filename', file.name);

            chunkPromises.push(async () => {
                try {
                    await uploadChunkWithRetry(formData);
                    fileProgress.get(file.name).uploaded += chunk.size;
                    onProgress(fileProgress);
                    console.log(`Uploaded chunk ${i}/${totalChunks} for ${file.name}`);
                } catch (error) {
                    console.error(`Failed to upload chunk ${i} for ${file.name}:`, error);
                    throw new Error(`Chunk ${i} upload failed for ${file.name}: ${error.message}`);
                }
            });
        }

        // Execute chunk uploads with limited concurrency
        for (let i = 0; i < chunkPromises.length; i += MAX_CONCURRENT_UPLOADS) {
            const batch = chunkPromises.slice(i, i + MAX_CONCURRENT_UPLOADS);
            await Promise.all(batch.map(task => task()));
        }

        // Assemble file after all chunks are uploaded
        try {
            const formData = new FormData();
            formData.append('upload_id', uploadId);
            formData.append('file_id', fileId);
            formData.append('total_chunks', totalChunks);
            formData.append('filename', file.name);

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), UPLOAD_TIMEOUT);
            const response = await fetch('/assemble_file', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            const result = await response.json();
            if (!result.success) {
                throw new Error(`File assembly failed for ${file.name}: ${result.error}`);
            }
            console.log(`Assembled file ${file.name}`);
        } catch (error) {
            if (error.name === 'AbortError') {
                error = new Error('File assembly timed out');
            }
            console.error(`Assembly failed for ${file.name}:`, error);
            throw error;
        }
    }

    return uploadId;
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

export function updateProgressBar(fileProgress, progressBar, progressElement) {
    let totalUploaded = 0;
    let totalSize = 0;

    for (const { uploaded, total } of fileProgress.values()) {
        totalUploaded += uploaded;
        totalSize += total;
    }

    const percentage = totalSize > 0 ? (totalUploaded / totalSize) * 100 : 0;
    progressElement.style.width = `${percentage}%`;
}