/**
 * 训练页面功能
 */

// 全局变量
let trainingStatus = 'idle';
let trainingProgress = 0;
let trainingLog = [];
let trainingMetrics = {};

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeTraining();
    console.log('训练页面已初始化');
});

/**
 * 初始化训练页面
 */
function initializeTraining() {
    // 获取模板数据
    const templateData = getTemplateData();
    
    // 初始化训练状态
    initializeTrainingStatus();
    
    // 绑定事件
    bindTrainingEvents();
    
    // 加载训练历史
    loadTrainingHistory();
}

/**
 * 获取模板数据
 */
function getTemplateData() {
    const templateDiv = document.getElementById('template-data');
    if (templateDiv) {
        return {
            projectName: templateDiv.dataset.projectName,
            isAuthenticated: templateDiv.dataset.isAuthenticated === 'true'
        };
    }
    return {};
}

/**
 * 初始化训练状态
 */
function initializeTrainingStatus() {
    updateTrainingStatus('idle', '准备开始训练');
    updateProgress(0, '等待开始训练');
}

/**
 * 绑定训练事件
 */
function bindTrainingEvents() {
    // 开始训练按钮
    const startBtn = document.getElementById('startTrainingBtn');
    if (startBtn) {
        startBtn.addEventListener('click', startTraining);
    }
    
    // 停止训练按钮
    const stopBtn = document.getElementById('stopTrainingBtn');
    if (stopBtn) {
        stopBtn.addEventListener('click', stopTraining);
    }
    
    // 训练参数输入
    bindTrainingParameters();
    
    // 其他事件
    bindOtherTrainingEvents();
}

/**
 * 绑定训练参数事件
 */
function bindTrainingParameters() {
    const inputs = document.querySelectorAll('.control-input');
    inputs.forEach(input => {
        input.addEventListener('change', validateTrainingParameters);
    });
    
    // 绑定模型选择事件
    const modelSelect = document.getElementById('modelType');
    if (modelSelect) {
        modelSelect.addEventListener('change', handleModelSelection);
    }
}

/**
 * 处理模型选择
 */
async function handleModelSelection(event) {
    const modelName = event.target.value;
    const modelInfo = document.getElementById('modelInfo');
    
    if (!modelName) return;
    
    try {
        // 显示检查状态
        modelInfo.innerHTML = '<small class="text-info">正在检查模型...</small>';
        
        // 检查模型是否已下载
        const templateData = getTemplateData();
        const response = await fetch(`/training/api/models?project_name=${templateData.projectName || 'test'}`);
        const result = await response.json();
        
        if (result.success) {
            const model = result.models.find(m => m.name === modelName);
            if (model) {
                if (model.downloaded) {
                    modelInfo.innerHTML = `<small class="text-success">✓ 模型已下载 (${model.size})</small>`;
                } else {
                    modelInfo.innerHTML = `<small class="text-warning">⚠ 模型未下载，开始训练时会自动下载 (${model.size})</small>`;
                }
            }
        }
    } catch (error) {
        console.error('检查模型状态失败:', error);
        modelInfo.innerHTML = '<small class="text-muted">无法检查模型状态</small>';
    }
}

/**
 * 绑定其他训练事件
 */
function bindOtherTrainingEvents() {
    // 可以添加其他训练相关事件
}

/**
 * 开始训练
 */
