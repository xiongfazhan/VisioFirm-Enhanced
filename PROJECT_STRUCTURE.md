# VisioFirm Enhanced - 项目结构说明

本项目是基于 [OschAI/VisioFirm](https://github.com/OschAI/VisioFirm) 的二次开发增强版本。

## 📁 项目结构

```
VisioFirm-Enhanced/
├── README.md                   # 项目主要说明文档
├── CHANGELOG.md               # 更新日志
├── ATTRIBUTION.md             # 归属说明和致谢
├── LICENSE                    # Apache 2.0 许可证
├── requirements.txt           # Python依赖包
├── setup.py                   # 项目安装配置
├── pyproject.toml            # 构建系统配置
├── run.py                     # 应用启动入口
└── visiofirm/                # 主要源代码目录
    ├── __init__.py           # 包初始化
    ├── config.py             # 配置管理
    ├── create_app.py         # Flask应用创建
    ├── models/               # 数据模型
    │   ├── __init__.py
    │   ├── user.py          # 用户模型
    │   ├── project.py       # 项目模型
    │   └── training.py      # 训练模型 [新增]
    ├── routes/               # 路由模块
    │   ├── __init__.py
    │   ├── auth.py          # 用户认证路由
    │   ├── dashboard.py     # 项目管理路由
    │   ├── annotation.py    # 标注功能路由
    │   └── training.py      # 训练功能路由 [新增]
    ├── templates/            # HTML模板
    │   ├── *.html           # 各页面模板
    │   └── ...
    ├── static/               # 静态资源
    │   ├── css/             # 样式文件
    │   ├── js/              # JavaScript文件
    │   └── ...
    └── utils/                # 工具函数
        ├── __init__.py
        ├── file_utils.py    # 文件处理工具
        ├── export_utils.py  # 导出工具
        ├── VFPreAnnotator.py # AI预标注器
        ├── TrainingEngine.py # 训练引擎 [新增]
        └── GroundingDinoConfigs/ # AI模型配置
```

## 🚀 主要增强特性

### 1. 训练模块 [新增]
- **文件**: `visiofirm/routes/training.py`, `visiofirm/models/training.py`, `visiofirm/utils/TrainingEngine.py`
- **功能**: 完整的模型训练工作流，支持自定义参数配置和训练进度监控

### 2. 中文本地化 [增强]
- **范围**: 所有用户界面、错误提示、文档说明
- **目标**: 提升中文用户的使用体验

### 3. 性能优化 [增强]
- **多线程上传**: 优化大文件处理机制
- **SAM2 Worker**: 浏览器端高性能分割
- **内存管理**: 改进资源使用效率

### 4. 架构改进 [增强]
- **模块化设计**: 更清晰的Flask Blueprint结构
- **代码质量**: 增强错误处理和日志记录
- **扩展性**: 更易于集成自定义AI模型

## 🔗 与源项目的关系

- **完全兼容**: 支持原项目的所有数据格式和导出功能
- **保持接口**: 维护相同的API设计，确保无缝迁移
- **增强功能**: 在原有基础上添加新特性，不破坏原有功能

## 📚 相关文档

- **安装使用**: 参见 [README.md](README.md)
- **更新历史**: 参见 [CHANGELOG.md](CHANGELOG.md) 
- **许可说明**: 参见 [ATTRIBUTION.md](ATTRIBUTION.md)
- **源项目**: [VisioFirm by OschAI](https://github.com/OschAI/VisioFirm)

---

**注意**: 本项目遵循开源精神，尊重原作者权益，致力于推动AI图像标注技术的发展。