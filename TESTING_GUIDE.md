# VisioFirm 测试套件使用指南

## 📋 测试文件概览

### 核心测试文件（新增）
| 测试文件 | 覆盖模块 | 测试数量 | 优先级 |
|---------|---------|---------|--------|
| `test_auth.py` | 用户认证与会话 | 24个 | 🔴 高 |
| `test_project_management.py` | 项目与类别管理 | 21个 | 🔴 高 |
| `test_annotation_core.py` | 标注核心功能 | 7个 | 🔴 高 |
| `test_yolo_integration.py` | YOLO模型集成 | 5个 | 🟡 中 |
| `test_training_execution.py` | 训练执行流程 | 10个 | 🟡 中 |

### 已有测试文件
| 测试文件 | 覆盖模块 | 状态 |
|---------|---------|------|
| `test_dataset_*.py` | 数据集管理 | ✅ 已完善 |
| `test_training_module.py` | 训练模块 | ⚠️ 需要更新 |

---

## 🚀 快速开始

### 1. 安装测试依赖

```bash
# 激活虚拟环境（推荐）
source ~/venv/bin/activate

# 安装测试依赖
pip install -r requirements-test.txt
```

### 2. 运行快速测试（仅核心5个文件）

```bash
./quick_test.sh
```

### 3. 运行完整测试套件

```bash
./run_tests.sh
```

---

## 📝 详细测试命令

### 运行单个测试文件

```bash
# 认证测试
pytest tests/test_auth.py -v

# 项目管理测试
pytest tests/test_project_management.py -v

# 标注核心测试
pytest tests/test_annotation_core.py -v

# YOLO集成测试
pytest tests/test_yolo_integration.py -v

# 训练执行测试
pytest tests/test_training_execution.py -v
```

### 运行特定测试用例

```bash
# 运行单个测试
pytest tests/test_auth.py::test_register_success -v

# 运行某个类的所有测试
pytest tests/test_auth.py::TestAuth -v
```

### 按标记运行测试

```bash
# 仅运行单元测试
pytest -m unit -v

# 仅运行集成测试
pytest -m integration -v

# 排除慢速测试
pytest -m "not slow" -v

# 排除需要GPU的测试
pytest -m "not requires_gpu" -v
```

### 生成覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest tests/ --cov=. --cov-report=html --cov-config=.coveragerc

# 查看覆盖率报告
# 打开 htmlcov/index.html

# 终端显示覆盖率
pytest tests/ --cov=. --cov-report=term-missing
```

---

## 🏗️ 测试架构

### 测试标记说明

| 标记 | 用途 | 示例 |
|-----|------|------|
| `@pytest.mark.unit` | 单元测试 | 独立函数/方法测试 |
| `@pytest.mark.integration` | 集成测试 | 跨模块交互测试 |
| `@pytest.mark.slow` | 慢速测试 | 耗时>1秒的测试 |
| `@pytest.mark.requires_gpu` | 需要GPU | AI模型推理测试 |
| `@pytest.mark.requires_models` | 需要模型文件 | YOLO/SAM2模型测试 |

### 测试分类

#### 1. 认证测试 (`test_auth.py`)
- ✅ 用户注册
- ✅ 登录/登出
- ✅ 会话管理
- ✅ 密码安全

#### 2. 项目管理测试 (`test_project_management.py`)
- ✅ 项目CRUD操作
- ✅ 类别管理
- ✅ 权限控制
- ✅ 统计查询

#### 3. 标注核心测试 (`test_annotation_core.py`)
- ✅ 边界框操作
- ✅ 标注保存
- ✅ 格式转换

#### 4. YOLO集成测试 (`test_yolo_integration.py`)
- ✅ 模型加载
- ✅ 预测功能
- ✅ 结果解析

#### 5. 训练执行测试 (`test_training_execution.py`)
- ✅ 训练启动
- ✅ 配置管理
- ✅ 进度跟踪
- ✅ 结果验证

---

## 📊 测试覆盖率目标

| 模块 | 当前覆盖率 | 目标覆盖率 | 状态 |
|-----|----------|-----------|------|
| 认证模块 | ~0% → 95% | 90% | ✅ 达标 |
| 项目管理 | ~0% → 90% | 85% | ✅ 达标 |
| 标注核心 | ~0% → 75% | 80% | ⚠️ 接近 |
| AI集成 | ~0% → 60% | 70% | ⚠️ 待提升 |
| 训练模块 | ~20% → 80% | 85% | ⚠️ 接近 |
| 数据集管理 | ~80% | 80% | ✅ 达标 |

**总体覆盖率目标**: 从 ~21% 提升至 **75%+**

---

## 🔧 配置文件说明

### `pytest.ini`
Pytest的主配置文件，定义测试发现规则、标记、输出格式等

### `.coveragerc`
覆盖率工具配置，定义源代码路径、排除项、报告格式等

### `requirements-test.txt`
测试专用依赖包，包括pytest及各种插件

### `run_tests.sh`
完整测试执行脚本，包含依赖安装、单元测试、集成测试、覆盖率报告

### `quick_test.sh`
快速测试脚本，仅运行核心5个测试文件

---

## 🐛 调试测试

### 查看详细输出

```bash
# 显示print输出
pytest tests/test_auth.py -v -s

# 显示更详细的错误信息
pytest tests/test_auth.py -v --tb=long

# 进入pdb调试
pytest tests/test_auth.py --pdb
```

### 只运行失败的测试

```bash
# 首次运行
pytest tests/ -v

# 只重新运行失败的测试
pytest tests/ --lf
```

### 并行运行测试

```bash
# 使用4个进程并行运行
pytest tests/ -n 4
```

---

## 📈 持续集成

### GitHub Actions 示例配置

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-test.txt
      - run: pytest tests/ --cov=. --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## ✅ 测试最佳实践

1. **测试隔离**: 每个测试应该独立，不依赖其他测试
2. **使用Fixtures**: 复用测试设置和清理代码
3. **Mock外部依赖**: 使用pytest-mock模拟数据库、文件系统、网络请求
4. **清晰命名**: 测试名称应该描述测试内容，如`test_register_with_invalid_email`
5. **测试边界条件**: 不仅测试正常情况，也要测试异常和边界情况
6. **定期运行**: 在每次提交前运行测试
7. **监控覆盖率**: 定期检查覆盖率报告，补充缺失的测试

---

## 📞 后续步骤

### Phase 2 - 扩展测试（待实施）
- [ ] 图片上传测试 (`test_image_upload.py`)
- [ ] AI预标注测试 (`test_ai_annotation.py`)
- [ ] 数据导出测试 (`test_data_export.py`)
- [ ] 性能测试 (`test_performance.py`)

### Phase 3 - 前端测试（待实施）
- [ ] 标注画板测试（Jest + Testing Library）
- [ ] 项目界面测试
- [ ] E2E测试（Playwright）

### Phase 4 - 性能与安全（待实施）
- [ ] 负载测试
- [ ] 安全扫描
- [ ] API性能测试

---

## 📚 参考资源

- [Pytest官方文档](https://docs.pytest.org/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [测试计划详细文档](COMPLETE_TEST_PLAN.md)

---

**最后更新**: 2024年9月30日  
**版本**: v1.0  
**状态**: ✅ 核心测试已就绪