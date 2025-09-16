// 训练模块JavaScript功能

// 全局变量
let currentTaskId = null;
let taskUpdateInterval = null;

// 打开创建任务模态框
function openCreateTaskModal() {
    document.getElementById('createTaskModal').style.display = 'block';
    // 重置表单
    document.getElementById('createTaskForm').reset();
    
    // 设置默认值
    document.getElementById('trainRatio').value = '0.7';
    document.getElementById('valRatio').value = '0.2';
    document.getElementById('testRatio').value = '0.1';
    document.getElementById('epochs').value = '100';
    document.getElementById('batchSize').value = '16';
    document.getElementById('learningRate').value = '0.01';
    document.getElementById('imageSize').value = '640';
    
    // 初始化数据集比例调整功能
    adjustDatasetRatios();
    updateRatioDisplay();
    
    // 添加实时验证
    addRealTimeValidation();
}

// 关闭创建任务模态框
function closeCreateTaskModal() {
    document.getElementById('createTaskModal').style.display = 'none';
}

// 验证表单数据
function validateTaskForm() {
    const taskName = document.getElementById('taskName').value.trim();
    const modelType = document.getElementById('modelType').value;
    const trainRatio = parseFloat(document.getElementById('trainRatio').value);
    const valRatio = parseFloat(document.getElementById('valRatio').value);
    const testRatio = parseFloat(document.getElementById('testRatio').value);
    const epochs = parseInt(document.getElementById('epochs').value);
    const batchSize = parseInt(document.getElementById('batchSize').value);
    const learningRate = parseFloat(document.getElementById('learningRate').value);
    const imageSize = parseInt(document.getElementById('imageSize').value);
    
    // 基本字段验证
    if (!taskName) {
        showAlert('请输入任务名称', 'error');
        return false;
    }
    
    if (taskName.length < 2 || taskName.length > 50) {
        showAlert('任务名称长度应在2-50个字符之间', 'error');
        return false;
    }
    
    if (!modelType) {
        showAlert('请选择模型类型', 'error');
        return false;
    }
    
    // 数据集分割比例验证
    if (trainRatio <= 0 || trainRatio >= 1) {
        showAlert('训练集比例应在0-1之间', 'error');
        return false;
    }
    
    if (valRatio <= 0 || valRatio >= 1) {
        showAlert('验证集比例应在0-1之间', 'error');
        return false;
    }
    
    if (testRatio < 0 || testRatio >= 1) {
        showAlert('测试集比例应在0-1之间', 'error');
        return false;
    }
    
    const totalRatio = trainRatio + valRatio + testRatio;
    if (Math.abs(totalRatio - 1.0) > 0.01) {
        showAlert(`数据集分割比例之和必须等于1.0，当前为: ${totalRatio.toFixed(2)}`, 'error');
        return false;
    }
    
    // 训练参数验证
    if (epochs < 1 || epochs > 1000) {
        showAlert('训练轮数应在1-1000之间', 'error');
        return false;
    }
    
    if (batchSize < 1 || batchSize > 128) {
        showAlert('批次大小应在1-128之间', 'error');
        return false;
    }
    
    if (learningRate <= 0 || learningRate > 1) {
        showAlert('学习率应在0-1之间', 'error');
        return false;
    }
    
    if (imageSize < 320 || imageSize > 1280 || imageSize % 32 !== 0) {
        showAlert('图像尺寸应在320-1280之间且为32的倍数', 'error');
        return false;
    }
    
    return true;
}

// 自动调整数据集分割比例
function adjustDatasetRatios() {
    const trainInput = document.getElementById('trainRatio');
    const valInput = document.getElementById('valRatio');
    const testInput = document.getElementById('testRatio');
    
    function updateRatios(changedInput) {
        const train = parseFloat(trainInput.value) || 0;
        const val = parseFloat(valInput.value) || 0;
        const test = parseFloat(testInput.value) || 0;
        
        const total = train + val + test;
        
        if (total > 1.0) {
            // 如果总和超过1.0，按比例缩放
            const scale = 1.0 / total;
            trainInput.value = (train * scale).toFixed(2);
            valInput.value = (val * scale).toFixed(2);
            testInput.value = (test * scale).toFixed(2);
        } else if (total < 1.0 && changedInput) {
            // 如果总和小于1.0，调整其他比例
            const remaining = 1.0 - parseFloat(changedInput.value);
            if (changedInput === trainInput) {
                const ratio = val + test > 0 ? remaining / (val + test) : 0.5;
                valInput.value = (val * ratio).toFixed(2);
                testInput.value = (test * ratio).toFixed(2);
            } else if (changedInput === valInput) {
                const ratio = train + test > 0 ? remaining / (train + test) : 0.5;
                trainInput.value = (train * ratio).toFixed(2);
                testInput.value = (test * ratio).toFixed(2);
            } else if (changedInput === testInput) {
                const ratio = train + val > 0 ? remaining / (train + val) : 0.5;
                trainInput.value = (train * ratio).toFixed(2);
                valInput.value = (val * ratio).toFixed(2);
            }
        }
        
        // 更新显示
        updateRatioDisplay();
    }
    
    trainInput.addEventListener('input', () => updateRatios(trainInput));
    valInput.addEventListener('input', () => updateRatios(valInput));
    testInput.addEventListener('input', () => updateRatios(testInput));
}

