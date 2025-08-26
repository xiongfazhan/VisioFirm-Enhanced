import { uploadFiles } from './chunkedUpload.js';

// Store upload state
let storedUploadId = null;
let storedFiles = [];

// Helper to read all directory entries, handling pagination
async function readAllDirectoryEntries(directoryReader) {
    const entries = [];
    try {
        while (true) {
            const batch = await new Promise((resolve, reject) => 
                directoryReader.readEntries(resolve, reject)
            );
            if (batch.length === 0) break;
            entries.push(...batch);
        }
    } catch (error) {
        console.error('Error reading directory entries:', error);
    }
    return entries;
}

// Process directory recursively, preserving full path
async function processDirectoryEntry(directoryEntry, basePath = '', fileList = []) {
    const currentPath = basePath ? `${basePath}/${directoryEntry.name}` : directoryEntry.name;
    try {
        if (directoryEntry.isFile) {
            const file = await new Promise((resolve, reject) => 
                directoryEntry.file(resolve, reject)
            );
            // Assign webkitRelativePath to preserve folder structure
            Object.defineProperty(file, 'webkitRelativePath', {
                value: currentPath,
                writable: false
            });
            fileList.push(file);
        } else if (directoryEntry.isDirectory) {
            const directoryReader = directoryEntry.createReader();
            const entries = await readAllDirectoryEntries(directoryReader);
            for (const entry of entries) {
                await processDirectoryEntry(entry, currentPath, fileList);
            }
        }
    } catch (error) {
        console.error(`Error processing entry at ${currentPath}:`, error);
    }
    return fileList;
}

// Collect all files from DataTransfer, handling files and directories
async function getAllFilesFromTransfer(dataTransfer) {
    const files = [];
    const items = Array.from(dataTransfer.items);

    await Promise.all(items.map(async (item) => {
        if (item.kind !== 'file') return;
        const entry = item.webkitGetAsEntry?.();
        try {
            if (entry?.isFile) {
                const file = await new Promise((resolve, reject) => 
                    entry.file(resolve, reject)
                );
                files.push(file);
            } else if (entry?.isDirectory) {
                const dirFiles = await processDirectoryEntry(entry);
                files.push(...dirFiles);
            } else {
                const file = item.getAsFile();
                if (file) files.push(file);
            }
        } catch (error) {
            console.warn('Error processing transfer item:', error);
        }
    }));

    // Fallback for browsers with limited API support
    if (files.length === 0 && dataTransfer.files.length > 0) {
        return Array.from(dataTransfer.files);
    }

    return files;
}

// Display file list, including images, archives, and annotations
export function showFileList(files, listElement, dropIcon, compressMsg) {
    const VALID_EXT = ['.webp', '.jpg', '.jpeg', '.png', '.avif'];
    const COMPRESSED_EXT = ['.zip', '.tar', '.rar'];
    const ANNOTATION_EXT = ['.txt', '.json', '.yaml'];

    listElement.innerHTML = '';
    const hasCompressed = files.some(file => 
        COMPRESSED_EXT.some(ext => file.name.toLowerCase().endsWith(ext))
    );

    const validFiles = files.filter(file => {
        const ext = file.name.toLowerCase().match(/\.[0-9a-z]+$/)?.[0] || '';
        return VALID_EXT.includes(ext) || COMPRESSED_EXT.includes(ext) || ANNOTATION_EXT.includes(ext);
    });

    if (validFiles.length > 0) {
        listElement.style.display = 'block';
        validFiles.forEach(file => {
            const div = document.createElement('div');
            div.textContent = file.webkitRelativePath || file.name;
            listElement.appendChild(div);
        });
        dropIcon?.classList.add('loaded');
        compressMsg.style.display = hasCompressed ? 'block' : 'none';
    } else {
        listElement.style.display = 'none';
        dropIcon?.classList.remove('loaded');
        compressMsg.style.display = 'none';
    }
}

// Initialize drop zone with comprehensive file handling
export function initDropZone(dropZone, fileInput, fileList, dropIcon, compressMsg, progressContainer, submitBtn, isImportModal = false) {
    const handleFiles = async (files) => {
        if (files.length === 0) {
            progressContainer.innerHTML = '<p class="error">No files selected</p>';
            return;
        }

        storedFiles = files;
        const dt = new DataTransfer();
        files.forEach(f => dt.items.add(f));
        fileInput.files = dt.files;

        await uploadFilesForProject(
            files,
            fileList,
            dropIcon,
            compressMsg,
            progressContainer,
            submitBtn,
            isImportModal
        );
        showFileList(files, fileList, dropIcon, compressMsg);
    };

    //dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');

        try {
            const files = await getAllFilesFromTransfer(e.dataTransfer);
            await handleFiles(files);
        } catch (error) {
            console.error('Drop processing error:', error);
            progressContainer.innerHTML = `<p class="error">Failed to process dropped files: ${error.message}</p>`;
        }
    });

    fileInput.addEventListener('change', async () => {
        if (fileInput.files.length > 0) {
            await handleFiles(Array.from(fileInput.files));
        }
    });
}

