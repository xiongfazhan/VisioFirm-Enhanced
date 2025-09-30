/**
 * 数据集选择器模块
 * 用于在项目创建过程中选择已有的数据集
 */
class DatasetSelector {
    constructor(options = {}) {
        this.apiBase = '/datasets/api';
        this.multiSelect = options.multiSelect || false;
        this.selectedDatasets = [];
        this.datasets = [];
        this.onSelectionChange = options.onSelectionChange || (() => {});
        this.onConfirm = options.onConfirm || (() => {});
        this.isInitialized = false;
    }

    /**
     * 初始化选择器
     */
    async initialize(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error(`容器元素 ${containerId} 不存在`);
            return false;
        }

        try {
            await this.loadDatasets();
            this.render();
            this.isInitialized = true;
            return true;
        } catch (error) {
            console.error('初始化数据集选择器失败:', error);
            this.showError('初始化失败，请重试');
            return false;
        }
    }

    /**
     * 加载数据集列表
     */
    async loadDatasets() {
        try {
            const response = await fetch(`${this.apiBase}/list?limit=100`);
            const result = await response.json();

            if (result.success) {
                this.datasets = result.data.datasets.filter(dataset => dataset.status === 'ready');
            } else {
                throw new Error(result.error || '加载数据集失败');
            }
        } catch (error) {
            console.error('加载数据集失败:', error);
            throw error;
        }
    }

    /**
     * 渲染选择器界面
     */
    render() {
        if (!this.container) return;

        const html = `
            <div class="dataset-selector">
                <div class="selector-header">
                    <h3>选择数据集</h3>
                    <div class="selector-search">
                        <input type="text" 
                               class="selector-search-input" 
                               placeholder="搜索数据集..."
                               onkeyup="datasetSelector.filterDatasets(this.value)">
                    </div>
                </div>
                
                <div class="selector-content">
                    ${this.datasets.length > 0 ? this.renderDatasetList() : this.renderEmptyState()}
                </div>
                
                <div class="selector-footer">
                    <div class="selected-info">
                        已选择: <span id="selectedCount">0</span> 个数据集
                    </div>
                    <div class="selector-actions">
                        <button type="button" class="btn btn-secondary" onclick="datasetSelector.clearSelection()">
                            清空选择
                        </button>
                        <button type="button" class="btn btn-primary" onclick="datasetSelector.confirmSelection()">
                            确认选择
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.container.innerHTML = html;
        this.updateSelectedCount();
    }

    /**
     * 渲染数据集列表
     */
    renderDatasetList() {
        return `
            <div class="selector-dataset-list">
                ${this.datasets.map(dataset => this.renderDatasetItem(dataset)).join('')}
            </div>
        `;
    }

    /**
     * 渲染单个数据集项
     */
    renderDatasetItem(dataset) {
        const isSelected = this.selectedDatasets.some(d => d.dataset_id === dataset.dataset_id);
        const inputType = this.multiSelect ? 'checkbox' : 'radio';
        const inputName = this.multiSelect ? `dataset_${dataset.dataset_id}` : 'selected_dataset';
        
        return `
            <div class="selector-dataset-item ${isSelected ? 'selected' : ''}" 
                 data-dataset-id="${dataset.dataset_id}">
                <div class="selector-item-header">
                    <label class="selector-item-checkbox">
                        <input type="${inputType}" 
                               name="${inputName}"
                               value="${dataset.dataset_id}"
                               ${isSelected ? 'checked' : ''}
                               onchange="datasetSelector.toggleSelection(${dataset.dataset_id}, this.checked)">
                        <span class="selector-dataset-name">${this.escapeHtml(dataset.name)}</span>
                    </label>
                    <span class="selector-dataset-type type-${dataset.dataset_type}">
                        ${this.getTypeDisplayName(dataset.dataset_type)}
                    </span>
                </div>
                
                <div class="selector-dataset-description">
                    ${this.escapeHtml(dataset.description || '暂无描述')}
                </div>
                
                <div class="selector-dataset-stats">
                    <span class="stat-item">
                        <strong>${dataset.image_count || 0}</strong> 图片
                    </span>
                    <span class="stat-item">
                        <strong>${dataset.class_count || 0}</strong> 类别
                    </span>
                    <span class="stat-item">
                        <strong>${this.formatFileSize(dataset.file_size || 0)}</strong>
                    </span>
                </div>
                
                ${dataset.classes && dataset.classes.length > 0 ? `
                <div class="selector-dataset-classes">
                    <strong>类别:</strong>
                    ${dataset.classes.slice(0, 5).map(cls => 
                        `<span class="class-tag">${this.escapeHtml(cls)}</span>`
                    ).join('')}
                    ${dataset.classes.length > 5 ? `<span class="class-more">+${dataset.classes.length - 5}</span>` : ''}
                </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * 渲染空状态
     */
    renderEmptyState() {
        return `
            <div class="selector-empty-state">
                <h4>暂无可用数据集</h4>
                <p>请先创建或下载数据集</p>
                <a href="/datasets" class="btn btn-primary">管理数据集</a>
            </div>
        `;
    }

    /**
     * 切换数据集选择状态
     */
    toggleSelection(datasetId, isSelected) {
        const dataset = this.datasets.find(d => d.dataset_id === datasetId);
        if (!dataset) return;

        if (isSelected) {
            if (this.multiSelect) {
                // 多选模式
                if (!this.selectedDatasets.some(d => d.dataset_id === datasetId)) {
                    this.selectedDatasets.push(dataset);
                }
            } else {
                // 单选模式
                this.selectedDatasets = [dataset];
                // 取消其他选项的选中状态
                this.container.querySelectorAll('input[type="radio"]').forEach(input => {
                    if (input.value !== datasetId.toString()) {
                        input.checked = false;
                    }
                });
            }
        } else {
            // 取消选择
            this.selectedDatasets = this.selectedDatasets.filter(d => d.dataset_id !== datasetId);
        }

        this.updateUI();
        this.onSelectionChange(this.selectedDatasets);
    }

    /**
     * 更新UI状态
     */
    updateUI() {
        // 更新选中状态样式
        this.container.querySelectorAll('.selector-dataset-item').forEach(item => {
            const datasetId = parseInt(item.dataset('dataset-id') || item.getAttribute('data-dataset-id'));
            const isSelected = this.selectedDatasets.some(d => d.dataset_id === datasetId);
            
            if (isSelected) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });

        this.updateSelectedCount();
    }

    /**
     * 更新选中数量显示
     */
    updateSelectedCount() {
        const countElement = this.container.querySelector('#selectedCount');
        if (countElement) {
            countElement.textContent = this.selectedDatasets.length;
        }
    }

    /**
     * 筛选数据集
     */
    filterDatasets(query) {
        const filteredDatasets = query.trim() 
            ? this.datasets.filter(dataset => 
                dataset.name.toLowerCase().includes(query.toLowerCase()) ||
                (dataset.description && dataset.description.toLowerCase().includes(query.toLowerCase()))
              )
            : this.datasets;

        // 重新渲染列表
        const listContainer = this.container.querySelector('.selector-dataset-list');
        if (listContainer) {
            listContainer.innerHTML = filteredDatasets.map(dataset => this.renderDatasetItem(dataset)).join('');
        }
    }

    /**
     * 清空选择
     */
    clearSelection() {
        this.selectedDatasets = [];
        
        // 清空所有选中状态
        this.container.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(input => {
            input.checked = false;
        });
        
        this.updateUI();
        this.onSelectionChange(this.selectedDatasets);
    }

    /**
     * 确认选择
     */
    confirmSelection() {
        if (this.selectedDatasets.length === 0) {
            alert('请至少选择一个数据集');
            return;
        }

        this.onConfirm(this.selectedDatasets);
    }

    /**
     * 获取选中的数据集
     */
    getSelectedDatasets() {
        return [...this.selectedDatasets];
    }

    /**
     * 设置选中的数据集
     */
    setSelectedDatasets(datasets) {
        this.selectedDatasets = datasets;
        this.updateUI();
    }

    /**
     * 刷新数据集列表
     */
    async refresh() {
        try {
            await this.loadDatasets();
            this.render();
        } catch (error) {
            console.error('刷新数据集列表失败:', error);
            this.showError('刷新失败，请重试');
        }
    }

    /**
     * 获取类型显示名称
     */
    getTypeDisplayName(type) {
        const typeNames = {
            'custom': '自定义',
            'downloaded': '下载',
            'imported': '导入'
        };
        return typeNames[type] || type;
    }

    /**
     * 格式化文件大小
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let unitIndex = 0;
        let size = bytes;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 显示错误消息
     */
    showError(message) {
        console.error('DatasetSelector Error:', message);
        // 这里可以集成一个通知组件
        alert('错误: ' + message);
    }
}

// 全局数据集选择器实例
let datasetSelector;

/**
 * 创建数据集选择器
 */
function createDatasetSelector(containerId, options = {}) {
    const selector = new DatasetSelector(options);
    selector.initialize(containerId);
    return selector;
}

/**
 * 显示数据集选择模态框
 */
function showDatasetSelectorModal(options = {}) {
    // 创建模态框HTML
    const modalHtml = `
        <div id="datasetSelectorModal" class="modal active">
            <div class="modal-content" style="max-width: 800px;">
                <div class="modal-header">
                    <h2 class="modal-title">选择数据集</h2>
                    <button class="modal-close" onclick="hideDatasetSelectorModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div id="datasetSelectorContainer"></div>
                </div>
            </div>
        </div>
    `;

    // 添加到页面
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 创建选择器
    const selector = createDatasetSelector('datasetSelectorContainer', {
        multiSelect: options.multiSelect || false,
        onSelectionChange: options.onSelectionChange || (() => {}),
        onConfirm: (selectedDatasets) => {
            hideDatasetSelectorModal();
            if (options.onConfirm) {
                options.onConfirm(selectedDatasets);
            }
        }
    });

    return selector;
}

/**
 * 隐藏数据集选择模态框
 */
function hideDatasetSelectorModal() {
    const modal = document.getElementById('datasetSelectorModal');
    if (modal) {
        modal.remove();
    }
}

// CSS样式（如果需要动态添加）
const selectorStyles = `
<style>
.dataset-selector {
    border: 1px solid #e1e1e1;
    border-radius: 8px;
    background: white;
}

.selector-header {
    padding: 20px;
    border-bottom: 1px solid #e1e1e1;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.selector-header h3 {
    margin: 0;
    color: #2c3e50;
}

.selector-search-input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    width: 200px;
}

.selector-content {
    max-height: 400px;
    overflow-y: auto;
}

.selector-dataset-list {
    padding: 10px;
}

.selector-dataset-item {
    padding: 15px;
    border: 1px solid #e1e1e1;
    border-radius: 6px;
    margin-bottom: 10px;
    transition: all 0.2s ease;
    cursor: pointer;
}

.selector-dataset-item:hover {
    border-color: #3498db;
}

.selector-dataset-item.selected {
    border-color: #3498db;
    background-color: #f8f9fa;
}

.selector-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.selector-item-checkbox {
    display: flex;
    align-items: center;
    cursor: pointer;
    font-weight: 500;
}

.selector-item-checkbox input {
    margin-right: 8px;
}

.selector-dataset-description {
    color: #666;
    font-size: 14px;
    margin-bottom: 10px;
}

.selector-dataset-stats {
    display: flex;
    gap: 15px;
    margin-bottom: 10px;
    font-size: 14px;
}

.selector-dataset-classes {
    font-size: 14px;
}

.class-tag {
    display: inline-block;
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 12px;
    margin-right: 4px;
}

.class-more {
    color: #666;
    font-size: 12px;
}

.selector-footer {
    padding: 20px;
    border-top: 1px solid #e1e1e1;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.selector-actions {
    display: flex;
    gap: 10px;
}

.selector-empty-state {
    padding: 60px 20px;
    text-align: center;
    color: #666;
}

.selector-empty-state h4 {
    margin-bottom: 10px;
    color: #999;
}
</style>
`;

// 如果需要，可以动态添加样式
if (typeof document !== 'undefined' && !document.querySelector('#datasetSelectorStyles')) {
    document.head.insertAdjacentHTML('beforeend', `<style id="datasetSelectorStyles">${selectorStyles.replace(/<\/?style[^>]*>/g, '')}</style>`);
}