// 更新比例显示
function updateRatioDisplay() {
    const train = parseFloat(document.getElementById('trainRatio').value) || 0;
    const val = parseFloat(document.getElementById('valRatio').value) || 0;
    const test = parseFloat(document.getElementById('testRatio').value) || 0;
    const total = train + val + test;
    
    // 添加总和显示
    let displayElement = document.getElementById('ratio-display');
    if (!displayElement) {
        displayElement = document.createElement('div');
        displayElement.id = 'ratio-display';
        displayElement.style.cssText = 'margin-top: 5px; font-size: 12px; color: #666;';
        document.querySelector('.form-row-3').appendChild(displayElement);
    }
    
    if (Math.abs(total - 1.0) <= 0.01) {
        displayElement.innerHTML = `<span style="color: green;">✓ 总和: ${total.toFixed(2)}</span>`;
    } else {
        displayElement.innerHTML = `<span style="color: red;">⚠ 总和: ${total.toFixed(2)} (应为1.0)</span>`;
    }
}
// 创建训练任务
async function createTask() {
    // 验证表单
    if (!validateTaskForm()) {
        return;
    }
    
    const taskData = {
        project_name: window.projectName,
        task_name: document.getElementById('taskName').value.trim(),
        model_type: document.getElementById('modelType').value,
        train_ratio: parseFloat(document.getElementById('trainRatio').value),
        val_ratio: parseFloat(document.getElementById('valRatio').value),
        test_ratio: parseFloat(document.getElementById('testRatio').value),
        epochs: parseInt(document.getElementById('epochs').value),
        batch_size: parseInt(document.getElementById('batchSize').value),
        learning_rate: parseFloat(document.getElementById('learningRate').value),
        image_size: parseInt(document.getElementById('imageSize').value),
        device: document.getElementById('device').value,
        optimizer: document.getElementById('optimizer').value
    };
    
    // 保存配置（如果提供了配置名称）
    const configName = document.getElementById('configName').value.trim();
    if (configName) {
        taskData.config_name = configName;
    }
    
    try {
        showLoading('正在创建训练任务...');
        
        const response = await fetch('/training/create_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(taskData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        hideLoading();
        
        if (result.success) {
            showAlert('训练任务创建成功！', 'success');
            closeCreateTaskModal();
            // 延迟刷新以显示新任务
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert('创建失败: ' + result.error, 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Create task error:', error);
        showAlert('创建失败: ' + error.message, 'error');
    }
}

// 添加实时验证
function addRealTimeValidation() {
    const taskNameInput = document.getElementById('taskName');
    const epochsInput = document.getElementById('epochs');
    const batchSizeInput = document.getElementById('batchSize');
    const learningRateInput = document.getElementById('learningRate');
    const imageSizeInput = document.getElementById('imageSize');
    
    // 任务名称验证
    taskNameInput.addEventListener('input', function() {
        const value = this.value.trim();
        if (value.length < 2) {
            this.style.borderColor = '#dc3545';
        } else if (value.length > 50) {
            this.style.borderColor = '#ffc107';
        } else {
            this.style.borderColor = '#28a745';
        }
    });
    
    // 训练轮数验证
    epochsInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        if (value < 1 || value > 1000) {
            this.style.borderColor = '#dc3545';
        } else {
            this.style.borderColor = '#28a745';
        }
    });
    
    // 批次大小验证
    batchSizeInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        if (value < 1 || value > 128) {
            this.style.borderColor = '#dc3545';
        } else {
            this.style.borderColor = '#28a745';
        }
    });
    
    // 学习率验证
    learningRateInput.addEventListener('input', function() {
        const value = parseFloat(this.value);
        if (value <= 0 || value > 1) {
            this.style.borderColor = '#dc3545';
        } else {
            this.style.borderColor = '#28a745';
        }
    });
    
    // 图像尺寸验证
    imageSizeInput.addEventListener('input', function() {
        const value = parseInt(this.value);
        if (value < 320 || value > 1280 || value % 32 !== 0) {
            this.style.borderColor = '#dc3545';
        } else {
            this.style.borderColor = '#28a745';
        }
    });
}

