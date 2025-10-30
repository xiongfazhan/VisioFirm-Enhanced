/**
 * 注册页面功能
 */

// 全局变量
let passwordStrength = 0;

/**
 * 页面初始化
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeRegister();
    console.log('注册页面已初始化');
});

/**
 * 初始化注册页面
 */
function initializeRegister() {
    // 初始化3D背景
    initThreeBackground();
    
    // 绑定表单事件
    bindFormEvents();
    
    // 初始化其他功能
    initOtherFeatures();
}

/**
 * 初始化3D背景
 */
function initThreeBackground() {
    // 这里可以添加Three.js背景动画
    const canvas = document.getElementById('three-canvas');
    if (canvas) {
        canvas.style.background = 'linear-gradient(45deg, #667eea 0%, #764ba2 100%)';
        canvas.style.animation = 'gradientShift 10s ease infinite';
    }
}

/**
 * 绑定表单事件
 */
function bindFormEvents() {
    const form = document.querySelector('.register-form form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
    
    // 密码强度检测
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        passwordInput.addEventListener('input', checkPasswordStrength);
    }
    
    // 实时验证
    const inputs = document.querySelectorAll('.form-group input');
    inputs.forEach(input => {
        input.addEventListener('input', validateInput);
        input.addEventListener('blur', validateInput);
    });
    
    // 确认密码验证
    const confirmPasswordInput = document.getElementById('confirm_password');
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', validatePasswordMatch);
    }
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
    showLoading('注册中...');
    
    // 提交表单
    submitRegistration(formData);
}

/**
 * 验证表单
 */
function validateForm(formData) {
    const firstName = formData.get('first_name');
    const lastName = formData.get('last_name');
    const username = formData.get('username');
    const email = formData.get('email');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirm_password');
    
    // 验证必填字段
    if (!firstName || !lastName || !username || !email || !password) {
        showError('请填写所有必填字段');
        return false;
    }
    
    // 验证邮箱格式
    if (!isValidEmail(email)) {
        showError('请输入有效的邮箱地址');
        return false;
    }
    
    // 验证用户名
    if (!isValidUsername(username)) {
        showError('用户名只能包含字母、数字和下划线，长度3-20个字符');
        return false;
    }
    
    // 验证密码强度
    if (passwordStrength < 2) {
        showError('密码强度不够，请使用更复杂的密码');
        return false;
    }
    
    // 验证密码匹配
    if (password !== confirmPassword) {
        showError('两次输入的密码不一致');
        return false;
    }
    
    // 验证服务条款
    const termsCheckbox = document.getElementById('terms');
    if (termsCheckbox && !termsCheckbox.checked) {
        showError('请同意服务条款和隐私政策');
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
    } else if (input.name === 'username') {
        if (value && isValidUsername(value)) {
            input.classList.add('is-valid');
        } else if (value) {
            input.classList.add('is-invalid');
        }
    } else if (input.name === 'password') {
        checkPasswordStrength(event);
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
 * 验证用户名格式
 */
function isValidUsername(username) {
    const usernameRegex = /^[a-zA-Z0-9_]{3,20}$/;
    return usernameRegex.test(username);
}

/**
 * 检查密码强度
 */
function checkPasswordStrength(event) {
    const password = event.target.value;
    const strengthIndicator = document.getElementById('password-strength');
    
    if (!strengthIndicator) {
        // 创建密码强度指示器
        const strengthDiv = document.createElement('div');
        strengthDiv.id = 'password-strength';
        strengthDiv.className = 'password-strength';
        event.target.parentNode.appendChild(strengthDiv);
    }
    
    const strength = calculatePasswordStrength(password);
    passwordStrength = strength;
    
    const strengthText = document.getElementById('password-strength');
    if (strengthText) {
        if (password.length === 0) {
            strengthText.textContent = '';
            strengthText.className = 'password-strength';
        } else if (strength === 0) {
            strengthText.textContent = '密码太弱';
            strengthText.className = 'password-strength strength-weak';
        } else if (strength === 1) {
            strengthText.textContent = '密码强度中等';
            strengthText.className = 'password-strength strength-medium';
        } else {
            strengthText.textContent = '密码强度良好';
            strengthText.className = 'password-strength strength-strong';
        }
    }
}

/**
 * 计算密码强度
 */
function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    return Math.min(2, Math.floor(strength / 2));
}

/**
 * 验证密码匹配
 */
function validatePasswordMatch(event) {
    const confirmPassword = event.target.value;
    const password = document.getElementById('password').value;
    
    const input = event.target;
    input.classList.remove('is-valid', 'is-invalid');
    
    if (confirmPassword && password === confirmPassword) {
        input.classList.add('is-valid');
    } else if (confirmPassword) {
        input.classList.add('is-invalid');
    }
}

/**
 * 提交注册
 */
async function submitRegistration(formData) {
    try {
        const response = await fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                first_name: formData.get('first_name'),
                last_name: formData.get('last_name'),
                username: formData.get('username'),
                email: formData.get('email'),
                password: formData.get('password'),
                company: formData.get('company')
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('注册成功！正在跳转到登录页面...');
            setTimeout(() => {
                window.location.href = '/auth/login';
            }, 2000);
        } else {
            throw new Error(result.error || '注册失败');
        }
    } catch (error) {
        console.error('注册失败:', error);
        showError('注册失败: ' + error.message);
    } finally {
        hideLoading();
    }
}

/**
 * 显示加载状态
 */
function showLoading(message) {
    const button = document.querySelector('.register-form button');
    if (button) {
        button.disabled = true;
        button.textContent = message;
    }
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    const button = document.querySelector('.register-form button');
    if (button) {
        button.disabled = false;
        button.textContent = '注册';
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
    showAlert(message, 'error');
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
    alertDiv.style.cssText = `
        padding: 12px;
        margin-bottom: 20px;
        border-radius: 6px;
        font-size: 14px;
        ${type === 'success' ? 'background: #d4edda; color: #155724; border: 1px solid #c3e6cb;' : ''}
        ${type === 'error' ? 'background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;' : ''}
    `;
    
    // 插入到表单前面
    const form = document.querySelector('.register-form form');
    if (form) {
        form.parentNode.insertBefore(alertDiv, form);
    }
    
    // 5秒后自动隐藏
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

/**
 * 初始化其他功能
 */
function initOtherFeatures() {
    // 自动聚焦到第一个输入框
    const firstInput = document.querySelector('.form-group input');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 100);
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
        const form = document.querySelector('.register-form form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
}
