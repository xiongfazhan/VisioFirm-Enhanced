# 贡献指南 (CONTRIBUTING)

感谢您对 VisioFirm Enhanced 项目的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告问题
如果您发现了bug或有功能建议：
1. 在 [Issues](https://github.com/xiongfazhan/VisioFirm-Enhanced/issues) 中搜索是否已有相同问题
2. 如果没有，请创建新的Issue并提供详细信息

### 提交代码
1. **Fork** 本项目到您的GitHub账户
2. **Clone** 您的Fork到本地
3. 创建新的功能分支：`git checkout -b feature/amazing-feature`
4. 进行您的修改
5. 提交更改：`git commit -m 'Add some amazing feature'`
6. 推送到分支：`git push origin feature/amazing-feature`
7. 创建 **Pull Request**

## 💻 开发环境设置

### 环境要求
- Python 3.10+
- Git
- 支持的操作系统: Linux, macOS, Windows

### 本地开发
```bash
# 克隆您的Fork
git clone https://github.com/YOUR_USERNAME/VisioFirm-Enhanced.git
cd VisioFirm-Enhanced

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\\Scripts\\activate  # Windows

# 安装依赖
pip install -e .
pip install -r requirements.txt

# 运行项目
visiofirm
```

## 📋 代码规范

### Python代码风格
- 遵循 PEP 8 标准
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串

### 提交消息格式
```
类型: 简短描述 (50字符内)

更详细的说明（如果需要）
- 使用现在时态
- 首字母大写
- 不以句号结尾
```

### 代码审查
- 所有代码更改需要通过Pull Request
- 保持代码简洁和可读性
- 确保现有测试通过
- 为新功能添加适当的测试

## 🎯 贡献重点领域

### 高优先级
- 🐛 Bug修复
- 📚 文档改进
- 🌐 中文本地化完善
- ⚡ 性能优化

### 欢迎贡献的功能
- 🎨 UI/UX改进
- 🧪 单元测试增加
- 🔧 工具和脚本
- 📱 移动端适配

### 需要技术经验的领域
- 🤖 AI模型集成
- 🔬 训练算法优化
- 🏗️ 架构改进
- 🔒 安全性增强

## 📖 文档贡献

### 文档类型
- **用户文档**: 安装、使用指南
- **开发文档**: API文档、架构说明
- **示例代码**: 使用示例和教程
- **翻译**: 多语言支持

### 文档标准
- 使用清晰简洁的语言
- 提供实际的代码示例
- 保持文档与代码同步更新

## 🌟 认可贡献者

我们会在以下方式认可贡献者：
- 在README中列出贡献者
- 在发布说明中感谢贡献者
- 通过GitHub的贡献者统计展示

## 📞 联系我们

如果您有任何问题或需要帮助：
- 📧 通过GitHub Issues联系我们
- 💬 参与GitHub Discussions讨论
- 🔗 查看[原项目](https://github.com/OschAI/VisioFirm)了解更多信息

## 📄 许可证

通过向本项目贡献，您同意您的贡献将在 [Apache 2.0](LICENSE) 许可证下授权。

---

**感谢您的贡献，让我们一起打造更好的AI图像标注工具！** 🚀