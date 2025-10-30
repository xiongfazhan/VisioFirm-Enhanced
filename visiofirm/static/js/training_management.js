/**
 * 训练管理页面JavaScript
 */

// 全局变量
let trainingTasks = [];
let currentFilters = {
    status: '',
    project: ''
};

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    console.log('训练管理页面已初始化');
    
    // 绑定事件
    bindEvents();
    
    // 加载数据
    loadTrainingTasks();
    loadProjects();
    
    // 设置自动刷新
    setInterval(loadTrainingTasks, 10000); // 每10秒刷新一次
});

/**
 * 绑定事件
 */
function bindEvents() {
    // 刷新按钮
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadTrainingTasks);
    }
    
    // 新建训练按钮
    const createTrainingBtn = document.getElementById('createTrainingBtn');
    if (createTrainingBtn) {
        createTrainingBtn.addEventListener('click', createNewTraining);
    }
    
    // 过滤器
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            currentFilters.status = this.value;
            filterTasks();
        });
    }
    
    const projectFilter = document.getElementById('projectFilter');
    if (projectFilter) {
        projectFilter.addEventListener('change', function() {
            currentFilters.project = this.value;
            filterTasks();
        });
    }
    
    // 模态框关闭
    const closeModalBtns = document.querySelectorAll('#closeModalBtn, #closeModalBtn2');
    closeModalBtns.forEach(btn => {
        btn.addEventListener('click', closeModal);
    });
    
    // 点击模态框背景关闭
    const modal = document.getElementById('taskDetailModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
}

/**
 * 加载训练任务
 */
