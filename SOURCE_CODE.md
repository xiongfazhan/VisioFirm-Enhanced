# VisioFirm Enhanced - 源代码说明

## 📁 源代码结构

本项目基于原始 [VisioFirm](https://github.com/OschAI/VisioFirm) 项目，包含完整的源代码实现。

### 🧩 主要模块

#### 1. 核心应用 (`visiofirm/`)
- **`__init__.py`** - 包初始化
- **`config.py`** - 跨平台配置管理
- **`create_app.py`** - Flask应用工厂

#### 2. 数据模型 (`visiofirm/models/`)
- **`user.py`** - 用户认证和管理
- **`project.py`** - 项目数据模型
- **`training.py`** - 训练任务模型 [新增]

#### 3. 路由模块 (`visiofirm/routes/`)
- **`auth.py`** - 用户认证路由
- **`dashboard.py`** - 项目管理界面
- **`annotation.py`** - 标注功能核心
- **`training.py`** - 训练管理路由 [新增]

#### 4. 工具函数 (`visiofirm/utils/`)
- **`file_utils.py`** - 文件处理工具
- **`export_utils.py`** - 导出功能支持
- **`VFPreAnnotator.py`** - AI预标注引擎
- **`TrainingEngine.py`** - 模型训练引擎 [新增]
- **`GroundingDinoConfigs/`** - AI模型配置

#### 5. 前端资源 (`visiofirm/static/` & `visiofirm/templates/`)
- **JavaScript模块**: 标注核心、SAM集成、用户交互
- **HTML模板**: 响应式页面布局
- **CSS样式**: 现代化用户界面

## 🚀 核心增强功能

### 1. 训练模块集成
- **完整工作流**: 从数据准备到模型导出
- **可视化训练**: 实时进度监控和结果展示
- **参数配置**: 灵活的训练参数自定义

### 2. 性能优化
- **分块上传**: 大文件高效处理机制
- **多线程处理**: 并发任务管理
- **内存优化**: 智能资源管理

### 3. 中文本地化
- **界面翻译**: 全面中文用户界面
- **错误提示**: 中文错误信息和用户反馈
- **文档支持**: 中文帮助和说明文档

## 🛠️ 技术特点

### Flask架构设计
- **Blueprint模式**: 模块化路由管理
- **工厂模式**: 应用实例创建
- **中间件集成**: 用户认证和权限管理

### 前端技术栈
- **ES6模块**: 现代JavaScript架构
- **Web Workers**: 高性能AI处理
- **响应式设计**: 跨设备兼容

### AI模型集成
- **YOLOv10**: 快速目标检测
- **SAM2**: 精确实例分割
- **Grounding DINO**: 零样本检测

## 📋 安装和运行

### 快速开始
```bash
# 克隆项目
git clone https://github.com/xiongfazhan/VisioFirm-Enhanced.git
cd VisioFirm-Enhanced

# 安装依赖
pip install -e .

# 启动应用
visiofirm
```

### 开发模式
```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行调试模式
python run.py
```

## 🔗 与原项目的兼容性

### 数据兼容
- ✅ 完全兼容原项目数据格式
- ✅ 支持现有项目无缝迁移
- ✅ 保持API接口一致性

### 功能扩展
- ✅ 新增训练模块
- ✅ 增强性能优化
- ✅ 改进用户体验
- ✅ 完善错误处理

## 📚 更多信息

- **详细文档**: [README.md](README.md)
- **更新历史**: [CHANGELOG.md](CHANGELOG.md)
- **贡献指南**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **许可说明**: [ATTRIBUTION.md](ATTRIBUTION.md)

---

**注意**: 完整的源代码实现请参考本地项目文件。本文档仅提供结构概览。如需完整源码，请：
1. 克隆本仓库到本地
2. 查看 `visiofirm/` 目录下的所有源文件
3. 参考原项目了解基础架构