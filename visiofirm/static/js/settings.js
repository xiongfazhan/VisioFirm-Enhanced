/**
 * 设置页面逻辑
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('设置页面已加载');
    
    // 添加复制API密钥功能（如果需要）
    const apiKeyElement = document.querySelector('p strong');
    if (apiKeyElement && apiKeyElement.textContent.includes('API密钥')) {
        const apiKeyValue = apiKeyElement.parentElement.textContent.split('：')[1]?.trim();
        
        if (apiKeyValue) {
            // 创建复制按钮
            const copyButton = document.createElement('button');
            copyButton.textContent = '复制';
            copyButton.className = 'btn btn-sm btn-secondary ml-2';
            copyButton.style.marginLeft = '10px';
            
            copyButton.addEventListener('click', function() {
                navigator.clipboard.writeText(apiKeyValue).then(() => {
                    const originalText = copyButton.textContent;
                    copyButton.textContent = '已复制!';
                    setTimeout(() => {
                        copyButton.textContent = originalText;
                    }, 2000);
                }).catch(err => {
                    console.error('复制失败:', err);
                    alert('复制失败，请手动复制');
                });
            });
            
            apiKeyElement.parentElement.appendChild(copyButton);
        }
    }
    
    // 生成新密钥确认
    const generateKeyForm = document.querySelector('form[action*="generate_api_key"]');
    if (generateKeyForm) {
        generateKeyForm.addEventListener('submit', function(e) {
            if (!confirm('确定要生成新的API密钥吗？旧密钥将失效。')) {
                e.preventDefault();
            }
        });
    }
});

