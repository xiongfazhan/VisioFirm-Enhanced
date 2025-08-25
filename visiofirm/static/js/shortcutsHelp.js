import { setupType } from './globals.js';

export function updateShortcutsNotice() {
    const shortcutsList = document.querySelector('.shortcuts-list');
    const shortcutsLegend = document.querySelector('.shortcuts-legend');
    shortcutsList.innerHTML = '';
    shortcutsLegend.innerHTML = '';

    const legendItems = [
        { key: 'ctrl', icon: 'fas fa-cogs', desc: 'Ctrl' },
        { key: 'shift', icon: 'fas fa-arrow-up', desc: 'Shift' },
        { key: 'alt', icon: 'fas fa-exchange-alt', desc: 'Alt' },
        { key: 'mouse-left', icon: 'fas fa-mouse-pointer', desc: 'Left Click' },
        { key: 'mouse-right', icon: 'fas fa-hand-pointer', desc: 'Right Click' },
        { key: 'wheel', icon: 'fas fa-scroll', desc: 'Mouse Wheel' }
    ];

    const legendHeader = document.createElement('h4');
    legendHeader.textContent = 'Key Icons';
    shortcutsLegend.appendChild(legendHeader);

    legendItems.forEach(item => {
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';

        const keySpan = document.createElement('span');
        keySpan.className = `legend-key ${item.key}`;
        keySpan.innerHTML = `<i class="${item.icon}"></i>`;

        const descSpan = document.createElement('span');
        descSpan.className = 'legend-desc';
        descSpan.textContent = item.desc;

        legendItem.appendChild(keySpan);
        legendItem.appendChild(descSpan);
        shortcutsLegend.appendChild(legendItem);
    });

    const shortcuts = [
        { keys: ['shift', 'mouse-left'], desc: 'Pan', icon: 'fas fa-arrows-alt' },
        { keys: ['wheel'], desc: 'Zoom', icon: 'fas fa-search-plus' },
        { keys: ['alt', 'wheel'], desc: 'Fine Zoom', icon: 'fas fa-search-plus' },
        { keys: ['ctrl', 'z'], desc: 'Undo', icon: 'fas fa-undo' },
        { keys: ['delete'], desc: 'Remove Selected', icon: 'fas fa-trash' },
        { keys: ['alt', 'd'], desc: 'Duplicate', icon: 'fas fa-copy' },
        { keys: ['ctrl', 's'], desc: 'Save', icon: 'fas fa-save' },
        { keys: ['arrow-left'], desc: 'Previous Image', icon: 'fas fa-arrow-left' },
        { keys: ['arrow-right'], desc: 'Next Image', icon: 'fas fa-arrow-right' },
        { keys: ['ctrl', 'arrow-up'], desc: 'Nudge Up', icon: 'fas fa-arrow-up' },
        { keys: ['ctrl', 'arrow-down'], desc: 'Nudge Down', icon: 'fas fa-arrow-down' },
        { keys: ['ctrl', 'arrow-left'], desc: 'Nudge Left', icon: 'fas fa-arrow-left' },
        { keys: ['ctrl', 'arrow-right'], desc: 'Nudge Right', icon: 'fas fa-arrow-right' },
        { keys: ['mouse-right', 'mouse-left'], desc: 'Edit', icon: 'fas fa-edit' },
        { keys: ['ctrl', 'a'], desc: 'Deselect', icon: 'fas fa-times' },
        { keys: ['ctrl', 'c'], desc: 'Copy Annotations', icon: 'fas fa-copy' },
        { keys: ['ctrl', 'v'], desc: 'Paste Annotations', icon: 'fas fa-paste' },
        { keys: ['hold "R"', 'mouse-left'], desc: 'Rotate bounding box', icon: 'fa-solid fa-rotate-right' }
    ];

    if (setupType === "Bounding Box" || setupType === "Oriented Bounding Box") {
        shortcuts.push({ keys: ['ctrl', 'shift', 'mouse-left'], desc: 'Center Rect', icon: 'far fa-square' });
        if (setupType === "Oriented Bounding Box") {
            shortcuts.push({ keys: ['alt', 'mouse-left'], desc: 'Orient Bounding Box', icon: 'fas fa-sync' });
        }
    } else if (setupType === "Segmentation") {
        shortcuts.push({ keys: ['ctrl', 'mouse-left'], desc: 'Add Point (Select)', icon: 'fas fa-plus' });
        shortcuts.push({ keys: ['escape'], desc: 'Close Polygon', icon: 'fas fa-check' });
    }

    shortcuts.forEach(shortcut => {
        const item = document.createElement('div');
        item.className = 'shortcut-item';

        const keysSpan = document.createElement('span');
        shortcut.keys.forEach((key, index) => {
            const keySpan = document.createElement('span');
            keySpan.className = `shortcut-key ${key.toLowerCase().replace(' ', '-')}`;
            if (key === 'ctrl') keySpan.innerHTML = '<i class="fas fa-cogs"></i>';
            else if (key === 'shift') keySpan.innerHTML = '<i class="fas fa-arrow-up"></i>';
            else if (key === 'alt') keySpan.innerHTML = '<i class="fas fa-exchange-alt"></i>';
            else if (key === 'mouse-left') keySpan.innerHTML = '<i class="fas fa-mouse-pointer"></i>';
            else if (key === 'mouse-right') keySpan.innerHTML = '<i class="fas fa-hand-pointer"></i>';
            else if (key === 'wheel') keySpan.innerHTML = '<i class="fas fa-scroll"></i>';
            else if (key.startsWith('arrow-')) keySpan.innerHTML = `<i class="fas fa-arrow-${key.split('-')[1]}"></i>`;
            else keySpan.textContent = key.toUpperCase();
            keysSpan.appendChild(keySpan);
            if (index < shortcut.keys.length - 1) keysSpan.appendChild(document.createTextNode(' + '));
        });

        const descSpan = document.createElement('span');
        descSpan.className = 'shortcut-desc';
        descSpan.innerHTML = `<i class="${shortcut.icon}"></i> ${shortcut.desc}`;

        item.appendChild(keysSpan);
        item.appendChild(descSpan);
        shortcutsList.appendChild(item);
    });
}

export function initShortcutsSidebar() {
    const sidebar = document.querySelector('.shortcuts-sidebar');
    if (sidebar) {
        // Initially collapse the sidebar
        sidebar.classList.add('collapsed');
    } else {
        console.warn('Shortcuts sidebar element not found');
        return;
    }

    const toggle = document.querySelector('.shortcuts-toggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
    } else {
        console.warn('Shortcuts toggle element not found');
    }
}