async function startTraining() {
    if (trainingStatus === 'training') {
        showError('训练已在进行中');
        return;
    }
    
    // 验证训练参数
    if (!validateTrainingParameters()) {
        return;
    }
    
    try {
        updateTrainingStatus('training', '正在启动训练...');
        
        const trainingConfig = getTrainingConfig();
        
        const response = await fetch('/training/api/start', {
            method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
            body: JSON.stringify(trainingConfig)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('训练已开始');
            startProgressTracking();
        } else {
            throw new Error(result.error || '启动训练失败');
        }
    } catch (error) {
        console.error('启动训练失败:', error);
        updateTrainingStatus('error', '启动训练失败');
        showError('启动训练失败: ' + error.message);
    }
}

/**
 * 停止训练
 */
async function stopTraining() {
    if (trainingStatus !== 'training') {
        showError('当前没有进行中的训练');
        return;
    }
    
    if (!confirm('确定要停止当前训练吗？')) {
        return;
    }
    
    try {
        const templateData = getTemplateData();
        const response = await fetch('/training/api/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_name: templateData.projectName || 'test'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateTrainingStatus('idle', '训练已停止');
            showSuccess('训练已停止');
        } else {
            throw new Error(result.error || '停止训练失败');
        }
    } catch (error) {
        console.error('停止训练失败:', error);
        showError('停止训练失败: ' + error.message);
    }
}

/**
 * 验证训练参数
 */
function validateTrainingParameters() {
    const epochs = document.getElementById('epochs')?.value;
    const batchSize = document.getElementById('batchSize')?.value;
    const learningRate = document.getElementById('learningRate')?.value;
    
    if (!epochs || epochs < 1 || epochs > 1000) {
        showError('训练轮数必须在1-1000之间');
        return false;
    }
    
    if (!batchSize || batchSize < 1 || batchSize > 128) {
        showError('批次大小必须在1-128之间');
        return false;
    }
    
    if (!learningRate || learningRate <= 0 || learningRate > 1) {
        showError('学习率必须在0-1之间');
        return false;
    }
    
    return true;
}

/**
 * 获取训练配置
 */
function getTrainingConfig() {
    const templateData = getTemplateData();
    return {
        project_name: templateData.projectName || 'test',
        epochs: parseInt(document.getElementById('epochs')?.value || 10),
        batch_size: parseInt(document.getElementById('batchSize')?.value || 32),
        learning_rate: parseFloat(document.getElementById('learningRate')?.value || 0.001),
        model_type: document.getElementById('modelType')?.value || 'YOLO',
        dataset_path: document.getElementById('datasetPath')?.value || ''
    };
}

/**
 * 更新训练状态
 */
function updateTrainingStatus(status, message) {
    trainingStatus = status;
    
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.querySelector('.status-text');
    
    if (statusIndicator) {
        statusIndicator.className = `status-indicator status-${status}`;
    }
    
    if (statusText) {
        statusText.textContent = message;
    }
    
    // 更新按钮状态
    updateButtonStates(status);
}

/**
 * 更新按钮状态
 */
function updateButtonStates(status) {
    const startBtn = document.getElementById('startTrainingBtn');
    const stopBtn = document.getElementById('stopTrainingBtn');
    
    if (startBtn) {
        startBtn.disabled = status === 'training';
        startBtn.textContent = status === 'training' ? '训练中...' : '开始训练';
    }
    
    if (stopBtn) {
        stopBtn.disabled = status !== 'training';
        stopBtn.style.display = status === 'training' ? 'inline-flex' : 'none';
    }
}

/**
 * 更新进度
 */
function updateProgress(progress, message) {
    trainingProgress = progress;
    
    const progressFill = document.querySelector('.progress-fill');
    const progressText = document.querySelector('.progress-text');
    
        if (progressFill) {
        progressFill.style.width = `${Math.min(100, Math.max(0, progress))}%`;
    }
    
    if (progressText) {
        progressText.textContent = message;
    }
}

/**
 * 开始进度跟踪
 */
function startProgressTracking() {
    const interval = setInterval(async () => {
        if (trainingStatus !== 'training') {
            clearInterval(interval);
            return;
        }
        
        try {
            const templateData = getTemplateData();
            const response = await fetch(`/training/api/status?project_name=${templateData.projectName || 'test'}`);
            const result = await response.json();
            
            if (result.success) {
                updateTrainingProgress(result.data);
                
                // 如果训练完成或失败，停止轮询
                if (result.data.status === 'completed' || result.data.status === 'failed' || result.data.status === 'stopped') {
                    clearInterval(interval);
                }
            }
        } catch (error) {
            console.error('获取训练状态失败:', error);
        }
    }, 3000); // 改为每3秒更新一次，减少频率
}

/**
 * 更新训练进度
 */
function updateTrainingProgress(data) {
    // 更新进度条
    const progress = data.progress || 0;
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressPercentage = document.getElementById('progressPercentage');
    
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
    }
    
    if (progressPercentage) {
        progressPercentage.textContent = `${progress}%`;
    }
    
    if (progressText) {
        progressText.textContent = data.message || getProgressText(data.status, progress);
    }
    
    // 更新指标
    updateTrainingMetrics(data.metrics);
    
    // 添加日志
    if (data.log) {
        addTrainingLog(data.log);
    }
    
    // 更新状态
    if (data.status === 'completed') {
        updateTrainingStatus('completed', '训练完成');
        showSuccess('🎉 训练完成！');
        // 停止进度条动画
        if (progressFill) {
            progressFill.classList.remove('animated');
        }
    } else if (data.status === 'error') {
        updateTrainingStatus('error', '训练出错');
        showError('❌ 训练出错: ' + data.error);
    } else if (data.status === 'running') {
        // 添加进度条动画
        if (progressFill) {
            progressFill.classList.add('animated');
        }
    }
}

