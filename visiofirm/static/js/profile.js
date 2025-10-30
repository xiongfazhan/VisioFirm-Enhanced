/**
 * 个人资料页面功能
 */

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeProfile();
    console.log('个人资料页面已初始化');
});

/**
 * 初始化个人资料页面
 */
function initializeProfile() {
    // 加载用户信息
    loadUserProfile();
    
    // 绑定事件
    bindProfileEvents();
    
    // 初始化其他功能
    initOtherFeatures();
}

/**
 * 加载用户信息
 */
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile');
        const result = await response.json();
        
        if (result.success) {
            displayUserProfile(result.data);
        } else {
            showError('加载用户信息失败: ' + result.error);
        }
    } catch (error) {
        console.error('加载用户信息失败:', error);
        showError('网络错误，请重试');
    }
}

/**
 * 显示用户信息
 */
function displayUserProfile(userData) {
    // 更新头像
    updateAvatar(userData);
    
    // 更新基本信息
    updateBasicInfo(userData);
    
    // 更新统计信息
    updateStats(userData.stats);
}

/**
 * 更新头像
 */
function updateAvatar(userData) {
    const avatar = document.querySelector('.avatar');
    if (avatar && userData.first_name) {
        const initials = (userData.first_name.charAt(0) + (userData.last_name || '').charAt(0)).toUpperCase();
        avatar.textContent = initials;
    }
}

/**
 * 更新基本信息
 */
function updateBasicInfo(userData) {
    const fields = {
        'username': userData.username,
        'email': userData.email,
        'first_name': userData.first_name,
        'last_name': userData.last_name,
        'company': userData.company || '未设置',
        'join_date': formatDate(userData.created_at)
    };
    
    Object.keys(fields).forEach(field => {
        const element = document.querySelector(`[data-field="${field}"]`);
        if (element) {
            element.textContent = fields[field];
        }
    });
}

/**
 * 更新统计信息
 */
function updateStats(stats) {
    if (!stats) return;
    
    const statFields = {
        'projects': stats.projects || 0,
        'datasets': stats.datasets || 0,
        'annotations': stats.annotations || 0,
        'training_sessions': stats.training_sessions || 0
    };
    
    Object.keys(statFields).forEach(field => {
        const element = document.querySelector(`[data-stat="${field}"]`);
        if (element) {
            element.textContent = statFields[field];
        }
    });
}

/**
 * 绑定个人资料事件
 */
function bindProfileEvents() {
    // 编辑按钮
    const editBtn = document.getElementById('editProfileBtn');
    if (editBtn) {
        editBtn.addEventListener('click', showEditModal);
    }
    
    // 更改密码按钮
    const changePasswordBtn = document.getElementById('changePasswordBtn');
    if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', showChangePasswordModal);
    }
    
    // 删除账户按钮
    const deleteAccountBtn = document.getElementById('deleteAccountBtn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', showDeleteAccountModal);
    }
    
    // 其他按钮
    bindOtherButtons();
}

/**
 * 绑定其他按钮
 */
function bindOtherButtons() {
    // 导出数据按钮
    const exportBtn = document.getElementById('exportDataBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportUserData);
    }
    
    // 设置按钮
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', () => {
            window.location.href = '/settings';
        });
    }
}

/**
 * 显示编辑模态框
 */
function showEditModal() {
    // 这里可以实现编辑个人资料的模态框
    alert('编辑个人资料功能将在后续版本中实现');
}

/**
 * 显示更改密码模态框
 */
function showChangePasswordModal() {
    // 这里可以实现更改密码的模态框
    alert('更改密码功能将在后续版本中实现');
}

/**
 * 显示删除账户模态框
 */
function showDeleteAccountModal() {
    if (!confirm('确定要删除账户吗？此操作不可撤销！')) {
        return;
    }
    
    if (!confirm('再次确认：删除账户将永久删除所有数据，包括项目、数据集和标注。确定继续吗？')) {
        return;
    }
    
    const password = prompt('请输入您的密码以确认删除：');
    if (!password) {
        return;
    }
    
    deleteAccount(password);
}

/**
 * 删除账户
 */
async function deleteAccount(password) {
    try {
        showLoading('正在删除账户...');
        
        const response = await fetch('/api/user/delete', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('账户已删除，正在跳转到首页...');
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            throw new Error(result.error || '删除账户失败');
        }
    } catch (error) {
        console.error('删除账户失败:', error);
        showError('删除账户失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * 导出用户数据
 */
async function exportUserData() {
    try {
        showLoading('正在导出数据...');
        
        const response = await fetch('/api/user/export');
        const result = await response.json();
        
        if (result.success) {
            // 创建下载链接
            const blob = new Blob([JSON.stringify(result.data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `user_data_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showSuccess('数据导出成功');
        } else {
            throw new Error(result.error || '导出数据失败');
        }
    } catch (error) {
        console.error('导出数据失败:', error);
        showError('导出数据失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * 显示加载状态
 */
function showLoading(message) {
    // 这里可以实现全局加载状态
    console.log('Loading:', message);
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    // 这里可以实现隐藏加载状态
    console.log('Loading hidden');
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

/**
 * 初始化其他功能
 */
function initOtherFeatures() {
    // 添加键盘快捷键
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // 其他初始化功能
    initAnimations();
}

/**
 * 处理键盘快捷键
 */
function handleKeyboardShortcuts(event) {
    // Ctrl+E 编辑个人资料
    if (event.ctrlKey && event.key === 'e') {
        event.preventDefault();
        showEditModal();
    }
    
    // Ctrl+P 更改密码
    if (event.ctrlKey && event.key === 'p') {
        event.preventDefault();
        showChangePasswordModal();
    }
}

/**
 * 初始化动画
 */
function initAnimations() {
    // 为统计卡片添加动画
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });
}
