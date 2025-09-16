![VisioFirm](https://github.com/OschAI/VisioFirm/blob/main/examples/visiofirm-logo.gif)

# VisioFirm: 快速近乎全自动的计算机视觉图像标注工具

[![GitHub Stars](https://img.shields.io/github/stars/OschAI/VisioFirm?style=social)](https://github.com/OschAI/VisioFirm/stargazers)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/OschAI/VisioFirm/blob/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/visiofirm.svg)](https://pypi.org/project/visiofirm/) 
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

-------
> [!IMPORTANT]
> 新版本刚刚发布。`VisioFirm 0.2.0` 带来了增强功能，包括图像导入的错误修复、改进的前端加载、云/SSH支持用于下载图像和保存标注、SAM2工作器卸载以获得更好的性能、优化的SAM2自动标注以实现更快的计算，以及图像上传的线程优化。此版本基于0.1.4的稳定GroundingDINO依赖构建。
> - **云/SSH集成**：从云存储或SSH服务器下载图像并远程保存标注（使用本地绝对路径）。
> - **增强的图像处理**：修复了图像导入中的错误，更快的前端加载，以及多线程上传以提高效率。
> - **SAM2优化**：基于工作器的卸载和改进的自动标注，在浏览器中实现快速、高性能的分割。虽然您可能会在第一次标签生成时遇到首次延迟，但后续的标注器是即时的。

> [!NOTE]
> 如果您更喜欢基于HF transformers的库（0.2.0之前），请通过`pip install visiofirm==0.1.0`从主分支安装。
-------

**VisioFirm** 是一个开源的、AI驱动的图像标注工具，旨在加速计算机视觉任务的标注，如目标检测、有向边界框（OBB）和分割。为速度和简单性而构建，它利用最先进的模型进行半自动预标注，让您专注于精炼而不是从头开始。无论您是为YOLO、SAM还是自定义模型准备数据集，VisioFirm都通过直观的Web界面和强大的后端简化您的工作流程。

非常适合处理大型图像数据集的研究人员、数据科学家和机器学习工程师——在几分钟内获得高质量的标注，而不是几小时！

## 为什么选择VisioFirm？

与其他标注工具不同，这个工具主要专注于计算机视觉任务标注检测（普通和有向边界框）和分割。

- **AI驱动的预标注**：使用YOLOv10、SAM2和Grounding DINO自动检测和分割对象——节省高达80%的手动工作。
- **多任务支持**：在一个工具中处理边界框、有向边界框和多边形分割。
- **基于浏览器的编辑**：交互式画布进行精确调整，在浏览器中实时SAM驱动的分割。
- **离线友好**：模型自动下载（或预取以供离线使用），使用SQLite后端进行本地项目。
- **可扩展和开源**：使用您自己的ultralytics模型进行自定义或集成到管道中——欢迎贡献！
- **SAM2-base webgpu**：通过SAM2与工作器卸载和自动标注实现标注的即时绘制，以实现更快的计算！
![标注编辑演示](https://github.com/OschAI/VisioFirm/blob/main/examples/orange-apples-test.gif) 

## 功能特性

- **半自动标注**：使用AI模型如YOLO进行检测、SAM进行分割、Grounding DINO进行零样本对象定位来启动标注。
- **灵活的标注类型**：
  - 用于标准检测的轴对齐边界框。
  - 用于旋转对象的有向边界框（例如，航空图像）。
  - 用于精确边界的多边形分割。
- **交互式前端**：在响应式画布上绘制、编辑和精炼标签。使用基于浏览器的SAM进行点击分割以获得即时掩码。
- **项目管理**：使用SQLite数据库存储创建、管理和导出项目。支持多个类别和图像。
- **导出格式**：无缝导出到YOLO、COCO或自定义格式进行训练。
- **性能优化**：聚类重叠检测、简化轮廓，并按置信度过滤以获得干净的数据集。
- **云/SSH集成**：无缝从云存储或SSH服务器下载图像并远程保存标注。
- **增强的图像处理**：修复了图像导入中的错误，更快的前端加载，以及多线程上传以提高效率。
- **SAM2优化**：基于工作器的卸载和改进的自动标注，在浏览器中实现快速、高性能的分割。
- **跨平台**：通过Python在Linux、macOS或Windows上本地运行——无云依赖。

![标注编辑演示](https://github.com/OschAI/VisioFirm/blob/main/examples/AIpreannotator-demo.gif) 

## 安装

VisioFirm很容易通过pip从GitHub安装（PyPI即将推出！）。

已在`Python 3.10+`上测试。

```bash
pip install -U visiofirm
```

对于开发或可编辑安装（从克隆的仓库）：

```bash
git clone https://github.com/OschAI/VisioFirm.git
cd VisioFirm
pip install -e .
```

## 快速开始

使用单个命令启动VisioFirm——它会自动启动本地Web服务器并在浏览器中打开。

```bash
visiofirm
```

1. 创建新项目并上传图像。
2. 定义类别（例如，"汽车"、"人"）。
3. 对于易于检测的对象运行AI预标注（选择模型：YOLO、Grounding DINO）。
4. 在交互式编辑器中精炼标签。
5. 导出您的标注数据集。

VisioFirm应用程序使用缓存目录在本地存储设置。

## 使用方法

### 使用AI进行预标注

VisioFirm使用先进的模型进行初始标签：

- **YOLOv10**：快速检测。
- **SAM2**：精确分割。
- **Grounding DINO**：通过文本提示进行零样本检测。

模型在首次运行时自动下载（存储在当前目录或缓存中）。对于离线准备：

### 前端自定义

Web界面（Flask + JS）支持热键、撤销/重做和缩放。编辑`static/js/sam.js`进行浏览器SAM调整。

### 导出数据

支持多种格式：YOLO、COCO、Pascal VOC、CSV。导出包括图像、标注和元数据。

## 贡献

欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解详细信息。

## 许可证

本项目采用Apache 2.0许可证 - 详情请参阅[LICENSE](LICENSE)文件。

## 支持

如果您遇到问题或有疑问，请在GitHub上[创建issue](https://github.com/OschAI/VisioFirm/issues)。

---

**让标注变得简单快速！** 🚀