// 增强错误处理的API调用函数
async function makeAPICall(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };
    
    try {
        const response = await fetch(url, defaultOptions);
        
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
            
            // 尝试解析错误信息
            try {
                const errorData = await response.json();
                if (errorData.error) {
                    errorMessage = errorData.error;
                }
            } catch (e) {
                // 如果无法解析JSON，使用默认错误信息
            }
            
            throw new Error(errorMessage);
        }
        
        return await response.json();
        
    } catch (error) {
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('网络连接失败，请检查网络连接');
        }
        throw error;
    }
}
// 启动训练任务
async function startTask(taskId) {
    if (!confirm('确定要启动这个训练任务吗？')) {
        return;
    }
    
    try {
        showLoading('正在启动训练任务...');
        
        const result = await makeAPICall('/training/start_task', {
            method: 'POST',
            body: JSON.stringify({
                project_name: window.projectName,
                task_id: parseInt(taskId)
            })
        });
        
        hideLoading();
        
        if (result.success) {
            showAlert('训练任务已启动！', 'success');
            updateTaskCard(taskId, 'running', 0);
        } else {
            showAlert('启动失败: ' + result.error, 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Start task error:', error);
        showAlert('启动失败: ' + error.message, 'error');
    }
}

// 停止训练任务
async function stopTask(taskId) {
    if (!confirm('确定要停止这个训练任务吗？')) {
        return;
    }
    
    try {
        showLoading('正在停止训练任务...');
        
        const result = await makeAPICall('/training/stop_task', {
            method: 'POST',
            body: JSON.stringify({
                project_name: window.projectName,
                task_id: parseInt(taskId)
            })
        });
        
        hideLoading();
        
        if (result.success) {
            showAlert('训练任务已停止！', 'success');
            updateTaskCard(taskId, 'stopped', null);
        } else {
            showAlert('停止失败: ' + result.error, 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Stop task error:', error);
        showAlert('停止失败: ' + error.message, 'error');
    }
}

// 删除训练任务
async function deleteTask(taskId) {
    if (!confirm('确定要删除这个训练任务吗？此操作不可撤销。')) {
        return;
    }
    
    try {
        showLoading('正在删除训练任务...');
        
        const response = await fetch('/training/delete_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                project_name: window.projectName,
                task_id: parseInt(taskId)
            })
        });
        
        const result = await response.json();
        hideLoading();
        
        if (result.success) {
            showAlert('训练任务已删除！', 'success');
            // 移除任务卡片
            const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskCard) {
                taskCard.remove();
            }
        } else {
            showAlert('删除失败: ' + result.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showAlert('删除失败: ' + error.message, 'error');
    }
}

// 下载模型
async function downloadModel(taskId) {
    try {
        showLoading('正在准备下载...');
        
        // 直接跳转到下载链接
        window.location.href = `/training/download_model/${window.projectName}/${parseInt(taskId)}`;
        
        hideLoading();
        showAlert('模型下载已开始！', 'success');
    } catch (error) {
        hideLoading();
        showAlert('下载失败: ' + error.message, 'error');
    }
}

// 验证模型（增强版）
async function validateModel(taskId) {
    try {
        showLoading('正在验证模型...');
        
        const result = await makeAPICall('/training/validate_model', {
            method: 'POST',
            body: JSON.stringify({
                project_name: window.projectName,
                task_id: parseInt(taskId),
                plots: true,
                save_json: true
            })
        });
        
        hideLoading();
        
        if (result.success) {
            showValidationResults(result.metrics);
        } else {
            showAlert('验证失败: ' + result.error, 'error');
        }
    } catch (error) {
        hideLoading();
        console.error('Validate model error:', error);
        showAlert('验证失败: ' + error.message, 'error');
    }
}

// 显示验证结果
function showValidationResults(metrics) {
    let resultHtml = `
        <div class="validation-results">
            <h3>📊 模型验证结果</h3>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">mAP@0.5</div>
                    <div class="metric-value">${(metrics.mAP50 * 100).toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">mAP@0.5:0.95</div>
                    <div class="metric-value">${(metrics['mAP50-95'] * 100).toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">精确率</div>
                    <div class="metric-value">${(metrics.precision * 100).toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">召回率</div>
                    <div class="metric-value">${(metrics.recall * 100).toFixed(2)}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">F1分数</div>
                    <div class="metric-value">${(metrics.f1_score * 100).toFixed(2)}%</div>
                </div>
            </div>
    `;
    
    // 显示每个类别的指标
    if (metrics.class_metrics) {
        resultHtml += `
            <h4>🏷️ 每个类别的指标</h4>
            <div class="class-metrics">
        `;
        
        for (const [className, classMetrics] of Object.entries(metrics.class_metrics)) {
            resultHtml += `
                <div class="class-metric-item">
                    <span class="class-name">${className}</span>
                    <span class="class-ap">AP50: ${(classMetrics.AP50 * 100).toFixed(2)}%</span>
                </div>
            `;
        }
        
        resultHtml += '</div>';
    }
    
    resultHtml += '</div>';
    
    // 在模态框中显示结果
    showCustomModal('模型验证结果', resultHtml);
}

// 模型导出功能
async function exportModel(taskId) {
    try {
        // 获取支持的导出格式
        const formatsResult = await makeAPICall('/training/export_formats');
        
        if (!formatsResult.success) {
            showAlert('获取导出格式失败', 'error');
            return;
        }
        
        showExportDialog(taskId, formatsResult.formats);
        
    } catch (error) {
        console.error('Export model error:', error);
        showAlert('导出模型失败: ' + error.message, 'error');
    }
}

// 显示导出对话框
function showExportDialog(taskId, formats) {
    let dialogHtml = `
        <div class="export-dialog">
            <h3>📦 导出模型</h3>
            <form id="exportForm">
                <div class="form-group">
                    <label class="form-label">导出格式 *</label>
                    <select class="form-control" id="exportFormat" required>
    `;
    
    for (const [key, format] of Object.entries(formats)) {
        const selected = format.recommended ? 'selected' : '';
        const requires = format.requires ? ` (需要: ${format.requires})` : '';
        dialogHtml += `<option value="${key}" ${selected}>${format.name} - ${format.description}${requires}</option>`;
    }
    
    dialogHtml += `
                    </select>
                </div>
                
                <div class="form-group">
                    <label class="form-label">优化选项</label>
                    <div class="checkbox-group">
                        <label><input type="checkbox" id="exportHalf"> FP16量化 (减少模型大小)</label>
                        <label><input type="checkbox" id="exportSimplify" checked> 简化模型</label>
                        <label><input type="checkbox" id="exportDynamic"> 动态输入尺寸</label>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">ONNX Opset版本</label>
                        <input type="number" class="form-control" id="exportOpset" value="12" min="9" max="16">
                    </div>
                    <div class="form-group">
                        <label class="form-label">批处理大小</label>
                        <input type="number" class="form-control" id="exportBatch" value="1" min="1" max="32">
                    </div>
                </div>
            </form>
            
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" onclick="closeCustomModal()">取消</button>
                <button type="button" class="btn btn-primary" onclick="performExport(${taskId})">开始导出</button>
            </div>
        </div>
    `;
    
    showCustomModal('导出模型', dialogHtml);
}

// 执行导出
async function performExport(taskId) {
    try {
        const format = document.getElementById('exportFormat').value;
        const half = document.getElementById('exportHalf').checked;
        const simplify = document.getElementById('exportSimplify').checked;
        const dynamic = document.getElementById('exportDynamic').checked;
        const opset = parseInt(document.getElementById('exportOpset').value);
        const batch = parseInt(document.getElementById('exportBatch').value);
        
        closeCustomModal();
        showLoading(`正在导出为 ${format.toUpperCase()} 格式...`);
        
        const result = await makeAPICall('/training/export_model', {
            method: 'POST',
            body: JSON.stringify({
                project_name: window.projectName,
                task_id: parseInt(taskId),
                format: format,
                half: half,
                simplify: simplify,
                dynamic: dynamic,
                opset: opset,
                batch: batch
            })
        });
        
        hideLoading();
        
        if (result.success) {
            showAlert(`模型已成功导出为 ${result.format.toUpperCase()} 格式\n文件大小: ${result.file_size_mb} MB`, 'success');
        } else {
            showAlert('导出失败: ' + result.error, 'error');
        }
        
    } catch (error) {
        hideLoading();
        console.error('Perform export error:', error);
        showAlert('导出失败: ' + error.message, 'error');
    }
}

// 查看任务详情
async function viewTaskDetails(taskId) {
    try {
        showLoading('正在加载任务详情...');
        
        const response = await fetch(`/training/task_status/${window.projectName}/${parseInt(taskId)}`);
        const result = await response.json();
        
        hideLoading();
        
        if (result.success) {
            showTaskDetails(result.task);
        } else {
            showAlert('加载失败: ' + result.error, 'error');
        }
    } catch (error) {
        hideLoading();
        showAlert('加载失败: ' + error.message, 'error');
    }
}

// 显示任务详情
function showTaskDetails(task) {
    const modal = document.getElementById('taskDetailsModal');
    const content = document.getElementById('taskDetailsContent');
    
    let html = `
        <div class="task-details-content">
            <h3>${task.task_name}</h3>
            <div class="details-grid">
                <div class="detail-item">
                    <strong>状态:</strong> 
                    <span class="task-status status-${task.status}">${task.status}</span>
                </div>
                <div class="detail-item">
                    <strong>模型类型:</strong> ${task.model_type}
                </div>
                <div class="detail-item">
                    <strong>进度:</strong> ${task.progress}%
                </div>
                <div class="detail-item">
                    <strong>创建时间:</strong> ${task.created_at}
                </div>
    `;
    
    if (task.started_at) {
        html += `<div class="detail-item"><strong>开始时间:</strong> ${task.started_at}</div>`;
    }
    
    if (task.completed_at) {
        html += `<div class="detail-item"><strong>完成时间:</strong> ${task.completed_at}</div>`;
    }
    
    if (task.error_message) {
        html += `<div class="detail-item"><strong>错误信息:</strong> <span style="color: red;">${task.error_message}</span></div>`;
    }
    
    html += '</div>';
    
    // 显示配置信息
    if (task.config) {
        html += `
            <h4>训练配置</h4>
            <div class="config-grid">
                <div class="config-item"><strong>训练轮数:</strong> ${task.config.epochs}</div>
                <div class="config-item"><strong>批次大小:</strong> ${task.config.batch_size}</div>
                <div class="config-item"><strong>学习率:</strong> ${task.config.learning_rate}</div>
                <div class="config-item"><strong>图像尺寸:</strong> ${task.config.image_size}</div>
                <div class="config-item"><strong>设备:</strong> ${task.config.device}</div>
                <div class="config-item"><strong>优化器:</strong> ${task.config.optimizer}</div>
            </div>
        `;
    }
    
    // 显示训练日志
    if (task.logs && task.logs.length > 0) {
        html += `
            <h4>训练日志</h4>
            <div class="logs-container">
                <table class="logs-table">
                    <thead>
                        <tr>
                            <th>轮次</th>
                            <th>损失</th>
                            <th>精度</th>
                            <th>验证损失</th>
                            <th>验证精度</th>
                            <th>时间</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        task.logs.forEach(log => {
            html += `
                <tr>
                    <td>${log.epoch}</td>
                    <td>${log.loss ? log.loss.toFixed(4) : '-'}</td>
                    <td>${log.accuracy ? (log.accuracy * 100).toFixed(2) + '%' : '-'}</td>
                    <td>${log.val_loss ? log.val_loss.toFixed(4) : '-'}</td>
                    <td>${log.val_accuracy ? (log.val_accuracy * 100).toFixed(2) + '%' : '-'}</td>
                    <td>${log.timestamp}</td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
    }
    
    // 显示指标
    if (task.metrics && Object.keys(task.metrics).length > 0) {
        html += `
            <h4>训练指标</h4>
            <div class="metrics-grid">
        `;
        
        for (const [key, value] of Object.entries(task.metrics)) {
            html += `<div class="metric-item"><strong>${key}:</strong> ${(value * 100).toFixed(2)}%</div>`;
        }
        
        html += '</div>';
    }
    
    html += '</div>';
    
    content.innerHTML = html;
    modal.style.display = 'block';
}

// 关闭任务详情模态框
function closeTaskDetailsModal() {
    document.getElementById('taskDetailsModal').style.display = 'none';
}

// 使用配置
function useConfig(configId) {
    // 这里可以实现加载配置到创建任务表单的功能
    showAlert('功能开发中...', 'info');
}

// 编辑配置
function editConfig(configId) {
    // 这里可以实现编辑配置的功能
    showAlert('功能开发中...', 'info');
}

// 更新任务状态（带重试机制）
async function updateTaskStatuses(retryCount = 0) {
    const maxRetries = 3;
    
    try {
        const result = await makeAPICall(`/training/tasks/${window.projectName}`);
        
        if (result.success) {
            result.tasks.forEach(task => {
                updateTaskCard(task.id, task.status, task.progress);
            });
        }
    } catch (error) {
        console.error('更新任务状态失败:', error);
        
        if (retryCount < maxRetries) {
            // 指数退让重试
            const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
            setTimeout(() => {
                updateTaskStatuses(retryCount + 1);
            }, delay);
        } else {
            // 重试失败后显示警告
            console.warn('多次重试后仍无法更新任务状态');
        }
    }
}

// 更新任务卡片
function updateTaskCard(taskId, status, progress) {
    const taskCard = document.querySelector(`[data-task-id="${taskId}"]`);
    if (!taskCard) return;
    
    // 确保参数类型正确
    taskId = parseInt(taskId);
    if (progress !== null && progress !== undefined) {
        progress = parseFloat(progress);
    }
    
    // 更新状态
    const statusElement = taskCard.querySelector('.task-status');
    if (statusElement) {
        statusElement.className = `task-status status-${status}`;
        statusElement.textContent = status;
    }
    
    // 更新进度条
    if (progress !== null) {
        const progressFill = taskCard.querySelector('.progress-fill');
        if (progressFill) {
            progressFill.style.width = `${progress}%`;
        }
    }
    
    // 更新操作按钮
    const actionsContainer = taskCard.querySelector('.task-actions');
    if (actionsContainer) {
        updateTaskActions(actionsContainer, taskId, status);
    }
}

// 更新任务操作按钮
function updateTaskActions(container, taskId, status) {
    taskId = parseInt(taskId);
    let html = '';
    
    if (status === 'pending') {
        html += `<button class="btn btn-primary" onclick="startTask('${taskId}')"><i class="fas fa-play"></i> 开始训练</button>`;
    } else if (status === 'running') {
        html += `<button class="btn btn-danger" onclick="stopTask('${taskId}')"><i class="fas fa-stop"></i> 停止训练</button>`;
    } else if (status === 'completed') {
        html += `<button class="btn btn-success" onclick="downloadModel('${taskId}')"><i class="fas fa-download"></i> 下载模型</button>`;
        html += `<button class="btn btn-secondary" onclick="validateModel('${taskId}')"><i class="fas fa-check"></i> 验证模型</button>`;
    }
    
    html += `<button class="btn btn-secondary" onclick="viewTaskDetails('${taskId}')"><i class="fas fa-eye"></i> 详情</button>`;
    
    if (status !== 'running') {
        html += `<button class="btn btn-danger" onclick="deleteTask('${taskId}')"><i class="fas fa-trash"></i> 删除</button>`;
    }
    
    container.innerHTML = html;
}

// 显示提示信息
function showAlert(message, type = 'info') {
    // 创建提示框
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        max-width: 400px;
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        animation: slideIn 0.3s ease;
    `;
    
    const colors = {
        success: { bg: '#d4edda', color: '#155724', border: '#c3e6cb' },
        error: { bg: '#f8d7da', color: '#721c24', border: '#f5c6cb' },
        warning: { bg: '#fff3cd', color: '#856404', border: '#ffeaa7' },
        info: { bg: '#d1ecf1', color: '#0c5460', border: '#bee5eb' }
    };
    
    const style = colors[type] || colors.info;
    alert.style.backgroundColor = style.bg;
    alert.style.color = style.color;
    alert.style.border = `1px solid ${style.border}`;
    
    alert.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 18px; cursor: pointer; color: ${style.color};">&times;</button>
        </div>
    `;
    
    document.body.appendChild(alert);
    
    // 自动移除
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
}

// 显示加载状态
function showLoading(message = '加载中...') {
    const loading = document.createElement('div');
    loading.id = 'loadingOverlay';
    loading.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10001;
    `;
    
    loading.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 8px; text-align: center;">
            <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
            <div>${message}</div>
        </div>
    `;
    
    document.body.appendChild(loading);
}

// 隐藏加载状态
function hideLoading() {
    const loading = document.getElementById('loadingOverlay');
    if (loading) {
        loading.remove();
    }
}

// 添加CSS动画
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .details-grid, .config-grid, .metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .detail-item, .config-item, .metric-item {
        padding: 10px;
        background: #f8f9fa;
        border-radius: 6px;
    }
    
    .logs-container {
        max-height: 300px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 6px;
    }
    
    .logs-table {
        width: 100%;
        border-collapse: collapse;
    }
    
    .logs-table th,
    .logs-table td {
        padding: 8px 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    
    .logs-table th {
        background: #f8f9fa;
        font-weight: bold;
    }
    
    .logs-table tr:hover {
        background: #f8f9fa;
    }
`;
document.head.appendChild(style);

// 显示自定义模态框
function showCustomModal(title, content) {
    // 创建模态框
    const modal = document.createElement('div');
    modal.id = 'customModal';
    modal.className = 'modal';
    modal.style.display = 'block';
    
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">${title}</div>
                <button class="close-btn" onclick="closeCustomModal()">&times;</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(modal);
    
    // 点击外部关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeCustomModal();
        }
    });
}

// 关闭自定义模态框
function closeCustomModal() {
    const modal = document.getElementById('customModal');
    if (modal) {
        modal.remove();
    }
}
window.onclick = function(event) {
    const createModal = document.getElementById('createTaskModal');
    const detailsModal = document.getElementById('taskDetailsModal');
    
    if (event.target === createModal) {
        closeCreateTaskModal();
    }
    if (event.target === detailsModal) {
        closeTaskDetailsModal();
    }
};

// 进度监控和可视化
class TrainingProgressMonitor {
    constructor() {
        this.charts = {};
        this.isMonitoring = false;
        this.currentTaskId = null;
        this.updateInterval = null;
    }
    
    // 开始监控训练任务
    startMonitoring(taskId) {
        this.currentTaskId = taskId;
        this.isMonitoring = true;
        
        // 创建监控界面
        this.createMonitoringInterface();
        
        // 开始定时更新
        this.updateInterval = setInterval(() => {
            this.updateProgress();
        }, 2000); // 每2秒更新一次
        
        // 初始化图表
        setTimeout(() => this.initializeCharts(), 100);
    }
    
    // 停止监控
    stopMonitoring() {
        this.isMonitoring = false;
        this.currentTaskId = null;
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        this.removeMonitoringInterface();
    }
    
    // 创建监控界面
    createMonitoringInterface() {
        // 检查是否已存在
        if (document.getElementById('progressMonitor')) {
            return;
        }
        
        const monitorHtml = `
            <div id="progressMonitor" class="progress-monitor">
                <div class="section-title">
                    <i class="fas fa-chart-line"></i>
                    训练进度监控
                    <span class="live-indicator">
                        <span class="live-dot"></span>
                        实时更新
                    </span>
                </div>
                
                <div class="progress-info">
                    <div class="progress-stats">
                        <div class="stat-item">
                            <span class="stat-label">当前轮次:</span>
                            <span id="currentEpoch">0</span> / <span id="totalEpochs">0</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">当前损失:</span>
                            <span id="currentLoss">--</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">预计剩余时间:</span>
                            <span id="estimatedTime">--</span>
                        </div>
                    </div>
                </div>
                
                <div class="progress-charts">
                    <div class="chart-container">
                        <div class="chart-title">训练损失曲线</div>
                        <canvas id="lossChart" width="400" height="200"></canvas>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">训练进度</div>
                        <canvas id="progressChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </div>
        `;
        
        // 插入到任务列表下方
        const tasksContainer = document.getElementById('tasks-container');
        tasksContainer.insertAdjacentHTML('afterend', monitorHtml);
    }
    
    // 移除监控界面
    removeMonitoringInterface() {
        const monitor = document.getElementById('progressMonitor');
        if (monitor) {
            monitor.remove();
        }
    }
    
    // 初始化图表
    initializeCharts() {
        // 检查Chart.js是否可用
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js未加载，无法显示图表');
            return;
        }
        
        // 损失曲线图
        const lossCtx = document.getElementById('lossChart');
        if (lossCtx) {
            this.charts.loss = new Chart(lossCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: '训练损失',
                        data: [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: '损失值'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: '训练轮次'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    }
                }
            });
        }
        
        // 进度环形图
        const progressCtx = document.getElementById('progressChart');
        if (progressCtx) {
            this.charts.progress = new Chart(progressCtx, {
                type: 'doughnut',
                data: {
                    labels: ['已完成', '剩余'],
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#28a745', '#e9ecef'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom'
                        }
                    }
                }
            });
        }
    }
    
    // 更新进度
    async updateProgress() {
        if (!this.isMonitoring || !this.currentTaskId) {
            return;
        }
        
        try {
            const result = await makeAPICall(`/training/task_status/${window.projectName}/${this.currentTaskId}`);
            
            if (result.success) {
                const task = result.task;
                this.updateProgressDisplay(task);
                
                // 如果任务完成或停止，停止监控
                if (task.status === 'completed' || task.status === 'stopped' || task.status === 'failed') {
                    setTimeout(() => this.stopMonitoring(), 2000);
                }
            }
        } catch (error) {
            console.error('更新进度失败:', error);
        }
    }
    
    // 更新进度显示
    updateProgressDisplay(task) {
        // 更新基本信息
        const currentEpoch = document.getElementById('currentEpoch');
        const totalEpochs = document.getElementById('totalEpochs');
        const currentLoss = document.getElementById('currentLoss');
        const estimatedTime = document.getElementById('estimatedTime');
        
        if (task.config && task.config.epochs) {
            const epochs = task.config.epochs;
            const progress = task.progress || 0;
            const currentEp = Math.floor((progress / 100) * epochs);
            
            if (currentEpoch) currentEpoch.textContent = currentEp;
            if (totalEpochs) totalEpochs.textContent = epochs;
            
            // 更新进度图
            if (this.charts.progress) {
                this.charts.progress.data.datasets[0].data = [progress, 100 - progress];
                this.charts.progress.update('none');
            }
        }
        
        // 更新损失图表
        if (task.logs && task.logs.length > 0 && this.charts.loss) {
            const labels = task.logs.map(log => log.epoch);
            const lossData = task.logs.map(log => log.loss);
            
            this.charts.loss.data.labels = labels;
            this.charts.loss.data.datasets[0].data = lossData;
            this.charts.loss.update('none');
            
            // 更新当前损失
            if (currentLoss && lossData.length > 0) {
                currentLoss.textContent = lossData[lossData.length - 1].toFixed(4);
            }
        }
        
        // 计算预计剩余时间（简单估算）
        if (estimatedTime && task.started_at && task.progress > 0) {
            const startTime = new Date(task.started_at);
            const now = new Date();
            const elapsed = now - startTime;
            const estimatedTotal = (elapsed / task.progress) * 100;
            const remaining = estimatedTotal - elapsed;
            
            if (remaining > 0) {
                const hours = Math.floor(remaining / (1000 * 60 * 60));
                const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
                estimatedTime.textContent = `${hours}h ${minutes}m`;
            } else {
                estimatedTime.textContent = '即将完成';
            }
        }
    }
}

// 全局进度监控器实例
let progressMonitor = new TrainingProgressMonitor();

// 重写startTask函数以集成进度监控
const originalStartTask = startTask;
startTask = async function(taskId) {
    const result = await originalStartTask(taskId);
    // 如果启动成功，开始监控
    if (result !== false) {
        progressMonitor.startMonitoring(taskId);
    }
    return result;
};

// 重写stopTask函数以停止监控
const originalStopTask = stopTask;
stopTask = async function(taskId) {
    const result = await originalStopTask(taskId);
    // 停止监控
    if (progressMonitor.currentTaskId == taskId) {
        progressMonitor.stopMonitoring();
    }
    return result;
};

// 资源监控类
class ResourceMonitor {
    constructor() {
        this.updateInterval = 5000; // 5秒更新一次
        this.intervalId = null;
        this.isMonitoring = false;
    }

    start() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.update();
        this.intervalId = setInterval(() => this.update(), this.updateInterval);
        console.log('资源监控已启动');
    }

    stop() {
        if (!this.isMonitoring) return;
        
        this.isMonitoring = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        console.log('资源监控已停止');
    }

    async update() {
        try {
            const response = await fetch(`/training/system_resources/${projectName}`);
            const result = await response.json();
            
            if (result.success) {
                this.displayResourceUsage(result.data);
                this.checkResourceWarnings(result.data);
            }
        } catch (error) {
            console.error('获取系统资源信息失败:', error);
        }
    }

    displayResourceUsage(data) {
        // 更新CPU使用率
        const cpuElement = document.getElementById('cpu-usage');
        if (cpuElement) {
            cpuElement.textContent = `${data.cpu_percent || 0}%`;
            cpuElement.className = this.getUsageClass(data.cpu_percent || 0);
        }

        // 更新内存使用率
        const memoryElement = document.getElementById('memory-usage');
        if (memoryElement) {
            memoryElement.textContent = `${data.memory_percent || 0}%`;
            memoryElement.className = this.getUsageClass(data.memory_percent || 0);
        }

        // 更新可用内存
        const memoryAvailableElement = document.getElementById('memory-available');
        if (memoryAvailableElement) {
            memoryAvailableElement.textContent = `${data.memory_available_gb || 0} GB`;
        }

        // 更新GPU信息
        const gpuContainer = document.getElementById('gpu-info');
        if (gpuContainer && data.gpu_info) {
            gpuContainer.innerHTML = '';
            data.gpu_info.forEach(gpu => {
                const gpuDiv = document.createElement('div');
                gpuDiv.className = 'gpu-item';
                gpuDiv.innerHTML = `
                    <div class="gpu-name">${gpu.name}</div>
                    <div class="gpu-memory">
                        <span class="${this.getUsageClass(gpu.memory_percent)}">
                            ${gpu.memory_percent}%
                        </span>
                        <span class="gpu-memory-detail">
                            ${gpu.memory_used_gb}/${gpu.memory_total_gb} GB
                        </span>
                    </div>
                `;
                gpuContainer.appendChild(gpuDiv);
            });
        }

        // 更新活跃任务数
        const activeTasksElement = document.getElementById('active-tasks');
        if (activeTasksElement) {
            const activeCount = data.active_tasks || 0;
            const maxCount = data.max_concurrent_tasks || 1;
            activeTasksElement.textContent = `${activeCount}/${maxCount}`;
            activeTasksElement.className = activeCount >= maxCount ? 'usage-high' : 'usage-normal';
        }
    }

    getUsageClass(percentage) {
        if (percentage >= 90) return 'usage-critical';
        if (percentage >= 75) return 'usage-high';
        if (percentage >= 50) return 'usage-medium';
        return 'usage-normal';
    }

    checkResourceWarnings(data) {
        const warnings = [];
        
        if (data.memory_percent >= 90) {
            warnings.push('内存使用率过高，可能影响训练性能');
        }
        
        if (data.cpu_percent >= 95) {
            warnings.push('CPU使用率过高，建议减少并发任务');
        }
        
        if (data.gpu_info) {
            data.gpu_info.forEach(gpu => {
                if (gpu.memory_percent >= 95) {
                    warnings.push(`GPU ${gpu.device} 内存使用率过高`);
                }
            });
        }
        
        if (data.active_tasks >= data.max_concurrent_tasks) {
            warnings.push('已达到最大并发任务数限制');
        }

        this.displayWarnings(warnings);
    }

    displayWarnings(warnings) {
        const warningContainer = document.getElementById('resource-warnings');
        if (!warningContainer) return;

        warningContainer.innerHTML = '';
        
        if (warnings.length === 0) {
            warningContainer.style.display = 'none';
            return;
        }

        warningContainer.style.display = 'block';
        warnings.forEach(warning => {
            const warningDiv = document.createElement('div');
            warningDiv.className = 'warning-item';
            warningDiv.innerHTML = `
                <i class="fas fa-exclamation-triangle"></i>
                <span>${warning}</span>
            `;
            warningContainer.appendChild(warningDiv);
        });
    }
}

// 性能优化器类
class PerformanceOptimizer {
    constructor() {
        this.suggestions = [];
    }

    async getSuggestions(modelType, config) {
        try {
            const response = await fetch(`/training/performance_suggestions/${projectName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model_type: modelType,
                    config: config
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.suggestions = result.data.suggestions;
                this.displaySuggestions();
                return this.suggestions;
            }
        } catch (error) {
            console.error('获取性能建议失败:', error);
        }
        return [];
    }

    async getOptimalConfig(modelType, epochs, device) {
        try {
            const response = await fetch(`/training/optimal_config/${projectName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model_type: modelType,
                    epochs: epochs,
                    device: device
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            }
        } catch (error) {
            console.error('获取优化配置失败:', error);
        }
        return null;
    }

    displaySuggestions() {
        const suggestionsContainer = document.getElementById('performance-suggestions');
        if (!suggestionsContainer) return;

        suggestionsContainer.innerHTML = '';
        
        if (this.suggestions.length === 0) {
            suggestionsContainer.innerHTML = '<p class="no-suggestions">当前配置良好，无需优化建议</p>';
            return;
        }

        this.suggestions.forEach(suggestion => {
            const suggestionDiv = document.createElement('div');
            suggestionDiv.className = `suggestion-item suggestion-${suggestion.type}`;
            
            let configChangesHtml = '';
            if (suggestion.config_changes) {
                const changes = Object.entries(suggestion.config_changes)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join(', ');
                configChangesHtml = `<div class="config-changes">建议配置: ${changes}</div>`;
            }
            
            suggestionDiv.innerHTML = `
                <div class="suggestion-header">
                    <i class="fas fa-lightbulb"></i>
                    <strong>${suggestion.issue}</strong>
                </div>
                <div class="suggestion-content">
                    <p>${suggestion.suggestion}</p>
                    ${configChangesHtml}
                </div>
                ${suggestion.config_changes ? `
                    <button class="btn btn-sm btn-primary apply-suggestion" 
                            data-changes='${JSON.stringify(suggestion.config_changes)}'>
                        应用建议
                    </button>
                ` : ''}
            `;
            
            suggestionsContainer.appendChild(suggestionDiv);
        });

        // 绑定应用建议按钮事件
        suggestionsContainer.querySelectorAll('.apply-suggestion').forEach(button => {
            button.addEventListener('click', (e) => {
                const changes = JSON.parse(e.target.dataset.changes);
                this.applyConfigChanges(changes);
            });
        });
    }

    applyConfigChanges(changes) {
        Object.entries(changes).forEach(([key, value]) => {
            const element = document.getElementById(key) || document.querySelector(`[name="${key}"]`);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = Boolean(value);
                } else {
                    element.value = value;
                }
                // 触发change事件
                element.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
        
        showAlert('已应用性能优化建议', 'success');
    }
}

// 全局实例
let resourceMonitor;
let performanceOptimizer;

// 在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    resourceMonitor = new ResourceMonitor();
    performanceOptimizer = new PerformanceOptimizer();
    
    // 启动资源监控
    resourceMonitor.start();
    
    // 绑定性能优化按钮
    const optimizeButton = document.getElementById('optimize-performance');
    if (optimizeButton) {
        optimizeButton.addEventListener('click', async () => {
            const modelType = document.getElementById('modelType')?.value || 'yolov8n';
            const config = getTrainingConfig();
            await performanceOptimizer.getSuggestions(modelType, config);
        });
    }
    
    // 绑定获取优化配置按钮
    const getOptimalConfigButton = document.getElementById('get-optimal-config');
    if (getOptimalConfigButton) {
        getOptimalConfigButton.addEventListener('click', async () => {
            const modelType = document.getElementById('modelType')?.value || 'yolov8n';
            const epochs = parseInt(document.getElementById('epochs')?.value) || 100;
            const device = document.getElementById('device')?.value || 'auto';
            
            const optimalConfig = await performanceOptimizer.getOptimalConfig(modelType, epochs, device);
            if (optimalConfig) {
                applyOptimalConfig(optimalConfig);
                showAlert('已应用优化配置', 'success');
            }
        });
    }
});

// 在页面卸载时停止监控
window.addEventListener('beforeunload', () => {
    if (resourceMonitor) {
        resourceMonitor.stop();
    }
});

function getTrainingConfig() {
    return {
        epochs: parseInt(document.getElementById('epochs')?.value) || 100,
        batch_size: parseInt(document.getElementById('batchSize')?.value) || 16,
        learning_rate: parseFloat(document.getElementById('learningRate')?.value) || 0.01,
        image_size: parseInt(document.getElementById('imageSize')?.value) || 640,
        device: document.getElementById('device')?.value || 'auto',
        optimizer: document.getElementById('optimizer')?.value || 'auto'
    };
}

function applyOptimalConfig(config) {
    Object.entries(config).forEach(([key, value]) => {
        let elementId = key;
        
        // 映射字段名到元素ID
        const fieldMapping = {
            'batch': 'batchSize',
            'lr0': 'learningRate',
            'imgsz': 'imageSize'
        };
        
        if (fieldMapping[key]) {
            elementId = fieldMapping[key];
        }
        
        const element = document.getElementById(elementId) || document.querySelector(`[name="${elementId}"]`);
        if (element) {
            if (typeof value === 'boolean') {
                element.checked = value;
            } else {
                element.value = value;
            }
            element.dispatchEvent(new Event('change', { bubbles: true }));
        }
    });
}