#!/bin/bash

# VisioFirm 测试执行脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "  VisioFirm 测试套件"
echo "======================================"
echo ""

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}警告: 未检测到虚拟环境${NC}"
    echo "建议激活虚拟环境: source ~/venv/bin/activate"
    echo ""
fi

# 安装测试依赖
echo -e "${GREEN}[步骤 1/4] 安装测试依赖...${NC}"
pip install -q -r requirements-test.txt
echo "✓ 测试依赖已安装"
echo ""

# 运行单元测试
echo -e "${GREEN}[步骤 2/4] 运行单元测试...${NC}"
pytest tests/ -v -m "unit or not integration" --tb=short || {
    echo -e "${RED}✗ 单元测试失败${NC}"
    exit 1
}
echo ""

# 运行集成测试
echo -e "${GREEN}[步骤 3/4] 运行集成测试...${NC}"
pytest tests/ -v -m "integration" --tb=short || {
    echo -e "${YELLOW}! 部分集成测试失败（可能需要外部依赖）${NC}"
}
echo ""

# 生成覆盖率报告
echo -e "${GREEN}[步骤 4/4] 生成覆盖率报告...${NC}"
pytest tests/ --cov=. --cov-report=html --cov-report=term --cov-config=.coveragerc
echo ""

echo "======================================"
echo -e "${GREEN}✓ 测试完成！${NC}"
echo "======================================"
echo ""
echo "覆盖率报告已生成:"
echo "  - HTML报告: htmlcov/index.html"
echo "  - 终端报告: 已显示在上方"
echo ""
echo "运行单个测试文件:"
echo "  pytest tests/test_auth.py -v"
echo ""
echo "运行特定测试:"
echo "  pytest tests/test_auth.py::test_register_success -v"
echo ""