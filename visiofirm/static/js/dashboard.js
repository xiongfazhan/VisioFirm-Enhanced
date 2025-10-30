/**
 * 仪表板页面主要功能
 */

// 全局变量
let currentProject = null;

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    console.log('仪表板页面已初始化');
});

/**
 * 初始化仪表板
 */
function initializeDashboard() {
    // 绑定菜单按钮事件
    bindMenuEvents();
    
    // 加载项目列表
    loadProjects();
    
    // 绑定其他事件
    bindOtherEvents();
}

/**
 * 绑定菜单事件
 */
function bindMenuEvents() {
    // 菜单按钮点击事件
    document.querySelectorAll('.menu-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const projectName = btn.dataset.project;
            const menu = document.getElementById('menu-' + projectName);
            const isVisible = menu.style.display === 'block';
            
            // 隐藏所有其他菜单
            document.querySelectorAll('.menu-dropdown').forEach(dropdown => {
                dropdown.style.display = 'none';
            });
            
            // 切换当前菜单
            menu.style.display = isVisible ? 'none' : 'block';
        });
    });
    
    // 概览按钮事件
    document.querySelectorAll('.overview-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const projectName = btn.dataset.project;
            showProjectOverview(projectName);
        });
    });
    
    // 导入按钮事件
    document.querySelectorAll('.import-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const projectName = btn.dataset.project;
            importImages(projectName);
        });
    });
    
    // 删除按钮事件
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const projectName = btn.dataset.project;
            deleteProject(projectName);
        });
    });
}

/**
 * 绑定其他事件
 */
function bindOtherEvents() {
    // 点击其他地方关闭菜单
    document.addEventListener('click', function() {
        document.querySelectorAll('.menu-dropdown').forEach(menu => {
            menu.style.display = 'none';
        });
    });
    
    // 创建项目按钮
    const createBtn = document.getElementById('createProjectBtn');
    if (createBtn) {
        createBtn.addEventListener('click', showCreateProjectModal);
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
            displayProjects(result.data);
        } else {
            showError('加载项目失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载项目失败:', error);
        showError('网络错误，请重试');
    }
}

/**
 * 显示项目列表
 */
function displayProjects(projects) {
    const container = document.getElementById('projectsContainer');
    if (!container) return;
    
    if (projects.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <h3>还没有项目</h3>
                <p>创建您的第一个项目开始标注工作</p>
                <a href="#" class="create-project-btn" id="createProjectBtn">
                    <i class="fas fa-plus"></i>
                    创建项目
                </a>
            </div>
        `;
        
        // 重新绑定创建按钮事件
        const createBtn = document.getElementById('createProjectBtn');
        if (createBtn) {
            createBtn.addEventListener('click', showCreateProjectModal);
        }
        return;
    }
    
    container.innerHTML = projects.map(project => `
        <div class="project-card">
            <div class="project-header">
                <h3 class="project-title">
                    <i class="fas fa-folder"></i>
                    ${project.name}
                </h3>
                <p class="project-description">${project.description || '暂无描述'}</p>
                <div class="project-meta">
                    <span><i class="fas fa-calendar"></i> ${formatDate(project.created_at)}</span>
                    <span><i class="fas fa-tag"></i> ${project.annotation_type}</span>
                </div>
                <button class="menu-btn" data-project="${project.name}">⋮</button>
                <div class="menu-dropdown" style="display: none;" id="menu-${project.name}">
                    <button class="overview-btn" data-project="${project.name}">概览</button>
                    <button class="import-btn" data-project="${project.name}">添加图片</button>
                    <button class="delete-btn" data-project="${project.name}">删除</button>
                </div>
            </div>
            <div class="project-stats">
                <div class="stat-item">
                    <div class="stat-value">${project.image_count || 0}</div>
                    <div class="stat-label">图片</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${project.annotation_count || 0}</div>
                    <div class="stat-label">标注</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${project.class_count || 0}</div>
                    <div class="stat-label">类别</div>
                </div>
            </div>
            <div class="project-actions">
                <a href="/annotation/${project.name}" class="action-btn annotation-btn">
                    <i class="fas fa-edit"></i>
                    <span>标注</span>
                </a>
                <a href="/training/${project.name}" class="action-btn training-btn">
                    <i class="fas fa-brain"></i>
                    <span>训练</span>
                </a>
            </div>
        </div>
    `).join('');
    
    // 重新绑定事件
    bindMenuEvents();
}

/**
 * 显示项目概览
 */
function showProjectOverview(projectName) {
    // 这里可以实现项目概览功能
    alert(`显示项目 ${projectName} 的概览信息`);
}

/**
 * 导入图片
 */
function importImages(projectName) {
    // 这里可以实现图片导入功能
    window.location.href = `/import/${projectName}`;
}

/**
 * 删除项目
 */
async function deleteProject(projectName) {
    if (!confirm(`确定要删除项目 "${projectName}" 吗？此操作不可撤销。`)) {
        return;
    }
    
    try {
        const response = await fetch(`/delete_project/${projectName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('项目删除成功');
            loadProjects(); // 重新加载项目列表
        } else {
            showError('删除失败: ' + result.error);
        }
    } catch (error) {
        console.error('删除项目失败:', error);
        showError('网络错误，请重试');
    }
}

/**
 * 显示创建项目模态框
 */
function showCreateProjectModal() {
    // 这里可以实现创建项目模态框
    const projectName = prompt('请输入项目名称:');
    if (projectName && projectName.trim()) {
        createProject(projectName.trim());
    }
}

/**
 * 创建项目
 */
async function createProject(projectName) {
    try {
        const response = await fetch('/api/projects', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: projectName,
                description: '',
                annotation_type: 'bounding_box'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('项目创建成功');
            loadProjects(); // 重新加载项目列表
        } else {
            showError('创建失败: ' + result.error);
        }
    } catch (error) {
        console.error('创建项目失败:', error);
        showError('网络错误，请重试');
    }
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
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
