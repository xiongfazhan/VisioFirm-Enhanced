![VisioFirm](https://github.com/OschAI/VisioFirm/blob/main/examples/visiofirm-logo.gif)

---

# 🇨🇳 中文文档 / Chinese Documentation

## VisioFirm 中文版: 快速近乎全自动的计算机视觉图像标注工具

> **🌟 这是 VisioFirm 的中文化和优化版本**  
> 基于原项目进行全面中文化，为中文用户提供更好的使用体验

## 📋 项目说明

本项目是对 [VisioFirm](https://github.com/OschAI/VisioFirm) 的中文化和二次开发版本，保持了原有的所有功能特性，同时针对中文用户进行了全面优化。

### 🔄 与原项目的关系
- **基于**: [OschAI/VisioFirm](https://github.com/OschAI/VisioFirm)
- **许可证**: Apache License 2.0（与原项目相同）
- **维护状态**: 积极维护和更新

## 🚀 中文化特性

### ✨ 全面中文化
- 🖥️ **完整的中文界面**: 所有按钮、菜单、对话框都已中文化
- 📝 **中文提示信息**: 错误消息、状态提示、帮助文本全部中文化
- 🎯 **本地化交互**: 符合中文用户使用习惯的界面设计
- 📚 **中文文档**: 完整的中文使用说明和API文档

### 🛠️ 优化改进
- 🎨 **界面优化**: 针对中文文本长度优化了布局
- 🔧 **功能增强**: 保持原有功能的同时提升用户体验
- 📱 **响应式设计**: 更好的移动端中文显示效果

---

## 📊 功能状态

### ✅ 已实现的功能

#### 🎨 核心标注功能
- ✅ **图像标注**: 支持手动和AI辅助标注
- ✅ **标注类型**: 
  - ✅ 轴对齐边界框 (Axis-aligned Bounding Boxes)
  - ✅ 定向边界框 (Oriented Bounding Boxes)
  - ✅ 多边形分割 (Polygon Segmentation)
- ✅ **AI预标注**:
  - ✅ YOLOv10 目标检测
  - ✅ SAM2 图像分割
  - ✅ Grounding DINO 零样本检测
- ✅ **交互式编辑**: 画布编辑、撤销/重做、缩放功能
- ✅ **快捷键支持**: 完整的键盘快捷键系统

#### 📦 项目管理
- ✅ **项目创建和管理**: 创建、编辑、删除项目
- ✅ **多项目管理**: 支持多个项目同时存在
- ✅ **分类管理**: 支持自定义多个类别
- ✅ **图像管理**: 批量上传、导入、删除图像
- ✅ **数据导出**: 
  - ✅ YOLO格式 (.txt)
  - ✅ COCO格式 (.json)
  - ✅ 带掩码的图像导出

#### 🤖 训练模块
- ✅ **模型训练**: 完整的YOLO模型训练工作流
- ✅ **训练配置**: 自定义训练参数（epochs, batch size等）
- ✅ **训练监控**: 实时训练进度和指标可视化
- ✅ **训练历史**: 保存和管理训练任务历史
- ✅ **模型导出**: 训练完成后导出模型文件

#### 📊 数据集管理
- ✅ **数据集CRUD**: 创建、读取、更新、删除数据集
- ✅ **数据集分析**: 数据集统计信息和分析
- ✅ **数据集下载**: 从URL下载公开数据集
- ✅ **数据集导入**: 从本地文件导入数据集
- ✅ **数据集关联**: 将数据集关联到项目

#### 👤 用户系统
- ✅ **用户注册和登录**: 完整的用户认证系统
- ✅ **用户资料管理**: 编辑用户信息
- ✅ **密码重置**: 密码找回功能
- ✅ **会话管理**: Flask-Login会话管理

#### 🎯 增强功能
- ✅ **完整中文化**: 界面、提示、文档全面中文化
- ✅ **代码规范**: CSS/JS文件分离，前后端分离架构
- ✅ **API优化**: RESTful API设计，JSON响应格式
- ✅ **性能优化**: 多线程上传、内存优化、缓存机制
- ✅ **错误处理**: 完善的错误处理和日志系统

---

### ❌ 缺失的功能

#### 🎬 高级标注
- ❌ **视频标注**: 视频帧标注和时间序列标注
- ❌ **分类任务**: 图像分类标签（仅支持检测和分割）
- ❌ **关键点标注**: 人体姿态、关键点检测标注
- ❌ **3D标注**: 3D目标检测和分割标注

#### 👥 协作功能
- ❌ **多用户协作**: 团队协作和任务分配
- ❌ **权限管理**: 角色权限和访问控制
- ❌ **标注审核**: 标注质量审核工作流
- ❌ **评论系统**: 标注讨论和反馈

#### 🔌 集成和扩展
- ❌ **更多ML框架**: mmdetection、detectron2集成
- ❌ **自定义模型**: 用户自定义AI模型集成
- ❌ **插件系统**: 可扩展的插件架构
- ❌ **API认证**: Token-based API认证

#### 📱 平台支持
- ❌ **移动端APP**: iOS/Android原生应用
- ❌ **云端部署**: Docker容器化部署方案
- ❌ **Web实时协作**: WebSocket实时同步

#### 📈 高级功能
- ❌ **自动化流水线**: CI/CD集成
- ❌ **批量处理**: 批量标注和处理工具
- ❌ **数据增强预览**: 训练前数据增强效果预览
- ❌ **模型版本管理**: 模型版本控制和回滚

---

### 🚧 计划中的功能

#### 短期计划 (v1.1.0)
- 🚧 **视频标注支持**: 视频帧标注和时间序列标注
- 🚧 **多用户协作**: 团队协作和任务分配
- 🚧 **分类任务支持**: 图像分类标注功能
- 🚧 **云端部署方案**: Docker和云平台部署指南

#### 中期计划 (v1.2.0)
- 🚧 **更多ML框架**: mmdetection、detectron2集成
- 🚧 **API认证**: Token-based API认证系统
- 🚧 **移动端适配**: 响应式设计优化和移动端支持
- 🚧 **插件系统**: 可扩展的插件架构

#### 长期计划 (v2.0.0)
- 🚧 **Web实时协作**: WebSocket实时同步
- 🚧 **自定义模型集成**: 用户自定义AI模型支持
- 🚧 **企业级功能**: 权限管理、审计日志、数据备份
- 🚧 **自动化流水线**: CI/CD集成和自动化工具

---

### 📋 功能完整性评估

| 功能模块 | 完成度 | 状态 |
|---------|--------|------|
| 核心标注功能 | 95% | ✅ 基本完成 |
| 项目管理 | 100% | ✅ 完整 |
| 训练模块 | 90% | ✅ 可用 |
| 数据集管理 | 85% | ✅ 基本完成 |
| 用户系统 | 90% | ✅ 基本完成 |
| 视频标注 | 0% | ❌ 未开始 |
| 多用户协作 | 0% | ❌ 未开始 |
| 分类任务 | 0% | ❌ 未开始 |
| 云端部署 | 0% | ❌ 未开始 |

**总体完成度**: 约 **75%** - 核心功能完整，高级功能待开发

---

### 💡 贡献建议

欢迎贡献以下功能：
- 🎯 高优先级: 视频标注、多用户协作
- 📊 中优先级: 分类任务、更多ML框架集成
- 🔧 低优先级: 插件系统、移动端APP

详见 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与贡献。

---

## 📁 项目结构

```
VisioFirm/
├── README.md                 # 项目主要说明
├── CHANGELOG.md              # 更新日志
├── LICENSE                   # 许可证文件
├── setup.py                  # 安装配置
├── requirements.txt          # 依赖包列表
├── run.py                    # 启动脚本
├── visiofirm/               # 主要源代码
│   ├── models/              # 数据模型
│   ├── routes/              # 路由模块
│   ├── static/              # 静态资源
│   ├── templates/           # HTML模板
│   └── utils/               # 工具函数
├── tests/                   # 测试文件
├── docs/                    # 项目文档
├── examples/                # 示例文件
└── scripts/                 # 脚本工具
```

---

## 安装 / Installation

VisioFirm 可以通过 pip 从 GitHub 安装（PyPI 即将推出！）

需要 `Python 3.10+`。

```bash
pip install -U visiofirm
```

开发环境安装（从克隆的仓库）：

```bash
git clone https://github.com/xiongfazhan/VisioFirm-Enhanced.git
cd VisioFirm-Enhanced
pip install -e .
```

## 快速开始 / Quick Start

使用单个命令启动 VisioFirm—它会自动启动本地 Web 服务器并在浏览器中打开。

```bash
visiofirm
```

1. 创建新项目并上传图像
2. 定义类别（例如 "car", "person"）
3. 对于易于检测的对象运行 AI 预标注（选择模型：YOLO、Grounding DINO）
4. 在交互式编辑器中完善标签
5. 导出标注的数据集

VisioFirm 应用使用缓存目录在本地存储设置。

---

# 🇺🇸 English Documentation

---

# VisioFirm: Fast Almost fully-Automated Image Annotation for Computer Vision

[![GitHub Stars](https://img.shields.io/github/stars/OschAI/VisioFirm?style=social)](https://github.com/OschAI/VisioFirm/stargazers)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/OschAI/VisioFirm/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/visiofirm.svg)](https://pypi.org/project/visiofirm/) 
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

-------
> [!IMPORTANT]
> A new release has just dropped. `VisioFirm 0.2.0` brings enhancements including bug fixes for image import, improved frontend loading, Cloud/SSH support for downloading images and saving annotations, SAM2 worker offloading for better performance, optimized SAM2-Auto annotation for faster computing, and thread optimizations for image uploading. This version builds on the stable GroundingDINO dependency from 0.1.4.
> - **Cloud/SSH Integration**: download images from cloud storage or SSH servers and save annotations remotely (using local absolute paths).
> - **Enhanced Image Handling**: Fixed bugs in image import, faster frontend loading, and multi-threaded uploading for efficiency.
> - **SAM2 Optimizations**: Worker-based offloading and improved auto-annotation for rapid, high-performance segmentation in the browser. Though you may experience a first timelaps for the first label generation the subsequent annotators are instant.

> [!NOTE]
> If you prefer the HF transformers-based library (pre-0.2.0), install from the main branch via `pip install visiofirm==0.1.0`.
-------


**VisioFirm** is an open-source, AI-powered image annotation tool designed to accelerate labeling for computer vision tasks like object detection, oriented bounding boxes (OBB), and segmentation. Built for speed and simplicity, it leverages state-of-the-art models for semi-automated pre-annotations, allowing you to focus on refining rather than starting from scratch. Whether you're preparing datasets for YOLO, SAM, or custom models, VisioFirm streamlines your workflow with a intuitive web interface and powerful backend.

Perfect for researchers, data scientists, and ML engineers handling large image datasets—get high-quality annotations in minutes, not hours!

## Why VisioFirm?

Unlike other annotation tool, this one is majoraly focused on CV tasks annotation detection (normal and oriented bounding box) and segmentation.

- **AI-Driven Pre-Annotation**: Automatically detect and segment objects using YOLOv10, SAM2, and Grounding DINO—saving up to 80% of manual effort.
- **Multi-Task Support**: Handles bounding boxes, oriented bounding boxes, and polygon segmentation in one tool.
- **array-Based Editing**: Interactive canvas for precise adjustments, with real-time SAM-powered segmentation in the browser.
- **Offline-Friendly**: Models download automatically (or pre-fetch for offline use), with SQLite backend for local projects.
- **Extensible & Open-Source**: Customize with your own ultralytics models or integrate into pipelines—contributions welcome!
- **SAM2-base webgpu**: Insta-drawing of annotations via SAM2 with worker offloading and auto-annotation for faster computing!

![Annotation Editing Demo](https://github.com/OschAI/VisioFirm/blob/main/examples/orange-apples-test.gif)

## Features

- **Semi-Automated Labeling**: Kickstart annotations with AI models like YOLO for detection, SAM for segmentation, and Grounding DINO for zero-shot object grounding.
- **Flexible Annotation Types**:
  - Axis-aligned bounding boxes for standard detection.
  - Oriented bounding boxes for rotated objects (e.g., aerial imagery).
  - Polygon segmentation for precise boundaries.
- **Interactive Frontend**: Draw, edit, and refine labels on a responsive canvas. Click-to-segment with browser-based SAM for instant masks.
- **Project Management**: Create, manage, and export projects with SQLite database storage. Support for multiple classes and images.
- **Export Formats**: Seamless exports to YOLO, COCO, or custom formats for training.
- **Performance Optimizations**: Cluster overlapping detections, simplify contours, and filter by confidence for clean datasets.
- **Cloud/SSH Integration**: Seamlessly download images from cloud storage or SSH servers and save annotations remotely.
- **Enhanced Image Handling**: Fixed bugs in image import, faster frontend loading, and multi-threaded uploading for efficiency.
- **SAM2 Optimizations**: Worker-based offloading and improved auto-annotation for rapid, high-performance segmentation in the browser.
- **Cross-Platform**: Runs locally on Linux, macOS, or Windows via Python— no cloud dependency.

![Annotation Editing Demo](https://github.com/OschAI/VisioFirm/blob/main/examples/AIpreannotator-demo.gif)

---

## Feature Status

### ✅ Implemented Features

#### 🎨 Core Annotation
- ✅ **Image Annotation**: Manual and AI-assisted annotation
- ✅ **Annotation Types**: 
  - ✅ Axis-aligned Bounding Boxes
  - ✅ Oriented Bounding Boxes
  - ✅ Polygon Segmentation
- ✅ **AI Pre-annotation**:
  - ✅ YOLOv10 Object Detection
  - ✅ SAM2 Image Segmentation
  - ✅ Grounding DINO Zero-shot Detection
- ✅ **Interactive Editing**: Canvas editing, undo/redo, zoom functionality
- ✅ **Keyboard Shortcuts**: Complete keyboard shortcut system

#### 📦 Project Management
- ✅ **Project CRUD**: Create, edit, delete projects
- ✅ **Multi-project Support**: Multiple projects simultaneously
- ✅ **Class Management**: Custom multiple classes
- ✅ **Image Management**: Batch upload, import, delete images
- ✅ **Data Export**: 
  - ✅ YOLO format (.txt)
  - ✅ COCO format (.json)
  - ✅ Images with masks export

#### 🤖 Training Module
- ✅ **Model Training**: Complete YOLO model training workflow
- ✅ **Training Configuration**: Custom training parameters (epochs, batch size, etc.)
- ✅ **Training Monitoring**: Real-time training progress and metrics visualization
- ✅ **Training History**: Save and manage training task history
- ✅ **Model Export**: Export model files after training completion

#### 📊 Dataset Management
- ✅ **Dataset CRUD**: Create, read, update, delete datasets
- ✅ **Dataset Analysis**: Dataset statistics and analysis
- ✅ **Dataset Download**: Download public datasets from URLs
- ✅ **Dataset Import**: Import datasets from local files
- ✅ **Dataset Linking**: Link datasets to projects

#### 👤 User System
- ✅ **User Registration & Login**: Complete user authentication system
- ✅ **User Profile Management**: Edit user information
- ✅ **Password Reset**: Password recovery functionality
- ✅ **Session Management**: Flask-Login session management

#### 🎯 Enhanced Features
- ✅ **Full Chinese Localization**: Interface, prompts, documentation fully localized
- ✅ **Code Standards**: CSS/JS file separation, frontend-backend separation architecture
- ✅ **API Optimization**: RESTful API design, JSON response format
- ✅ **Performance Optimization**: Multi-threaded upload, memory optimization, caching mechanism
- ✅ **Error Handling**: Comprehensive error handling and logging system

---

### ❌ Missing Features

#### 🎬 Advanced Annotation
- ❌ **Video Annotation**: Video frame annotation and time-series annotation
- ❌ **Classification Tasks**: Image classification labels (only detection and segmentation supported)
- ❌ **Keypoint Annotation**: Human pose, keypoint detection annotation
- ❌ **3D Annotation**: 3D object detection and segmentation annotation

#### 👥 Collaboration Features
- ❌ **Multi-user Collaboration**: Team collaboration and task assignment
- ❌ **Permission Management**: Role permissions and access control
- ❌ **Annotation Review**: Annotation quality review workflow
- ❌ **Comment System**: Annotation discussion and feedback

#### 🔌 Integration & Extension
- ❌ **More ML Frameworks**: mmdetection, detectron2 integration
- ❌ **Custom Models**: User-defined AI model integration
- ❌ **Plugin System**: Extensible plugin architecture
- ❌ **API Authentication**: Token-based API authentication

#### 📱 Platform Support
- ❌ **Mobile Apps**: iOS/Android native applications
- ❌ **Cloud Deployment**: Docker containerization deployment solution
- ❌ **Web Real-time Collaboration**: WebSocket real-time synchronization

#### 📈 Advanced Features
- ❌ **Automation Pipeline**: CI/CD integration
- ❌ **Batch Processing**: Batch annotation and processing tools
- ❌ **Data Augmentation Preview**: Data augmentation effect preview before training
- ❌ **Model Version Management**: Model version control and rollback

---

### 🚧 Planned Features

#### Short-term (v1.1.0)
- 🚧 **Video Annotation Support**: Video frame annotation and time-series annotation
- 🚧 **Multi-user Collaboration**: Team collaboration and task assignment
- 🚧 **Classification Task Support**: Image classification annotation functionality
- 🚧 **Cloud Deployment Solutions**: Docker and cloud platform deployment guides

#### Mid-term (v1.2.0)
- 🚧 **More ML Frameworks**: mmdetection, detectron2 integration
- 🚧 **API Authentication**: Token-based API authentication system
- 🚧 **Mobile Adaptation**: Responsive design optimization and mobile support
- 🚧 **Plugin System**: Extensible plugin architecture

#### Long-term (v2.0.0)
- 🚧 **Web Real-time Collaboration**: WebSocket real-time synchronization
- 🚧 **Custom Model Integration**: User-defined AI model support
- 🚧 **Enterprise Features**: Permission management, audit logs, data backup
- 🚧 **Automation Pipeline**: CI/CD integration and automation tools

---

### 📋 Feature Completeness Assessment

| Feature Module | Completion | Status |
|---------------|------------|--------|
| Core Annotation | 95% | ✅ Mostly Complete |
| Project Management | 100% | ✅ Complete |
| Training Module | 90% | ✅ Usable |
| Dataset Management | 85% | ✅ Mostly Complete |
| User System | 90% | ✅ Mostly Complete |
| Video Annotation | 0% | ❌ Not Started |
| Multi-user Collaboration | 0% | ❌ Not Started |
| Classification Tasks | 0% | ❌ Not Started |
| Cloud Deployment | 0% | ❌ Not Started |

**Overall Completion**: Approximately **75%** - Core features complete, advanced features pending

---

### 💡 Contribution Suggestions

Contributions are welcome for the following features:
- 🎯 High Priority: Video annotation, multi-user collaboration
- 📊 Medium Priority: Classification tasks, more ML framework integration
- 🔧 Low Priority: Plugin system, mobile apps

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

---

## Installation

VisioFirm is easy to install via pip from GitHub (PyPI coming soon!).

It was tested with `Python 3.10+`.

```bash
pip install -U visiofirm
```

For development or editable install (from a cloned repo):

```bash
git clone https://github.com/OschAI/VisioFirm.git
cd VisioFirm
pip install -e .
```

## Quick Start

Launch VisioFirm with a single command—it auto-starts a local web server and opens in your browser.

```bash
visiofirm
```

1. Create a new project and upload images.
2. Define classes (e.g., "car", "person").
3. For easy-to-detect object run AI pre-annotation (select model: YOLO, Grounding DINO).
4. Refine labels in the interactive editor.
5. Export your annotated dataset.

The VisioFirm app uses cache directories to store settings locally.

## Usage

### Pre-Annotation with AI

VisioFirm uses advanced models for initial labels:

- **YOLOv10**: Fast detection.
- **SAM2**: Precise segmentation.
- **Grounding DINO**: Zero-shot detection via text prompts.

Models auto-download on first run (stored in current dir or cache). For offline prep:

### Frontend Customization

The web interface (Flask + JS) supports hotkeys, undo/redo, and zoom. Edit `static/js/sam.js` for browser SAM tweaks.

### Exporting Data

From the dashboard, export to JSON, TXT (YOLO format), or images with masks.

## Community & Support

- **Issues**: Report bugs or request features [here](https://github.com/OschAI/VisioFirm/issues).
- **Discord**: Coming soon—star the repo for updates!
- **Roadmap**: Multi-user support, video annotation, custom model integration.

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

---

Built by [Safouane El Ghazouali](https://github.com/safouaneelg) for the research community. Star the repo if it helps your workflow! 🚀

## Citation

```
@misc{ghazouali2025visiofirm,
    title={VisioFirm: Cross-Platform AI-assisted Annotation Tool for Computer Vision},
    author={Safouane El Ghazouali and Umberto Michelucci},
    year={2025},
    eprint={2509.04180},
    archivePrefix={arXiv},
    primaryClass={cs.CV}
}
```

## TODOs

**SOON**:

- Documentation website
- Discord community
- Paper - detailing the implementation and AI preannotation pipeline
- Classification

**Futur**:

- Support for video annotation
- Support for more ML frameworks (such as mmdetection and detectron2)

