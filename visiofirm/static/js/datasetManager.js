/**
 * 数据集管理核心模块
 * 负责数据集的列表显示、搜索、筛选、详情查看等功能
 */
class DatasetManager {
    constructor() {
        this.apiBase = '/datasets/api';
        this.currentPage = 1;
        this.pageSize = 20;
        this.currentFilters = {};
        this.datasets = [];
        this.totalPages = 0;
        this.isLoading = false;
    }

    /**
     * 初始化数据集管理器
     */
    async initialize() {
        try {
            await this.loadDatasets();
            this.setupEventListeners();
        } catch (error) {
            console.error('初始化数据集管理器失败:', error);
            this.showError('初始化失败，请刷新页面重试');
        }
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 搜索输入框回车事件
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchDatasets();
                }
            });
        }

        // 类型筛选变化事件
        const typeFilter = document.getElementById('typeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', () => {
                this.filterDatasets();
            });
        }
    }

    /**
     * 加载数据集列表
     */
    async loadDatasets(page = 1, filters = {}) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading();

        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: this.pageSize.toString(),
                ...filters
            });

            const response = await fetch(`${this.apiBase}/list?${params}`);
            const result = await response.json();

            if (result.success) {
                this.datasets = result.data.datasets;
                this.currentPage = result.data.page;
                this.totalPages = result.data.total_pages;
                this.currentFilters = filters;

                this.renderDatasets();
                this.renderPagination();
            } else {
                throw new Error(result.error || '加载数据集失败');
            }
        } catch (error) {
            console.error('加载数据集失败:', error);
            this.showError('加载数据集失败: ' + error.message);
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * 渲染数据集网格
     */
    renderDatasets() {
        const grid = document.getElementById('datasetGrid');
        if (!grid) return;

        if (this.datasets.length === 0) {
            grid.innerHTML = this.getEmptyStateHTML();
            return;
        }

        const cardsHTML = this.datasets.map(dataset => this.createDatasetCard(dataset)).join('');
        grid.innerHTML = cardsHTML;
    }

    /**
     * 创建数据集卡片HTML
     */
    createDatasetCard(dataset) {
        const typeClass = `type-${dataset.dataset_type}`;
        const statusClass = `status-${dataset.status}`;
        
        const previewImages = dataset.sample_images || [];
        const previewHTML = previewImages.length > 0 
            ? previewImages.slice(0, 4).map(img => 
                `<img src="${img}" class="preview-img" alt="预览" onerror="this.style.display='none'">`
              ).join('')
            : '<div style="color: #999; font-size: 12px;">暂无预览</div>';

        return `
            <div class="dataset-card" onclick="showDatasetDetail(${dataset.dataset_id})">
                <div class="dataset-card-header">
                    <h3 class="dataset-name">${this.escapeHtml(dataset.name)}</h3>
                    <div class="dataset-type ${typeClass}">
                        ${this.getTypeDisplayName(dataset.dataset_type)}
                    </div>
                </div>
                
                <div class="dataset-description">
                    ${this.escapeHtml(dataset.description || '暂无描述')}
                </div>
                
                <div class="dataset-stats">
                    <div class="stat-item">
                        <div class="stat-value">${dataset.image_count || 0}</div>
                        <div class="stat-label">图片</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${dataset.class_count || 0}</div>
                        <div class="stat-label">类别</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${this.formatFileSize(dataset.file_size || 0)}</div>
                        <div class="stat-label">大小</div>
                    </div>
                </div>
                
                <div class="dataset-preview">
                    <div class="preview-images">
                        ${previewHTML}
                    </div>
                </div>
                
                <div class="dataset-actions-card" onclick="event.stopPropagation()">
                    <span class="status-badge ${statusClass}">${this.getStatusDisplayName(dataset.status)}</span>
                    <button class="btn btn-primary btn-small" onclick="linkDatasetToProject(${dataset.dataset_id})">
                        关联项目
                    </button>
                    <button class="btn btn-secondary btn-small" onclick="deleteDataset(${dataset.dataset_id})">
                        删除
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * 渲染分页组件
     */
    renderPagination() {
        const pagination = document.getElementById('pagination');
        if (!pagination || this.totalPages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';
        
        let paginationHTML = '';
        
        // 上一页按钮
        paginationHTML += `
            <button onclick="datasetManager.goToPage(${this.currentPage - 1})" 
                    ${this.currentPage <= 1 ? 'disabled' : ''}>
                上一页
            </button>
        `;
        
        // 页码按钮
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(this.totalPages, this.currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const isCurrentPage = i === this.currentPage;
            paginationHTML += `
                <button onclick="datasetManager.goToPage(${i})" 
                        class="${isCurrentPage ? 'current-page' : ''}">
                    ${i}
                </button>
            `;
        }
        
        // 下一页按钮
        paginationHTML += `
            <button onclick="datasetManager.goToPage(${this.currentPage + 1})" 
                    ${this.currentPage >= this.totalPages ? 'disabled' : ''}>
                下一页
            </button>
        `;
        
        pagination.innerHTML = paginationHTML;
    }

    /**
     * 跳转到指定页面
     */
    async goToPage(page) {
        if (page < 1 || page > this.totalPages || page === this.currentPage) {
            return;
        }
        await this.loadDatasets(page, this.currentFilters);
    }

    /**
     * 搜索数据集
     */
    async searchDatasets() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput ? searchInput.value.trim() : '';
        
        if (query) {
            try {
                const response = await fetch(`${this.apiBase}/search?query=${encodeURIComponent(query)}&page=1&limit=${this.pageSize}`);
                const result = await response.json();
                
                if (result.success) {
                    this.datasets = result.data.datasets;
                    this.currentPage = result.data.page;
                    this.totalPages = result.data.total_pages;
                    this.currentFilters = { query };
                    
                    this.renderDatasets();
                    this.renderPagination();
                } else {
                    throw new Error(result.error || '搜索失败');
                }
            } catch (error) {
                console.error('搜索数据集失败:', error);
                this.showError('搜索失败: ' + error.message);
            }
        } else {
            // 如果搜索框为空，重新加载所有数据集
            await this.loadDatasets();
        }
    }

    /**
     * 筛选数据集
     */
    async filterDatasets() {
        const typeFilter = document.getElementById('typeFilter');
        const type = typeFilter ? typeFilter.value : '';
        
        const filters = {};
        if (type) {
            filters.type = type;
        }
        
        await this.loadDatasets(1, filters);
    }

    /**
     * 获取数据集详情
     */
    async getDatasetDetail(datasetId) {
        try {
            const response = await fetch(`${this.apiBase}/${datasetId}`);
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            } else {
                throw new Error(result.error || '获取数据集详情失败');
            }
        } catch (error) {
            console.error('获取数据集详情失败:', error);
            throw error;
        }
    }

    /**
     * 删除数据集
     */
    async deleteDataset(datasetId) {
        if (!confirm('确定要删除这个数据集吗？此操作不可撤销。')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/${datasetId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('数据集删除成功');
                await this.loadDatasets(this.currentPage, this.currentFilters);
            } else {
                throw new Error(result.error || '删除失败');
            }
        } catch (error) {
            console.error('删除数据集失败:', error);
            this.showError('删除失败: ' + error.message);
        }
    }

    /**
     * 关联数据集到项目
     */
    async linkToProject(datasetId, projectName) {
        try {
            const response = await fetch(`${this.apiBase}/${datasetId}/link-project`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ project_name: projectName })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('数据集关联成功');
                return true;
            } else {
                throw new Error(result.error || '关联失败');
            }
        } catch (error) {
            console.error('关联数据集失败:', error);
            this.showError('关联失败: ' + error.message);
            return false;
        }
    }

    /**
     * 显示加载状态
     */
    showLoading() {
        const grid = document.getElementById('datasetGrid');
        if (grid) {
            grid.innerHTML = '<div class="loading">正在加载数据集...</div>';
        }
    }

    /**
     * 显示空状态
     */
    getEmptyStateHTML() {
        return `
            <div class="empty-state">
                <h3>暂无数据集</h3>
                <p>开始创建或下载您的第一个数据集吧！</p>
            </div>
        `;
    }

    /**
     * 显示成功消息
     */
    showSuccess(message) {
        // 这里可以集成一个通知组件
        alert(message);
    }

    /**
     * 显示错误消息
     */
    showError(message) {
        // 这里可以集成一个通知组件
        alert('错误: ' + message);
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
     * 获取状态显示名称
     */
    getStatusDisplayName(status) {
        const statusNames = {
            'ready': '就绪',
            'downloading': '下载中',
            'error': '错误'
        };
        return statusNames[status] || status;
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
}

// 全局数据集管理器实例
let datasetManager;

/**
 * 初始化数据集管理器
 */
function initializeDatasetManager() {
    datasetManager = new DatasetManager();
    datasetManager.initialize();
}

/**
 * 全局函数 - 显示数据集详情
 */
async function showDatasetDetail(datasetId) {
    try {
        const dataset = await datasetManager.getDatasetDetail(datasetId);
        
        const modal = document.getElementById('detailModal');
        const title = document.getElementById('detailTitle');
        const body = document.getElementById('detailBody');
        
        if (title) title.textContent = dataset.name;
        
        if (body) {
            body.innerHTML = `
                <div style="margin-bottom: 20px;">
                    <h4>基本信息</h4>
                    <p><strong>描述:</strong> ${dataset.description || '暂无描述'}</p>
                    <p><strong>类型:</strong> ${datasetManager.getTypeDisplayName(dataset.dataset_type)}</p>
                    <p><strong>格式:</strong> ${dataset.annotation_format || '无标注'}</p>
                    <p><strong>创建时间:</strong> ${new Date(dataset.created_at).toLocaleString()}</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4>统计信息</h4>
                    <p><strong>图片数量:</strong> ${dataset.image_count || 0}</p>
                    <p><strong>类别数量:</strong> ${dataset.class_count || 0}</p>
                    <p><strong>文件大小:</strong> ${datasetManager.formatFileSize(dataset.file_size || 0)}</p>
                </div>
                
                ${dataset.classes && dataset.classes.length > 0 ? `
                <div style="margin-bottom: 20px;">
                    <h4>类别列表</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                        ${dataset.classes.map(cls => `<span style="background: #f0f0f0; padding: 4px 8px; border-radius: 4px; font-size: 12px;">${cls}</span>`).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${dataset.projects && dataset.projects.length > 0 ? `
                <div>
                    <h4>关联项目</h4>
                    <ul>
                        ${dataset.projects.map(project => `<li>${project}</li>`).join('')}
                    </ul>
                </div>
                ` : ''}
            `;
        }
        
        if (modal) {
            modal.classList.add('active');
        }
    } catch (error) {
        datasetManager.showError('获取数据集详情失败: ' + error.message);
    }
}

/**
 * 全局函数 - 隐藏数据集详情模态框
 */
function hideDetailModal() {
    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * 全局函数 - 删除数据集
 */
function deleteDataset(datasetId) {
    if (datasetManager) {
        datasetManager.deleteDataset(datasetId);
    }
}

/**
 * 全局函数 - 关联数据集到项目
 */
function linkDatasetToProject(datasetId) {
    const projectName = prompt('请输入要关联的项目名称:');
    if (projectName && datasetManager) {
        datasetManager.linkToProject(datasetId, projectName.trim());
    }
}

/**
 * 全局函数 - 搜索数据集
 */
function searchDatasets() {
    if (datasetManager) {
        datasetManager.searchDatasets();
    }
}

/**
 * 全局函数 - 筛选数据集
 */
function filterDatasets() {
    if (datasetManager) {
        datasetManager.filterDatasets();
    }
}

/**
 * 全局函数 - 处理搜索框回车事件
 */
function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        searchDatasets();
    }
}