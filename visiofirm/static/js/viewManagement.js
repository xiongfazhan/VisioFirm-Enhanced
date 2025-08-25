import { state } from './sharedState.js';
import { selectImage } from './imageHandling.js';

export function switchToAnnotationView(imgElement = null) {
    console.log('Switching to annotation view');
    const gridView = document.getElementById('grid-view');
    const annotationView = document.getElementById('annotation-view');

    gridView.classList.remove('show');
    gridView.classList.add('hide');
    gridView.addEventListener('transitionend', function handler() {
        gridView.style.display = 'none';
        gridView.removeEventListener('transitionend', handler);
    }, { once: true });

    annotationView.style.display = 'flex';
    annotationView.classList.remove('hide');
    setTimeout(() => {
        annotationView.classList.add('show');
    }, 10);

    if (imgElement) {
        const gridCard = imgElement.closest('.grid-card');
        const listRow = imgElement.closest('#list-table tbody tr');
        let index;

        if (gridCard) {
            // Grid view index calculation
            index = Array.from(document.querySelectorAll('.grid-card')).indexOf(gridCard);
        } else if (listRow) {
            // List view index calculation
            index = Array.from(document.querySelectorAll('#list-table tbody tr')).indexOf(listRow);
        } else {
            console.error('Could not determine parent element for image:', imgElement);
            return;
        }

        if (index === -1) {
            console.error('Image element not found in current view:', imgElement);
            return;
        }

        selectImage(imgElement, index);
    } else if (!state.currentImage && state.thumbnailImages.length > 0) {
        selectImage(state.thumbnailImages[0], 0); // Fallback to first image
    }
}

export function switchToGridView() {
    console.log('Switching to grid view');
    const gridView = document.getElementById('grid-view');
    const annotationView = document.getElementById('annotation-view');

    annotationView.classList.remove('show');
    annotationView.classList.add('hide');
    annotationView.addEventListener('transitionend', function handler() {
        annotationView.style.display = 'none';
        annotationView.removeEventListener('transitionend', handler);
    }, { once: true });

    gridView.style.display = 'block';
    gridView.classList.remove('hide');
    setTimeout(() => {
        gridView.classList.add('show');
    }, 10);
}

export function initializeGridView() {
    const gridView = document.getElementById('grid-view');
    const annotationView = document.getElementById('annotation-view');
    gridView.style.display = 'block';
    annotationView.style.display = 'none';
    gridView.classList.add('show');
    gridView.classList.remove('hide');
    annotationView.classList.add('hide');
    annotationView.classList.remove('show');
}

export function sortImages(sortType) {
    const gridCards = Array.from(document.querySelectorAll('.grid-card'));
    const listRows = Array.from(document.querySelectorAll('#list-table tbody tr'));

    let sortedGrid, sortedList;

    switch(sortType) {
        case 'name-asc':
            sortedGrid = gridCards.sort((a, b) => a.dataset.id.localeCompare(b.dataset.id));
            sortedList = listRows.sort((a, b) => a.dataset.id.localeCompare(b.dataset.id));
            break;
        case 'name-desc':
            sortedGrid = gridCards.sort((a, b) => b.dataset.id.localeCompare(a.dataset.id));
            sortedList = listRows.sort((a, b) => b.dataset.id.localeCompare(a.dataset.id));
            break;
        case 'date-asc':
            sortedGrid = gridCards.sort((a, b) => new Date(a.dataset.date) - new Date(b.dataset.date));
            sortedList = listRows.sort((a, b) => new Date(a.dataset.date) - new Date(b.dataset.date));
            break;
        case 'date-desc':
            sortedGrid = gridCards.sort((a, b) => new Date(b.dataset.date) - new Date(a.dataset.date));
            sortedList = listRows.sort((a, b) => new Date(b.dataset.date) - new Date(a.dataset.date));
            break;
        case 'status-asc':
            sortedGrid = gridCards.sort((a, b) => {
                const aStatus = a.dataset.annotated === 'true' ? 0 : (a.dataset.preannotated === 'true' ? 1 : 2);
                const bStatus = b.dataset.annotated === 'true' ? 0 : (b.dataset.preannotated === 'true' ? 1 : 2);
                return aStatus - bStatus;
            });
            sortedList = listRows.sort((a, b) => {
                const aStatus = a.dataset.annotated === 'true' ? 0 : (a.dataset.preannotated === 'true' ? 1 : 2);
                const bStatus = b.dataset.annotated === 'true' ? 0 : (b.dataset.preannotated === 'true' ? 1 : 2);
                return aStatus - bStatus;
            });
            break;
        case 'status-desc':
            sortedGrid = gridCards.sort((a, b) => {
                const aStatus = a.dataset.annotated === 'true' ? 0 : (a.dataset.preannotated === 'true' ? 1 : 2);
                const bStatus = b.dataset.annotated === 'true' ? 0 : (b.dataset.preannotated === 'true' ? 1 : 2);
                return bStatus - aStatus;
            });
            sortedList = listRows.sort((a, b) => {
                const aStatus = a.dataset.annotated === 'true' ? 0 : (a.dataset.preannotated === 'true' ? 1 : 2);
                const bStatus = b.dataset.annotated === 'true' ? 0 : (b.dataset.preannotated === 'true' ? 1 : 2);
                return bStatus - aStatus;
            });
            break;
        default:
            return;
    }

    const gridContainer = document.getElementById('grid-thumbnails');
    gridContainer.innerHTML = '';
    sortedGrid.forEach(card => gridContainer.appendChild(card));

    const listBody = document.querySelector('#list-table tbody');
    listBody.innerHTML = '';
    sortedList.forEach(row => listBody.appendChild(row));
}

export function toggleView(viewType) {
    if (viewType === 'grid') {
        document.getElementById('grid-thumbnails').style.display = 'grid';
        document.getElementById('list-table').style.display = 'none';
        document.getElementById('grid-toggle-btn').classList.add('active');
        document.getElementById('list-toggle-btn').classList.remove('active');
    } else {
        document.getElementById('grid-thumbnails').style.display = 'none';
        document.getElementById('list-table').style.display = 'table';
        document.getElementById('grid-toggle-btn').classList.remove('active');
        document.getElementById('list-toggle-btn').classList.add('active');
    }

    document.querySelectorAll('.image-checkbox').forEach(checkbox => {
        const path = checkbox.dataset.path;
        const otherViewCheckbox = document.querySelector(
            `.image-checkbox[data-path="${path}"]:not([checked="${checkbox.checked}"])`
        );
        if (otherViewCheckbox) {
            otherViewCheckbox.checked = checkbox.checked;
        }
    });
}