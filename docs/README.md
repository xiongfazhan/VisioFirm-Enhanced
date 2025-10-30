# VisioFirm-Enhanced 文档中心

## 📚 文档索引

### 🎯 开发规范
- **[开发规范文档 (DEVELOPMENT_RULES.md)](../DEVELOPMENT_RULES.md)** ⭐推荐首读  
  项目的核心开发规范，包括前端代码标准化、前后端分离原则等

- **[代码规范使用指南 (CODE_STANDARDS_README.md)](../CODE_STANDARDS_README.md)**  
  如何使用代码规范检查工具，包括Git hooks设置

### 🔧 API优化
- **[后端API优化总结 (BACKEND_API_OPTIMIZATION_SUMMARY.md)](./BACKEND_API_OPTIMIZATION_SUMMARY.md)** ⭐必读  
  后端API优化的完整总结报告，包括优化内容、效果和后续建议

- **[API优化指南 (API_OPTIMIZATION_GUIDE.md)](./API_OPTIMIZATION_GUIDE.md)** ⭐实用指南  
  详细的API优化实施指南，包含代码示例、最佳实践和迁移步骤

### 📖 快速开始

#### 1. 新开发者入职
```bash
# 1. 阅读开发规范
cat DEVELOPMENT_RULES.md

# 2. 安装代码检查钩子
bash scripts/install-hooks.sh

# 3. 运行代码规范检查
python3 scripts/check_code_standards.py
```

#### 2. 开发新API端点
```python
# 参考 API_OPTIMIZATION_GUIDE.md 中的模板
from visiofirm.utils.api_helpers import APIResponse, APIError, handle_api_errors

@bp.route('/api/my_endpoint', methods=['POST'])
@login_required
@handle_api_errors
def my_endpoint():
    """端点说明"""
    # 使用标准化响应
    return APIResponse.success(data=result)
```

#### 3. 提交代码前检查
```bash
# 自动运行（如果已安装Git hooks）
git commit -m "your message"

# 手动运行
python3 scripts/check_code_standards.py
```

## 🗂️ 文档结构

```
docs/
├── README.md                              # 本文件 - 文档索引
├── BACKEND_API_OPTIMIZATION_SUMMARY.md    # API优化总结报告
└── API_OPTIMIZATION_GUIDE.md              # API优化实施指南

根目录/
├── DEVELOPMENT_RULES.md                   # 开发规范（主要）
├── CODE_STANDARDS_README.md               # 代码规范工具使用指南
└── .cursorrules                           # Cursor编辑器规则配置
```

## 📋 常见任务索引

### 任务：创建新页面
1. 阅读 [DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md) 中的"文件结构规范"
2. 创建 HTML 模板（使用 `{% block styles %}` 和 `{% block scripts %}`）
3. 创建独立的 CSS 文件
4. 创建独立的 JS 文件（使用 `addEventListener`）
5. 运行 `python3 scripts/check_code_standards.py` 检查

### 任务：优化现有API
1. 阅读 [API_OPTIMIZATION_GUIDE.md](./API_OPTIMIZATION_GUIDE.md) 中的"迁移现有API的步骤"
2. 添加 `@handle_api_errors` 装饰器
3. 使用 `APIResponse` 和 `APIError`
4. 添加详细的文档注释
5. 测试API功能

### 任务：修复代码规范问题
1. 运行 `python3 scripts/check_code_standards.py` 查看问题
2. 根据错误提示修复：
   - ❌ 内联样式 → 移到独立CSS文件
   - ❌ 内联脚本 → 移到独立JS文件
   - ⚠️ onclick事件 → 使用addEventListener
3. 重新运行检查确认修复

### 任务：添加新功能
1. 遵循[DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md)中的规范
2. HTML/CSS/JS 分离
3. 后端使用标准化API响应（参考 [API_OPTIMIZATION_GUIDE.md](./API_OPTIMIZATION_GUIDE.md)）
4. 添加文档注释
5. 提交前运行代码检查

## 🔍 关键概念

### 1. HTML/CSS/JS 分离
- ❌ 禁止在HTML中内联`<style>`和`<script>`标签
- ✅ 使用外部文件引用
- ✅ 通过`{% block styles %}`和`{% block scripts %}`注入

### 2. 事件处理现代化
- ❌ 禁止使用内联`onclick`等事件属性
- ✅ 使用`addEventListener`在JS文件中绑定

### 3. API响应标准化
- ✅ 使用`APIResponse.success()`返回成功
- ✅ 使用`APIError`抛出错误
- ✅ 使用`@handle_api_errors`自动处理异常

### 4. render_template的合理使用
- ✅ 页面首次加载使用render_template（合理且必要）
- ✅ 数据交互使用JSON API
- ℹ️ 这是混合架构，不是完全前后端分离

## 🛠️ 工具使用

### 代码规范检查器
```bash
# 检查所有文件
python3 scripts/check_code_standards.py

# 查看详细输出
python3 scripts/check_code_standards.py --verbose
```

**输出说明**:
- `❌ 错误` - 必须修复
- `⚠️ 警告` - 建议优化
- `✅ 成功` - 符合规范

### Git Hooks
```bash
# 安装（首次）
bash scripts/install-hooks.sh

# 效果：每次commit前自动检查
git commit -m "your message"  # 自动运行检查
```

## 📞 需要帮助？

- **开发规范问题**: 查看 [DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md)
- **API优化问题**: 查看 [API_OPTIMIZATION_GUIDE.md](./API_OPTIMIZATION_GUIDE.md)
- **代码检查问题**: 查看 [CODE_STANDARDS_README.md](../CODE_STANDARDS_README.md)
- **其他问题**: 联系项目维护者

## 🔄 文档更新

- **最后更新**: 2025-10-13
- **文档版本**: v1.0
- **维护者**: 开发团队

---

💡 **提示**: 建议新团队成员按顺序阅读以下文档：
1. [DEVELOPMENT_RULES.md](../DEVELOPMENT_RULES.md) - 了解项目规范
2. [API_OPTIMIZATION_GUIDE.md](./API_OPTIMIZATION_GUIDE.md) - 学习API开发
3. [CODE_STANDARDS_README.md](../CODE_STANDARDS_README.md) - 掌握检查工具

