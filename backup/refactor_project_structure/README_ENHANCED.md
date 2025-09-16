# VisioFirm Enhanced - AI驱动的图像标注工具增强版

[![GitHub Stars](https://img.shields.io/github/stars/xiongfazhan/VisioFirm-Enhanced?style=social)](https://github.com/xiongfazhan/VisioFirm-Enhanced/stargazers)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/xiongfazhan/VisioFirm-Enhanced/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

## 📌 项目说明

本项目是基于 [OschAI/VisioFirm](https://github.com/OschAI/VisioFirm) 的二次开发增强版本，在原项目的基础上进行了功能扩展和优化改进。

### 🔗 源项目信息
- **原项目**: [VisioFirm by OschAI](https://github.com/OschAI/VisioFirm)
- **原作者**: Safouane El Ghazouali
- **许可证**: Apache 2.0 License
- **基础版本**: v0.2.0

## 🚀 增强特性

### ✨ 新增功能
- **训练模块增强**: 新增完整的模型训练流程管理
- **中文本地化**: 全面中文界面优化，提升中文用户体验
- **性能优化**: 
  - 多线程上传优化
  - SAM2 Worker性能增强
  - 内存管理改进
- **用户体验改进**:
  - 更直观的项目管理界面
  - 增强的快捷键支持
  - 改进的标注工具

### 🔧 技术改进
- **架构优化**: 更清晰的模块化设计
- **代码质量**: 增强的错误处理和日志记录
- **兼容性**: 更好的跨平台支持
- **扩展性**: 更易于集成自定义AI模型

## 📖 项目概述

**VisioFirm Enhanced** 是一个开源的、AI驱动的图像标注工具，专门用于加速计算机视觉任务的标注工作，包括目标检测、有向边界框（OBB）和图像分割。

### 🎯 核心价值
- **效率提升**: 通过AI预标注节省高达80%的手动标注时间
- **多任务支持**: 支持边界框、有向边界框和多边形分割
- **智能辅助**: 集成YOLOv10、SAM2、Grounding DINO等先进AI模型
- **易于使用**: 直观的Web界面，支持热键操作

## 🛠️ 技术架构

### 后端技术栈
- **框架**: Flask (Python 3.10+)
- **数据库**: SQLite
- **AI集成**: YOLOv10, SAM2, Grounding DINO
- **用户认证**: Flask-Login
- **Web服务器**: Waitress

### 前端技术栈
- **核心**: 原生JavaScript + HTML + CSS
- **模块化**: ES6模块系统
- **优化**: Web Worker + 分块上传

## 📦 安装与使用

### 环境要求
- Python 3.10+
- pip
- 支持的操作系统: Linux, macOS, Windows

### 快速开始

```bash
# 克隆仓库
git clone https://github.com/xiongfazhan/VisioFirm-Enhanced.git
cd VisioFirm-Enhanced

# 安装依赖
pip install -e .

# 启动应用
visiofirm
```

### 开发环境安装

```bash
# 开发模式安装
pip install -e .

# 安装开发依赖
pip install -r requirements.txt
```

## 🔄 与源项目的差异

### 主要改进
1. **模型训练模块**: 新增完整的训练工作流
2. **中文优化**: 界面和文档全面中文化
3. **性能增强**: 优化的文件上传和处理机制
4. **用户体验**: 改进的交互设计和错误处理

### 保持兼容
- 完全兼容原项目的数据格式
- 支持原有的导出格式 (YOLO, COCO, Pascal VOC, CSV)
- 保持相同的API接口设计

## 🤝 贡献指南

欢迎贡献代码和建议！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- 感谢 [OschAI](https://github.com/OschAI) 创建了优秀的原版 VisioFirm 项目
- 感谢开源社区提供的各种AI模型和工具支持

## 📞 支持与反馈

如果您遇到问题或有建议，请：
- 在 GitHub 上[创建 Issue](https://github.com/xiongfazhan/VisioFirm-Enhanced/issues)
- 查看[原项目文档](https://github.com/OschAI/VisioFirm)

---

**让AI驱动的图像标注更智能、更高效！** 🚀