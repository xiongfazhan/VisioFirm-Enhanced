/**
 * 数据集下载模块
 * 负责处理数据集下载相关功能
 */
class DatasetDownloader {
    constructor() {
        this.apiBase = '/datasets/api';
        this.downloadTasks = new Map();
        this.progressInterval = null;
        this.isDownloading = false;
    }

    /**
     * 启动数据集下载
     */
    async startDownload(url, name, description = '') {
        if (this.isDownloading) {
            alert('已有下载任务在进行中，请等待完成后再试');
            return false;
        }

        try {
            this.isDownloading = true;
            this.showProgressContainer();
            this.updateProgress(0, '正在启动下载任务...');

            const response = await fetch(`${this.apiBase}/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    name: name,
                    description: description
                })
            });

            const result = await response.json();

            if (result.success) {
                const taskId = result.data.task_id;
                this.downloadTasks.set(taskId, {
                    url: url,
                    name: name,
                    description: description,
                    startTime: new Date()
                });

                this.startProgressTracking(taskId);
                return taskId;
            } else {
                throw new Error(result.error || '启动下载失败');
            }
        } catch (error) {
            console.error('下载失败:', error);
            this.showError('下载失败: ' + error.message);
            this.isDownloading = false;
            this.hideProgressContainer();
            return false;
        }
    }

    /**
     * 开始跟踪下载进度
     */
    startProgressTracking(taskId) {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        this.progressInterval = setInterval(async () => {
            try {
                const status = await this.getDownloadProgress(taskId);
                
                if (status) {
                    this.updateProgressFromStatus(status);

                    // 检查是否完成
                    if (status.status === 'completed') {
                        this.onDownloadCompleted(taskId, status);
                    } else if (status.status === 'error') {
                        this.onDownloadError(taskId, status);
                    } else if (status.status === 'cancelled') {
                        this.onDownloadCancelled(taskId, status);
                    }
                } else {
                    // 任务不存在，可能已完成或出错
                    this.stopProgressTracking();
                    this.isDownloading = false;
                }
            } catch (error) {
                console.error('获取下载进度失败:', error);
                this.stopProgressTracking();
                this.isDownloading = false;
            }
        }, 1000); // 每秒更新一次
    }

    /**
     * 停止进度跟踪
     */
    stopProgressTracking() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    /**
     * 获取下载进度
     */
    async getDownloadProgress(taskId) {
        try {
            const response = await fetch(`${this.apiBase}/download/status/${taskId}`);
            const result = await response.json();

            if (result.success) {
                return result.data;
            } else {
                return null;
            }
        } catch (error) {
            console.error('获取下载状态失败:', error);
            return null;
        }
    }

    /**
     * 取消下载
     */
    async cancelDownload(taskId) {
        try {
            const response = await fetch(`${this.apiBase}/download/cancel/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const result = await response.json();

            if (result.success) {
                this.stopProgressTracking();
                this.isDownloading = false;
                this.hideProgressContainer();
                this.showSuccess('下载已取消');
                return true;
            } else {
                throw new Error(result.error || '取消下载失败');
            }
        } catch (error) {
            console.error('取消下载失败:', error);
            this.showError('取消下载失败: ' + error.message);
            return false;
        }
    }

    /**
     * 下载完成处理
     */
    onDownloadCompleted(taskId, status) {
        this.stopProgressTracking();
        this.isDownloading = false;
        
        this.updateProgress(100, status.message || '下载完成！');
        this.showSuccess('数据集下载完成！');
        
        // 3秒后隐藏进度条并刷新列表
        setTimeout(() => {
            this.hideProgressContainer();
            this.refreshDatasetList();
        }, 3000);

        this.downloadTasks.delete(taskId);
    }

    /**
     * 下载错误处理
     */
    onDownloadError(taskId, status) {
        this.stopProgressTracking();
        this.isDownloading = false;
        
        this.updateProgress(0, status.message || '下载失败');
        this.showError('下载失败: ' + (status.error || '未知错误'));
        
        setTimeout(() => {
            this.hideProgressContainer();
        }, 5000);

        this.downloadTasks.delete(taskId);
    }

    /**
     * 下载取消处理
     */
    onDownloadCancelled(taskId, status) {
        this.stopProgressTracking();
        this.isDownloading = false;
        
        this.updateProgress(0, status.message || '下载已取消');
        
        setTimeout(() => {
            this.hideProgressContainer();
        }, 3000);

        this.downloadTasks.delete(taskId);
    }

    /**
     * 根据状态更新进度
     */
    updateProgressFromStatus(status) {
        let message = status.message || '下载中...';
        
        if (status.status === 'downloading' && status.speed && status.eta) {
            const downloaded = this.formatFileSize(status.downloaded_size || 0);
            const total = this.formatFileSize(status.total_size || 0);
            message = `${message} (${downloaded}/${total}, 速度: ${status.speed}, 剩余: ${status.eta})`;
        }
        
        this.updateProgress(status.progress || 0, message);
    }

    /**
     * 显示进度容器
     */
    showProgressContainer() {
        const container = document.getElementById('progressContainer');
        if (container) {
            container.style.display = 'block';
        }

        // 禁用下载按钮
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.disabled = true;
            downloadBtn.textContent = '下载中...';
        }
    }

