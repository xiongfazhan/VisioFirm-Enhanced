/**
 * 数据集管理页面主要功能
 */

// 全局变量
let datasetManager;
let datasetDownloader;

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeDatasetManager();
    initializeDatasetDownloader();
    initializeEventListeners();
    console.log('数据集管理页面已初始化');
});

/**
 * 初始化所有事件监听器（替换onclick）
 */
function initializeEventListeners() {
    // 下载数据集按钮
    const downloadBtn = document.querySelector('.btn-secondary');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', showDownloadModal);
    }
    
    // 创建数据集按钮
    const createBtn = document.querySelector('.btn-primary');
    if (createBtn) {
        createBtn.addEventListener('click', createDataset);
    }
    
    // 搜索按钮
    const searchBtn = document.querySelector('.search-btn');
    if (searchBtn) {
        searchBtn.addEventListener('click', searchDatasets);
    }
    
    // 搜索输入框回车
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keypress', handleSearchKeypress);
    }
    
    // 类型过滤器
    const typeFilter = document.getElementById('typeFilter');
    if (typeFilter) {
        typeFilter.addEventListener('change', filterDatasets);
    }
    
    // 下载模态框关闭按钮
    const downloadModalClose = document.querySelector('#downloadModal .modal-close');
    if (downloadModalClose) {
        downloadModalClose.addEventListener('click', hideDownloadModal);
    }
    
    // 下载模态框底部取消按钮
    const downloadModalCancel = document.querySelector('#downloadModal .btn-secondary');
    if (downloadModalCancel) {
        downloadModalCancel.addEventListener('click', hideDownloadModal);
    }
    
    // 下载标签页按钮
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach((btn, index) => {
        const tabs = ['manual', 'search', 'popular'];
        btn.addEventListener('click', () => switchDownloadTab(tabs[index]));
    });
    
    // 公开数据集搜索按钮
    const publicSearchBtn = document.querySelector('#searchTab .search-btn');
    if (publicSearchBtn) {
        publicSearchBtn.addEventListener('click', searchPublicDatasets);
    }
    
    // 热门数据集卡片
    const popularDatasetCards = document.querySelectorAll('.dataset-card');
    const popularDatasets = ['coco', 'imagenet', 'voc', 'openimages'];
    const popularNames = ['COCO数据集', 'ImageNet', 'Pascal VOC', 'Open Images'];
    const popularDescriptions = [
        'Microsoft Common Objects in Context',
        '大规模图像分类数据集',
        'Pascal Visual Object Classes',
        'Google开源图像数据集'
    ];
    
    popularDatasetCards.forEach((card, index) => {
        if (index < popularDatasets.length) {
            card.addEventListener('click', () => {
                selectPopularDataset(
                    popularDatasets[index],
                    popularNames[index],
                    popularDescriptions[index]
                );
            });
        }
    });
    
    // 取消下载按钮
    const cancelBtn = document.getElementById('cancelBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelDownload);
    }
    
    // 开始下载按钮
    const downloadStartBtn = document.getElementById('downloadBtn');
    if (downloadStartBtn) {
        downloadStartBtn.addEventListener('click', startDownload);
    }
    
    // 详情模态框关闭按钮
    const detailModalClose = document.querySelector('#detailModal .modal-close');
    if (detailModalClose) {
        detailModalClose.addEventListener('click', hideDetailModal);
    }
    
    // 详情模态框底部关闭按钮
    const detailModalCloseBtn = document.querySelector('#detailModal .btn-secondary');
    if (detailModalCloseBtn) {
        detailModalCloseBtn.addEventListener('click', hideDetailModal);
    }
    
    // 关联项目按钮
    const linkProjectBtn = document.getElementById('linkProjectBtn');
    if (linkProjectBtn) {
        linkProjectBtn.addEventListener('click', linkToProject);
    }
}

/**
 * 初始化数据集管理器
 */
function initializeDatasetManager() {
    if (typeof DatasetManager !== 'undefined') {
        datasetManager = new DatasetManager();
        datasetManager.initialize();
    }
}

/**
 * 初始化数据集下载器
 */
function initializeDatasetDownloader() {
    if (typeof DatasetDownloader !== 'undefined') {
        datasetDownloader = new DatasetDownloader();
    }
}

/**
 * 显示下载模态框
 */
function showDownloadModal() {
    const modal = document.getElementById('downloadModal');
    if (modal) {
        modal.classList.add('active');
        
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
 * 取消下载
 */
function cancelDownload() {
    if (datasetDownloader && datasetDownloader.currentTaskId) {
        datasetDownloader.cancelDownload(datasetDownloader.currentTaskId);
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
 * 搜索数据集
 */
function searchDatasets() {
    if (datasetManager) {
        datasetManager.searchDatasets();
    }
}

/**
 * 处理搜索输入框回车事件
 */
function handleSearchKeypress(event) {
    if (event.key === 'Enter') {
        searchDatasets();
    }
}

/**
 * 过滤数据集
 */
function filterDatasets() {
    if (datasetManager) {
        datasetManager.filterDatasets();
    }
}

/**
 * 隐藏详情模态框
 */
function hideDetailModal() {
    const modal = document.getElementById('detailModal');
    if (modal) {
        modal.classList.remove('active');
    }
}
