# VisioFirm-Enhanced 项目开发规范

## 🎯 核心开发原则

### 1. 前端代码标准化
- **HTML、CSS、JavaScript必须分离到不同文件**
- **禁止在HTML中内联CSS和JavaScript**
- **每个文件职责单一，便于维护和复用**

### 2. 前后端分离架构
- **后端提供RESTful API接口**
- **前端通过AJAX调用后端API**
- **数据交互使用JSON格式**
- **避免服务端渲染，采用客户端渲染**

## 📁 文件结构规范

### 前端文件组织
```
visiofirm/
├── static/
│   ├── css/           # 样式文件
│   │   ├── style.css     # 全局样式
│   │   ├── datasets.css  # 数据集页面样式
│   │   └── projects.css  # 项目页面样式
│   ├── js/            # JavaScript文件
│   │   ├── common.js     # 通用功能
│   │   ├── datasetManager.js  # 数据集管理
│   │   ├── datasetDownloader.js # 下载功能
│   │   └── datasets.js   # 数据集页面逻辑
│   └── images/        # 图片资源
└── templates/         # HTML模板
    ├── index.html     # 主页面
    ├── datasets.html  # 数据集页面
    └── projects.html  # 项目页面
```

### 后端文件组织
```
visiofirm/
├── routes/           # 路由文件
│   ├── dashboard.py  # 仪表板路由
│   ├── dataset.py    # 数据集API路由
│   └── project.py    # 项目API路由
├── models/           # 数据模型
├── utils/            # 工具类
└── config.py         # 配置文件
```

## 🔧 开发规范

### HTML规范
```html
<!-- ✅ 正确：引用外部CSS和JS -->
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/datasets.css') }}">
</head>
<body>
    <!-- HTML内容 -->
    <script src="{{ url_for('static', filename='js/datasets.js') }}"></script>
</body>
</html>

<!-- ❌ 错误：内联样式和脚本 -->
<style>
    .example { color: red; }
</style>
<script>
    function example() { }
</script>
```

### CSS规范
```css
/* ✅ 正确：模块化CSS */
.dataset-container {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.dataset-card {
    border: 1px solid #e1e1e1;
    border-radius: 8px;
    padding: 20px;
    transition: all 0.3s ease;
}

/* ❌ 错误：内联样式 */
<div style="color: red; font-size: 16px;">内容</div>
```

### JavaScript规范
```javascript
// ✅ 正确：模块化JavaScript
class DatasetManager {
    constructor() {
        this.apiBase = '/datasets/api';
    }
    
    async loadDatasets() {
        const response = await fetch(`${this.apiBase}/list`);
        return response.json();
    }
}

// ❌ 错误：内联事件处理
<button onclick="handleClick()">按钮</button>
```

## 🌐 API设计规范

### RESTful API设计
```python
# ✅ 正确：RESTful API设计
@bp.route('/datasets/api/list', methods=['GET'])
def list_datasets():
    """获取数据集列表"""
    return jsonify({
        'success': True,
        'data': datasets,
        'total': total_count
    })

@bp.route('/datasets/api/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """获取单个数据集详情"""
    return jsonify({
        'success': True,
        'data': dataset_info
    })

@bp.route('/datasets/api/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """删除数据集"""
    return jsonify({
        'success': True,
        'message': '删除成功'
    })
```

### 前端API调用
```javascript
// ✅ 正确：使用fetch API
async function loadDatasets() {
    try {
        const response = await fetch('/datasets/api/list');
        const result = await response.json();
        
        if (result.success) {
            displayDatasets(result.data);
        } else {
            showError(result.error);
        }
    } catch (error) {
        console.error('加载失败:', error);
        showError('网络错误');
    }
}

// ❌ 错误：服务端渲染
def render_datasets():
    datasets = get_datasets()
    return render_template('datasets.html', datasets=datasets)
```

## 📋 代码审查清单

### 前端代码审查
- [ ] HTML中没有内联`<style>`标签
- [ ] HTML中没有内联`<script>`标签
- [ ] CSS文件按功能模块分离
- [ ] JavaScript使用ES6+语法
- [ ] 事件处理使用addEventListener
- [ ] API调用使用async/await
- [ ] 错误处理完善

### 后端代码审查
- [ ] API返回JSON格式
- [ ] 使用RESTful设计原则
- [ ] 错误处理统一返回格式
- [ ] 避免在路由中直接渲染HTML
- [ ] 数据验证在API层进行
- [ ] 日志记录完善

## 🚀 最佳实践

### 1. 模块化开发
```javascript
// 按功能模块组织JavaScript
// datasetManager.js - 数据集管理
// datasetDownloader.js - 下载功能
// common.js - 通用工具
```

### 2. 响应式设计
```css
/* 移动端优先的响应式设计 */
.dataset-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 20px;
}

@media (min-width: 768px) {
    .dataset-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (min-width: 1200px) {
    .dataset-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}
```

### 3. 错误处理
```javascript
// 统一的错误处理
function handleApiError(error, context) {
    console.error(`${context}失败:`, error);
    
    const message = error.message || '操作失败，请重试';
    showNotification(message, 'error');
}

// API调用包装
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        handleApiError(error, 'API调用');
        throw error;
    }
}
```

## 📝 提交规范

### Git提交信息格式
```
feat: 添加数据集下载功能
fix: 修复菜单按钮无响应问题
style: 重构CSS文件分离
refactor: 重构JavaScript模块化
docs: 更新开发规范文档
```

### 分支命名规范
```
feature/dataset-download    # 新功能
bugfix/menu-button-fix     # 错误修复
refactor/css-separation    # 重构
hotfix/critical-bug       # 紧急修复
```

## 🔍 代码质量检查

### 自动化检查
```bash
# CSS检查
npm run lint:css

# JavaScript检查
npm run lint:js

# HTML检查
npm run lint:html
```

### 手动检查清单
- [ ] 代码格式统一
- [ ] 变量命名规范
- [ ] 函数职责单一
- [ ] 注释完整清晰
- [ ] 无重复代码
- [ ] 性能优化合理

---

**注意：所有新开发的页面和功能都必须遵循以上规范，现有代码在重构时也要逐步向规范靠拢。**
