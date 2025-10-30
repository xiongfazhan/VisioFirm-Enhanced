# VisioFirm-Enhanced 代码规范指南

## 🎯 项目开发规范已建立

本项目已建立严格的代码规范，确保代码质量和可维护性。

## 📋 核心规范

### 1. 前端代码标准化
- ✅ **HTML、CSS、JavaScript必须分离到不同文件**
- ✅ **禁止在HTML中内联CSS和JavaScript**
- ✅ **每个文件职责单一，便于维护和复用**

### 2. 前后端分离架构
- ✅ **后端提供RESTful API接口**
- ✅ **前端通过AJAX调用后端API**
- ✅ **数据交互使用JSON格式**
- ✅ **避免服务端渲染，采用客户端渲染**

## 🔧 如何使用规范检查

### 手动检查代码规范
```bash
# 运行代码规范检查脚本
python3 scripts/check_code_standards.py
```

### 自动检查（Git钩子）
代码提交时会自动运行规范检查：
```bash
git add .
git commit -m "feat: 添加新功能"
# 自动运行规范检查，如有违规会阻止提交
```

## 📊 当前项目状态

根据最新的规范检查，发现以下问题需要修复：

### ❌ 严重问题（必须修复）
1. **13个HTML文件包含内联样式和脚本**
   - `login.html` - 内联样式
   - `index.html` - 内联样式和脚本
   - `datasets.html` - 内联脚本
   - `training.html` - 内联样式和脚本
   - `reset.html` - 内联样式
   - `labeler_base.html` - 内联样式和脚本
   - `register.html` - 内联样式
   - `annotation.html` - 内联样式和脚本
   - `profile.html` - 内联样式

### ⚠️ 警告问题（建议修复）
1. **多个HTML文件缺少外部CSS/JS引用**
2. **发现内联onclick事件，建议使用addEventListener**
3. **后端路由中发现render_template调用，建议使用API返回JSON**

## 🚀 修复计划

### 阶段1：修复HTML文件（高优先级）
- [ ] 将内联样式提取到CSS文件
- [ ] 将内联脚本提取到JS文件
- [ ] 添加外部CSS和JS文件引用
- [ ] 将onclick事件改为addEventListener

### 阶段2：优化后端API（中优先级）
- [ ] 减少render_template使用
- [ ] 增加JSON API接口
- [ ] 完善错误处理

### 阶段3：完善文件结构（低优先级）
- [ ] 创建缺失的CSS文件
- [ ] 创建缺失的JS文件
- [ ] 优化文件组织结构

## 📁 推荐的文件结构

```
visiofirm/
├── static/
│   ├── css/
│   │   ├── style.css          # 全局样式
│   │   ├── login.css          # 登录页面样式
│   │   ├── dashboard.css       # 仪表板样式
│   │   ├── datasets.css       # 数据集页面样式
│   │   ├── training.css       # 训练页面样式
│   │   ├── annotation.css     # 标注页面样式
│   │   └── profile.css        # 个人资料页面样式
│   ├── js/
│   │   ├── common.js          # 通用功能
│   │   ├── login.js           # 登录页面逻辑
│   │   ├── dashboard.js       # 仪表板逻辑
│   │   ├── datasets.js        # 数据集页面逻辑
│   │   ├── training.js        # 训练页面逻辑
│   │   ├── annotation.js      # 标注页面逻辑
│   │   └── profile.js         # 个人资料页面逻辑
│   └── images/
└── templates/
    ├── login.html
    ├── index.html
    ├── datasets.html
    ├── training.html
    ├── annotation.html
    └── profile.html
```

## 🔍 代码审查清单

### 提交前检查
- [ ] 运行 `python3 scripts/check_code_standards.py`
- [ ] 确保没有错误（❌）
- [ ] 尽量减少警告（⚠️）
- [ ] 代码格式统一
- [ ] 变量命名规范

### 代码质量检查
- [ ] HTML中没有内联`<style>`标签
- [ ] HTML中没有内联`<script>`标签
- [ ] CSS文件按功能模块分离
- [ ] JavaScript使用ES6+语法
- [ ] 事件处理使用addEventListener
- [ ] API调用使用async/await
- [ ] 错误处理完善

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

## 🎉 成功案例

### 已符合规范的文件
- ✅ `visiofirm/templates/datasets.html` - 已重构为分离结构
- ✅ `visiofirm/static/css/datasets.css` - 独立的样式文件
- ✅ `visiofirm/static/js/datasets.js` - 独立的逻辑文件
- ✅ `visiofirm/static/js/datasetDownloader.js` - 模块化JavaScript

## 🚨 重要提醒

1. **所有新开发的页面和功能都必须遵循规范**
2. **现有代码在重构时也要逐步向规范靠拢**
3. **代码审查时必须检查是否违反规范**
4. **违反规范的代码不允许合并到主分支**

## 📞 获取帮助

如果对规范有疑问，请：
1. 查看 `DEVELOPMENT_RULES.md` 详细规范
2. 运行 `python3 scripts/check_code_standards.py` 检查问题
3. 参考已重构的文件作为示例
4. 联系项目维护者获取帮助

---

**记住：规范的目的是提高代码质量，让项目更易维护，让团队协作更高效！** 🚀