/**
 * 获取进度文本
 */
function getProgressText(status, progress) {
    switch (status) {
        case 'running':
            return `训练进行中... ${progress}%`;
        case 'completed':
            return '训练完成！';
        case 'error':
            return '训练出错';
        case 'stopped':
            return '训练已停止';
        default:
            return '等待开始训练';
    }
}

/**
 * 更新训练指标
 */
function updateTrainingMetrics(metrics) {
    if (!metrics) return;
    
    trainingMetrics = metrics;
    
    // 更新准确率
    if (metrics.accuracy !== undefined) {
        const accuracyElement = document.querySelector('[data-metric="accuracy"]');
        if (accuracyElement) {
            accuracyElement.textContent = `${(metrics.accuracy * 100).toFixed(1)}%`;
        }
    }
    
    // 更新损失值
    if (metrics.loss !== undefined) {
        const lossElement = document.querySelector('[data-metric="loss"]');
        if (lossElement) {
            lossElement.textContent = metrics.loss.toFixed(4);
        }
    }
    
    // 更新轮数
    if (metrics.epoch !== undefined) {
        const epochElement = document.querySelector('[data-metric="epoch"]');
        if (epochElement) {
            epochElement.textContent = metrics.epoch;
        }
    }
}
        
/**
 * 添加训练日志
 */
function addTrainingLog(logEntry) {
    if (logEntry) {
        trainingLog.push(logEntry);
        
        const logContainer = document.querySelector('.training-log');
        if (logContainer) {
            const logElement = document.createElement('div');
            logElement.className = 'log-entry';
            logElement.innerHTML = `
                <span class="log-timestamp">${new Date().toLocaleTimeString()}</span>
                <span class="log-level-${logEntry.level}">[${logEntry.level.toUpperCase()}]</span>
                ${logEntry.message}
            `;
            
            logContainer.appendChild(logElement);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    }
}

/**
 * 加载训练历史
 */
async function loadTrainingHistory() {
    try {
        const templateData = getTemplateData();
        const response = await fetch(`/training/api/history?project_name=${templateData.projectName || 'test'}`);
        const result = await response.json();
        
        if (result.success) {
            displayTrainingHistory(result.history);
        }
    } catch (error) {
        console.error('加载训练历史失败:', error);
    }
}

/**
 * 显示训练历史
 */
function displayTrainingHistory(history) {
    // 这里可以实现训练历史的显示
    console.log('训练历史:', history);
}

/**
 * 显示成功消息
 */
function showSuccess(message) {
    // 这里可以集成一个通知组件
    alert('成功: ' + message);
}

/**
 * 显示错误消息
 */
function showError(message) {
    // 这里可以集成一个通知组件
    alert('错误: ' + message);
}