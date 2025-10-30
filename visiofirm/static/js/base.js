/**
 * 基础页面功能
 */

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeBase();
    console.log('基础页面已初始化');
});

/**
 * 初始化基础功能
 */
function initializeBase() {
    // 绑定用户菜单事件
    bindUserMenuEvents();
    
    // 绑定其他基础事件
    bindBaseEvents();
}

/**
 * 绑定用户菜单事件
 */
function bindUserMenuEvents() {
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userMenu = document.getElementById('userMenu');
    
    if (userMenuBtn && userMenu) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isVisible = userMenu.style.display === 'block';
            
            // 隐藏所有其他菜单
            document.querySelectorAll('.user-menu-dropdown').forEach(menu => {
                menu.style.display = 'none';
            });
            
            // 切换当前菜单
            userMenu.style.display = isVisible ? 'none' : 'block';
        });
    }
    
    // 点击其他地方关闭菜单
    document.addEventListener('click', function() {
        document.querySelectorAll('.user-menu-dropdown').forEach(menu => {
            menu.style.display = 'none';
        });
    });
}

/**
 * 绑定基础事件
 */
function bindBaseEvents() {
    // 导航链接高亮
    highlightActiveNavLink();
    
    // 其他基础事件
    bindOtherBaseEvents();
}

/**
 * 高亮当前导航链接
 */
function highlightActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href)) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * 绑定其他基础事件
 */
function bindOtherBaseEvents() {
    // 可以在这里添加其他基础功能
    // 比如：主题切换、语言切换等
}

/**
 * 显示通知消息
 */
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // 添加样式
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        border-radius: 6px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    
    // 根据类型设置背景色
    const colors = {
        'success': '#28a745',
        'error': '#dc3545',
        'warning': '#ffc107',
        'info': '#17a2b8'
    };
    
    notification.style.backgroundColor = colors[type] || colors.info;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 3秒后自动移除
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * 显示加载状态
 */
function showLoading(message = '加载中...') {
    const loading = document.createElement('div');
    loading.id = 'globalLoading';
    loading.innerHTML = `
        <div class="loading-overlay">
            <div class="loading-spinner"></div>
            <div class="loading-text">${message}</div>
        </div>
    `;
    
    loading.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    `;
    
    document.body.appendChild(loading);
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const loading = document.getElementById('globalLoading');
    if (loading && loading.parentNode) {
        loading.parentNode.removeChild(loading);
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
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 格式化文件大小
 */
function formatFileSize(bytes) {
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
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 节流函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
