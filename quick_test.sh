#!/bin/bash

# VisioFirm 快速测试脚本（仅运行核心测试）

set -e

GREEN='\033[0;32m'
NC='\033[0m'

echo "======================================"
echo "  快速测试 (核心5个测试文件)"
echo "======================================"
echo ""

# 测试文件列表
tests=(
    "test_auth.py"
    "test_project_management.py"
    "test_annotation_core.py"
    "test_yolo_integration.py"
    "test_training_execution.py"
)

for test in "${tests[@]}"; do
    echo -e "${GREEN}运行: $test${NC}"
    pytest tests/$test -v --tb=line || echo "✗ $test 有失败"
    echo ""
done

echo "======================================"
echo -e "${GREEN}✓ 快速测试完成！${NC}"
echo "======================================"