async function loadTrainingTasks() {
    try {
        const response = await fetch('/training/api/tasks');
        const result = await response.json();
        
        if (result.success) {
            trainingTasks = result.tasks || [];
            updateStatistics();
            renderTasks();
        } else {
            console.error('加载训练任务失败:', result.error);
            showError('加载训练任务失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载训练任务失败:', error);
        showError('加载训练任务失败: ' + error.message);
    }
}

/**
 * 加载项目列表
 */
async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const result = await response.json();
        
        if (result.success) {
            const projectFilter = document.getElementById('projectFilter');
            if (projectFilter) {
                // 清空现有选项（保留"所有项目"选项）
                projectFilter.innerHTML = '<option value="">所有项目</option>';
                
                // 添加项目选项
                result.projects.forEach(project => {
                    const option = document.createElement('option');
                    option.value = project.name;
                    option.textContent = project.name;
                    projectFilter.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('加载项目列表失败:', error);
    }
}

/**
 * 更新统计信息
 */
function updateStatistics() {
    const totalTasks = trainingTasks.length;
    const completedTasks = trainingTasks.filter(task => task.status === 'completed').length;
    const runningTasks = trainingTasks.filter(task => task.status === 'running').length;
    const failedTasks = trainingTasks.filter(task => task.status === 'failed').length;
    
    // 更新统计卡片
    updateStatCard('totalTasks', totalTasks);
    updateStatCard('completedTasks', completedTasks);
    updateStatCard('runningTasks', runningTasks);
    updateStatCard('failedTasks', failedTasks);
}

/**
 * 更新统计卡片
 */
function updateStatCard(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value;
    }
}

/**
 * 渲染任务列表
 */
function renderTasks() {
    const tasksList = document.getElementById('tasksList');
    if (!tasksList) return;
    
    if (trainingTasks.length === 0) {
        tasksList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i class="fas fa-tasks"></i>
                </div>
                <div class="empty-state-title">暂无训练任务</div>
                <div class="empty-state-text">开始您的第一个训练任务吧！</div>
                <button class="btn btn-primary" onclick="createNewTraining()">
                    <i class="fas fa-plus"></i>
                    新建训练
                </button>
            </div>
        `;
        return;
    }
    
    // 应用过滤器
    const filteredTasks = applyFilters(trainingTasks);
    
    tasksList.innerHTML = filteredTasks.map(task => createTaskCard(task)).join('');
    
    // 绑定任务卡片事件
    bindTaskCardEvents();
}

/**
 * 应用过滤器
 */
function applyFilters(tasks) {
    return tasks.filter(task => {
        if (currentFilters.status && task.status !== currentFilters.status) {
            return false;
        }
        if (currentFilters.project && task.project_name !== currentFilters.project) {
            return false;
        }
        return true;
    });
}

/**
 * 创建任务卡片
 */
function createTaskCard(task) {
    const statusClass = getStatusClass(task.status);
    const statusText = getStatusText(task.status);
    const progress = task.progress || 0;
    const createdAt = new Date(task.created_at).toLocaleString();
    const duration = calculateDuration(task.created_at, task.updated_at);
    
    return `
        <div class="task-card" data-task-id="${task.id}">
            <div class="task-header">
                <h3 class="task-title">${task.name || '未命名任务'}</h3>
                <span class="task-status ${statusClass}">${statusText}</span>
            </div>
            
            <div class="task-info">
                <div class="task-info-item">
                    <div class="task-info-label">项目</div>
                    <div class="task-info-value">${task.project_name || '未知'}</div>
                </div>
                <div class="task-info-item">
                    <div class="task-info-label">模型</div>
                    <div class="task-info-value">${task.model_type || '未知'}</div>
                </div>
                <div class="task-info-item">
                    <div class="task-info-label">创建时间</div>
                    <div class="task-info-value">${createdAt}</div>
                </div>
                <div class="task-info-item">
                    <div class="task-info-label">持续时间</div>
                    <div class="task-info-value">${duration}</div>
                </div>
            </div>
            
            ${task.status === 'running' ? `
                <div class="task-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <div class="progress-text">${progress}% 完成</div>
                </div>
            ` : ''}
            
            <div class="task-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="viewTaskDetail(${task.id})">
                    <i class="fas fa-eye"></i>
                    查看详情
                </button>
                ${task.status === 'running' ? `
                    <button class="btn btn-sm btn-warning" onclick="stopTask(${task.id})">
                        <i class="fas fa-stop"></i>
                        停止
                    </button>
                ` : ''}
                ${task.status === 'completed' ? `
                    <button class="btn btn-sm btn-success" onclick="downloadModel(${task.id})">
                        <i class="fas fa-download"></i>
                        下载模型
                    </button>
                ` : ''}
                <button class="btn btn-sm btn-danger" onclick="deleteTask(${task.id})">
                    <i class="fas fa-trash"></i>
                    删除
                </button>
            </div>
        </div>
    `;
}

/**
 * 获取状态样式类
 */
function getStatusClass(status) {
    const statusMap = {
        'running': 'running',
        'completed': 'completed',
        'failed': 'failed',
        'stopped': 'stopped',
        'pending': 'stopped'
    };
    return statusMap[status] || 'stopped';
}

/**
 * 获取状态文本
 */
function getStatusText(status) {
    const statusMap = {
        'running': '进行中',
        'completed': '已完成',
        'failed': '失败',
        'stopped': '已停止',
        'pending': '等待中'
    };
    return statusMap[status] || '未知';
}

/**
 * 计算持续时间
 */
function calculateDuration(startTime, endTime) {
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diff = end - start;
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 0) {
        return `${hours}小时${minutes}分钟`;
    } else {
        return `${minutes}分钟`;
    }
}

/**
 * 绑定任务卡片事件
 */
function bindTaskCardEvents() {
    // 任务卡片点击事件
    const taskCards = document.querySelectorAll('.task-card');
    taskCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // 如果点击的是按钮，不触发卡片点击
            if (e.target.closest('button')) {
                return;
            }
            
            const taskId = this.dataset.taskId;
            viewTaskDetail(taskId);
        });
    });
}

/**
 * 查看任务详情
 */
async function viewTaskDetail(taskId) {
    try {
        const response = await fetch(`/training/api/task/${taskId}`);
        const result = await response.json();
        
        if (result.success) {
            showTaskDetailModal(result.task);
        } else {
            showError('获取任务详情失败: ' + result.error);
        }
    } catch (error) {
        console.error('获取任务详情失败:', error);
        showError('获取任务详情失败: ' + error.message);
    }
}

/**
 * 显示任务详情模态框
 */
function showTaskDetailModal(task) {
    const modal = document.getElementById('taskDetailModal');
    const content = document.getElementById('taskDetailContent');
    
    if (!modal || !content) return;
    
    content.innerHTML = `
        <div class="task-detail">
            <div class="detail-section">
                <h4>基本信息</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>任务名称:</label>
                        <span>${task.name || '未命名任务'}</span>
                    </div>
                    <div class="detail-item">
                        <label>项目名称:</label>
                        <span>${task.project_name || '未知'}</span>
                    </div>
                    <div class="detail-item">
                        <label>模型类型:</label>
                        <span>${task.model_type || '未知'}</span>
                    </div>
                    <div class="detail-item">
                        <label>状态:</label>
                        <span class="task-status ${getStatusClass(task.status)}">${getStatusText(task.status)}</span>
                    </div>
                    <div class="detail-item">
                        <label>进度:</label>
                        <span>${task.progress || 0}%</span>
                    </div>
                    <div class="detail-item">
                        <label>创建时间:</label>
                        <span>${new Date(task.created_at).toLocaleString()}</span>
                    </div>
                </div>
            </div>
            
            ${task.metrics ? `
                <div class="detail-section">
                    <h4>训练指标</h4>
                    <div class="metrics-grid">
                        ${Object.entries(task.metrics).map(([key, value]) => `
                            <div class="metric-item">
                                <label>${key}:</label>
                                <span>${value}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
            
            ${task.logs && task.logs.length > 0 ? `
                <div class="detail-section">
                    <h4>训练日志</h4>
                    <div class="log-container">
                        ${task.logs.map(log => `
                            <div class="log-entry">
                                <span class="log-time">${new Date(log.timestamp).toLocaleString()}</span>
                                <span class="log-message">${log.message}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    modal.style.display = 'block';
}

/**
 * 关闭模态框
 */
function closeModal() {
    const modal = document.getElementById('taskDetailModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

/**
 * 停止任务
 */
async function stopTask(taskId) {
    if (!confirm('确定要停止这个训练任务吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/training/api/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ task_id: taskId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('任务已停止');
            loadTrainingTasks(); // 刷新列表
        } else {
            showError('停止任务失败: ' + result.error);
        }
    } catch (error) {
        console.error('停止任务失败:', error);
        showError('停止任务失败: ' + error.message);
    }
}

/**
 * 删除任务
 */
async function deleteTask(taskId) {
    if (!confirm('确定要删除这个训练任务吗？此操作不可恢复！')) {
        return;
    }
    
    try {
        const response = await fetch(`/training/api/task/${taskId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('任务已删除');
            loadTrainingTasks(); // 刷新列表
        } else {
            showError('删除任务失败: ' + result.error);
        }
    } catch (error) {
        console.error('删除任务失败:', error);
        showError('删除任务失败: ' + error.message);
    }
}

/**
 * 下载模型
 */
async function downloadModel(taskId) {
    try {
        const response = await fetch(`/training/api/download/${taskId}`);
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `model_${taskId}.pt`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showSuccess('模型下载已开始');
        } else {
            const result = await response.json();
            showError('下载模型失败: ' + result.error);
        }
    } catch (error) {
        console.error('下载模型失败:', error);
        showError('下载模型失败: ' + error.message);
    }
}

/**
 * 创建新训练
 */
function createNewTraining() {
    // 跳转到训练页面
    window.location.href = '/training';
}

/**
 * 过滤任务
 */
function filterTasks() {
    renderTasks();
}

/**
 * 显示成功消息
 */
function showSuccess(message) {
    // 这里可以集成一个通知系统
    alert('成功: ' + message);
}

/**
 * 显示错误消息
 */
function showError(message) {
    // 这里可以集成一个通知系统
    alert('错误: ' + message);
}