    /**
     * 隐藏进度容器
     */
    hideProgressContainer() {
        const container = document.getElementById('progressContainer');
        if (container) {
            container.style.display = 'none';
        }

        // 恢复下载按钮
        const downloadBtn = document.getElementById('downloadBtn');
        if (downloadBtn) {
            downloadBtn.disabled = false;
            downloadBtn.textContent = '开始下载';
        }
    }

    /**
     * 更新进度条
     */
    updateProgress(progress, message) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        if (progressFill) {
            progressFill.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        }

        if (progressText) {
            progressText.textContent = message;
        }
    }

    /**
     * 刷新数据集列表
     */
    refreshDatasetList() {
        if (window.datasetManager) {
            window.datasetManager.loadDatasets();
        }
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
}

// 全局下载器实例
let datasetDownloader;

/**
 * 初始化数据集下载器
 */
function initializeDatasetDownloader() {
    datasetDownloader = new DatasetDownloader();
}

/**
 * 显示下载模态框
 */
function showDownloadModal() {
    const modal = document.getElementById('downloadModal');
    if (modal) {
        modal.classList.add('active');
        
        // 初始化下载器（如果还没有初始化）
        if (!datasetDownloader) {
            initializeDatasetDownloader();
        }
        
        // 重置到手动输入标签页
        switchDownloadTab('manual');
    }
}

/**
 * 隐藏下载模态框
 */
function hideDownloadModal() {
    const modal = document.getElementById('downloadModal');
    if (modal) {
        modal.classList.remove('active');
        
        // 清空表单
        const form = modal.querySelector('.download-form');
        if (form) {
            form.reset();
        }
        
        // 隐藏进度条
        if (datasetDownloader) {
            datasetDownloader.hideProgressContainer();
        }
    }
}

/**
 * 开始下载
 */
async function startDownload(event) {
    event.preventDefault();
    
    const url = document.getElementById('downloadUrl')?.value?.trim();
    const name = document.getElementById('downloadName')?.value?.trim();
    const description = document.getElementById('downloadDescription')?.value?.trim();
    
    if (!url || !name) {
        alert('请填写数据集URL和名称');
        return;
    }
    
    // 验证URL格式
    try {
        new URL(url);
    } catch (error) {
        alert('请输入有效的URL地址');
        return;
    }
    
    if (!datasetDownloader) {
        initializeDatasetDownloader();
    }
    
    const taskId = await datasetDownloader.startDownload(url, name, description);
    
    if (taskId) {
        console.log(`下载任务已启动: ${taskId}`);
    }
}

/**
 * 创建数据集（跳转到项目创建页面）
 */
