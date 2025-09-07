![VisioFirm](https://github.com/OschAI/VisioFirm/blob/main/examples/visiofirm-logo.gif)

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
- **Browser-Based Editing**: Interactive canvas for precise adjustments, with real-time SAM-powered segmentation in the browser.
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