// Initialize import modal with consistent behavior
export function initImportModal(modal, form, dropZone, fileInput, fileList, closeBtn, compressMsg, progressContainer, submitBtn, enableDragDetection = false) {
    const modalState = {
        openedByDrag: false,
        hasDroppedFiles: false,
        dragTimer: null
    };

    initDropZone(
        dropZone,
        fileInput,
        fileList,
        dropZone.querySelector('.drop-icon'),
        compressMsg,
        progressContainer,
        submitBtn,
        true
    );

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        resetModalState();
        fetch('/cleanup_chunks', { method: 'POST' });
    });

    if (enableDragDetection) {
        document.addEventListener('dragover', (e) => {
            if (e.dataTransfer.types.includes('Files')) {
                clearTimeout(modalState.dragTimer);
                if (modal.style.display !== 'flex') {
                    modal.style.display = 'flex';
                    dropZone.classList.add('dragover');
                    modalState.openedByDrag = true;
                    modalState.hasDroppedFiles = false;
                    submitBtn.disabled = true;
                }
            }
        });

        document.addEventListener('dragleave', (e) => {
            if (e.relatedTarget === null && modalState.openedByDrag && !modalState.hasDroppedFiles) {
                modalState.dragTimer = setTimeout(() => {
                    modal.style.display = 'none';
                    resetModalState();
                }, 100);
            }
        });

        document.addEventListener('drop', () => {
            modalState.hasDroppedFiles = true;
        });
    }

    function resetModalState() {
        fileInput.files = new DataTransfer().files;
        storedFiles = [];
        storedUploadId = null;
        fileList.innerHTML = '';
        fileList.style.display = 'none';
        dropZone.querySelector('.drop-icon').classList.remove('loaded');
        compressMsg.style.display = 'none';
        progressContainer.innerHTML = '';
        submitBtn.disabled = true;
        modalState.openedByDrag = false;
        modalState.hasDroppedFiles = false;
        dropZone.classList.remove('dragover');
    }

    return {
        reset: resetModalState,
        getStoredUploadId: () => storedUploadId
    };
}

// Handle file uploads with progress tracking
async function uploadFilesForProject(files, fileList, dropIcon, compressMsg, progressContainer, submitBtn, isImportModal) {
    if (files.length === 0) return;

    submitBtn?.setAttribute('disabled', 'true');
    createProgressBars(files, progressContainer);

    try {
        const endpoint = isImportModal ? '/import_images' : '/create_project';
        storedUploadId = await uploadFiles(files, endpoint, {}, updateProgress);

        fileList.innerHTML = '';
        fileList.style.display = 'none';
        dropIcon?.classList.remove('loaded');
        compressMsg.style.display = 'none';
        progressContainer.innerHTML = '<p class="upload-success">Upload complete!</p>';
        submitBtn?.removeAttribute('disabled');
    } catch (error) {
        console.error('Upload failed:', error);
        progressContainer.innerHTML = '<p class="error">Upload failed. Please try again.</p>';
        resetUploadState();
    }

    function updateProgress(fileProgress) {
        fileProgress.forEach(({ uploaded, total }, fileName) => {
            const progressElement = document.getElementById(`progress-${fileName.replace(/\W/g, '_')}`);
            if (progressElement) {
                progressElement.style.width = `${(uploaded / total) * 100}%`;
            }
        });
    }

    function resetUploadState() {
        fileList.innerHTML = '';
        fileList.style.display = 'none';
        dropIcon?.classList.remove('loaded');
        compressMsg.style.display = 'none';
        storedFiles = [];
        storedUploadId = null;
        submitBtn?.setAttribute('disabled', 'true');
    }
}

// Create progress bars for uploaded files
function createProgressBars(files, container) {
    container.innerHTML = files.map(file => `
        <div class="progress-container">
            <div class="file-progress">${file.webkitRelativePath || file.name}</div>
            <div class="progress-bar">
                <div class="progress" id="progress-${file.name.replace(/\W/g, '_')}"></div>
            </div>
        </div>
    `).join('');
}

export function getStoredUploadId() {
    return storedUploadId;
}

export function clearStoredData() {
    storedFiles = [];
    storedUploadId = null;
}