function createDataset() {
    // 这里可以跳转到项目创建页面，或者显示创建数据集的界面
    window.location.href = '/';
}

/**
 * 关联到项目
 */
function linkToProject() {
    // 这个函数会在数据集详情模态框中使用
    alert('关联到项目功能将在项目创建流程中实现');
}

/**
 * 切换下载标签页
 */
function switchDownloadTab(tabName) {
    // 隐藏所有标签页内容
    document.querySelectorAll('.download-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 移除所有标签按钮的active状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 显示选中的标签页
    const targetTab = document.getElementById(tabName + 'Tab');
    const targetBtn = document.querySelector(`[onclick="switchDownloadTab('${tabName}')"]`);
    
    if (targetTab) {
        targetTab.classList.add('active');
    }
    if (targetBtn) {
        targetBtn.classList.add('active');
    }
}

/**
 * 搜索公开数据集
 */
async function searchPublicDatasets() {
    const query = document.getElementById('datasetSearch')?.value?.trim();
    const source = document.getElementById('sourceFilter')?.value || 'all';
    
    if (!query) {
        alert('请输入搜索关键词');
        return;
    }
    
    try {
        const response = await fetch(`/datasets/api/public/search?query=${encodeURIComponent(query)}&source=${source}&limit=10`);
        const result = await response.json();
        
        if (result.success) {
            displaySearchResults(result.data.results);
        } else {
            throw new Error(result.error || '搜索失败');
        }
    } catch (error) {
        console.error('搜索失败:', error);
        alert('搜索失败: ' + error.message);
    }
}

/**
 * 显示搜索结果
 */
function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = '<div class="no-results">未找到相关数据集</div>';
        return;
    }
    
    container.innerHTML = results.map(result => `
        <div class="search-result-item" onclick="selectSearchResult('${result.url}', '${result.name}', '${result.description}')">
            <div class="result-title">${result.name}</div>
            <div class="result-description">${result.description}</div>
            <div class="result-meta">
                <span>来源: ${result.source}</span>
                <span>大小: ${result.size}</span>
                <span>格式: ${result.format}</span>
                <span>下载量: ${result.downloads}</span>
            </div>
        </div>
    `).join('');
}

/**
 * 选择搜索结果
 */
function selectSearchResult(url, name, description) {
    // 切换到手动输入标签页并填充数据
    switchDownloadTab('manual');
    
    document.getElementById('downloadUrl').value = url;
    document.getElementById('downloadName').value = name;
    document.getElementById('downloadDescription').value = description;
}

/**
 * 选择热门数据集
 */
function selectPopularDataset(datasetId, name, description) {
    // 预设的热门数据集URL（实际项目中应该从配置或API获取）
    const popularDatasets = {
        'coco': 'https://images.cocodataset.org/zips/train2017.zip',
        'imagenet': 'https://image-net.org/data/ILSVRC/2012/ILSVRC2012_img_train.tar',
        'voc': 'https://host.robots.ox.ac.uk/pascal/VOC/voc2012/VOCtrainval_11-May-2012.tar',
        'openimages': 'https://storage.googleapis.com/openimages/2018_04/train/train-images-boxable-with-labels.csv'
    };
    
    const url = popularDatasets[datasetId];
    if (url) {
        // 切换到手动输入标签页并填充数据
        switchDownloadTab('manual');
        
        document.getElementById('downloadUrl').value = url;
        document.getElementById('downloadName').value = name;
        document.getElementById('downloadDescription').value = description;
    } else {
        alert('该数据集暂不可用');
    }
}

/**
 * 取消下载
 */
function cancelDownload() {
    if (datasetDownloader && datasetDownloader.currentTaskId) {
        datasetDownloader.cancelDownload(datasetDownloader.currentTaskId);
    }
}

// 当页面加载完成时初始化
document.addEventListener('DOMContentLoaded', function() {
    // 数据集下载器会在需要时初始化
    console.log('数据集下载模块已准备就绪');
});