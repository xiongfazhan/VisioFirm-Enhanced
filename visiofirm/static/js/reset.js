/**
 * 重置密码页面功能
 */

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeReset();
    console.log('重置密码页面已初始化');
});

/**
 * 初始化重置密码页面
 */
function initializeReset() {
    // 绑定表单事件
    bindFormEvents();
    
    // 初始化其他功能
    initOtherFeatures();
}

/**
 * 绑定表单事件
 */
function bindFormEvents() {
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // 输入框验证
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('input', validateInput);
        input.addEventListener('blur', validateInput);
    });
}

/**
 * 处理表单提交
 */
function handleFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    // 验证表单
    if (!validateForm(formData)) {
        return;
    }
    
    // 显示加载状态
    showLoading('处理中...');
    
    // 提交表单
    submitResetRequest(formData);
}

/**
 * 验证表单
 */
function validateForm(formData) {
    const email = formData.get('email');
    
    if (!email || !isValidEmail(email)) {
        showError('请输入有效的邮箱地址');
        return false;
    }
    
    return true;
}

/**
 * 验证输入框
 */
function validateInput(event) {
    const input = event.target;
    const value = input.value.trim();
    
    // 移除之前的验证状态
    input.classList.remove('is-valid', 'is-invalid');
    
    if (input.type === 'email') {
        if (value && isValidEmail(value)) {
            input.classList.add('is-valid');
        } else if (value) {
            input.classList.add('is-invalid');
        }
    }
}

/**
 * 验证邮箱格式
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * 提交重置请求
 */
async function submitResetRequest(formData) {
    try {
        const response = await fetch('/auth/reset_password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: formData.get('email')
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('重置密码邮件已发送，请检查您的邮箱');
            clearForm();
        } else {
            throw new Error(result.error || '发送失败');
        }
    } catch (error) {
        console.error('重置密码失败:', error);
        showError('重置密码失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * 显示加载状态
 */
function showLoading(message) {
    const button = document.querySelector('.btn');
    if (button) {
        button.disabled = true;
        button.textContent = message;
    }
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const button = document.querySelector('.btn');
    if (button) {
        button.disabled = false;
        button.textContent = '发送重置邮件';
    }
}

/**
 * 显示成功消息
 */
function showSuccess(message) {
    showAlert(message, 'success');
}

/**
 * 显示错误消息
 */
function showError(message) {
    showAlert(message, 'danger');
}

/**
 * 显示警告消息
 */
function showWarning(message) {
    showAlert(message, 'info');
}

/**
 * 显示提示消息
 */
function showAlert(message, type) {
    // 移除现有的提示
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 创建新的提示
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    // 插入到表单前面
    const form = document.querySelector('form');
    if (form) {
        form.parentNode.insertBefore(alertDiv, form);
    }
    
    // 3秒后自动隐藏
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

/**
 * 清空表单
 */
function clearForm() {
    const form = document.querySelector('form');
    if (form) {
        form.reset();
        
        // 清除验证状态
        const inputs = document.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.classList.remove('is-valid', 'is-invalid');
        });
    }
}

/**
 * 初始化其他功能
 */
function initOtherFeatures() {
    // 自动聚焦到邮箱输入框
    const emailInput = document.querySelector('input[type="email"]');
    if (emailInput) {
        setTimeout(() => emailInput.focus(), 100);
    }
    
    // 添加键盘快捷键
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

/**
 * 处理键盘快捷键
 */
function handleKeyboardShortcuts(event) {
    // Enter键提交表单
    if (event.key === 'Enter') {
        const form = document.querySelector('form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape键清空表单
    if (event.key === 'Escape') {
        clearForm();
    }
}
