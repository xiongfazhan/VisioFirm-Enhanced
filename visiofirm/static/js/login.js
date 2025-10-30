/**
 * 登录页面功能
 */

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeLogin();
    console.log('登录页面已初始化');
});

/**
 * 初始化登录页面
 */
function initializeLogin() {
    // 初始化3D背景
    initThreeBackground();
    
    // 绑定表单事件
    bindFormEvents();
    
    // 其他初始化
    initOtherFeatures();
}

/**
 * 初始化3D背景
 */
function initThreeBackground() {
    // 这里可以添加Three.js背景动画
    // 暂时使用简单的CSS动画
    const canvas = document.getElementById('three-canvas');
    if (canvas) {
        // 简单的背景动画
        canvas.style.background = 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)';
        canvas.style.animation = 'gradientShift 10s ease infinite';
    }
}

/**
 * 绑定表单事件
 */
function bindFormEvents() {
    const form = document.querySelector('.login-form form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // 输入框焦点效果
    const inputs = document.querySelectorAll('.form-group input');
    inputs.forEach(input => {
        input.addEventListener('focus', handleInputFocus);
        input.addEventListener('blur', handleInputBlur);
    });
}

/**
 * 处理表单提交
 */
function handleFormSubmit(event) {
    const form = event.target;
    const formData = new FormData(form);
    
    // 表单验证
    const identifier = formData.get('identifier');
    const password = formData.get('password');
    
    if (!identifier || !password) {
        event.preventDefault();
        showError('请填写所有字段');
        return;
    }
    
    // 显示加载状态
    showLoading('登录中...');
    
    // 表单验证通过，允许正常提交
    console.log('登录表单提交:', { identifier, password: '***' });
    
    // 移除旧的错误消息
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 设置超时处理，防止无限加载
    setTimeout(() => {
        const button = document.querySelector('.login-form button');
        if (button && button.textContent === '登录中...') {
            hideLoading();
            showError('登录超时，请重试');
        }
    }, 10000); // 10秒超时
}

/**
 * 处理输入框焦点
 */
function handleInputFocus(event) {
    const input = event.target;
    const formGroup = input.closest('.form-group');
    if (formGroup) {
        formGroup.classList.add('focused');
    }
}

/**
 * 处理输入框失焦
 */
function handleInputBlur(event) {
    const input = event.target;
    const formGroup = input.closest('.form-group');
    if (formGroup) {
        formGroup.classList.remove('focused');
    }
}

/**
 * 初始化其他功能
 */
function initOtherFeatures() {
    // 添加键盘快捷键
    document.addEventListener('keydown', handleKeyboardShortcuts);
    
    // 自动聚焦到第一个输入框
    const firstInput = document.querySelector('.form-group input');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
    }
}

/**
 * 处理键盘快捷键
 */
function handleKeyboardShortcuts(event) {
    // Enter键提交表单
    if (event.key === 'Enter') {
        const form = document.querySelector('.login-form form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape键清空表单
    if (event.key === 'Escape') {
        const form = document.querySelector('.login-form form');
        if (form) {
            form.reset();
        }
    }
}

/**
 * 显示错误消息
 */
function showError(message) {
    // 移除现有的错误消息
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 创建新的错误消息
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    errorDiv.style.cssText = `
        color: #dc3545;
        font-size: 14px;
        margin-top: 10px;
        padding: 8px;
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 4px;
    `;
    
    // 插入到表单中
    const form = document.querySelector('.login-form form');
    if (form) {
        form.appendChild(errorDiv);
    }
}

/**
 * 显示成功消息
 */
function showSuccess(message) {
    // 移除现有的消息
    const existingMessage = document.querySelector('.success-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // 创建新的成功消息
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    successDiv.style.cssText = `
        color: #155724;
        font-size: 14px;
        margin-top: 10px;
        padding: 8px;
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
    `;
    
    // 插入到表单中
    const form = document.querySelector('.login-form form');
    if (form) {
        form.appendChild(successDiv);
    }
}

/**
 * 显示加载状态
 */
function showLoading(message) {
    const button = document.querySelector('.login-form button');
    if (button) {
        button.disabled = true;
        button.textContent = message;
        button.style.opacity = '0.7';
    }
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const button = document.querySelector('.login-form button');
    if (button) {
        button.disabled = false;
        button.textContent = '登录';
        button.style.opacity = '1';
    }
}
