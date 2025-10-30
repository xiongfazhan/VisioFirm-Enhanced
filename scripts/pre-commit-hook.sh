#!/bin/bash
"""
Git pre-commit钩子
在代码提交前自动检查代码规范
"""

echo "🔍 运行代码规范检查..."

# 运行代码规范检查脚本
python3 scripts/check_code_standards.py

# 检查脚本退出状态
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 代码规范检查失败！"
    echo "请修复上述错误后再提交代码。"
    echo ""
    echo "💡 提示："
    echo "1. 确保HTML、CSS、JavaScript文件分离"
    echo "2. 避免在HTML中使用内联样式和脚本"
    echo "3. 使用RESTful API设计"
    echo "4. 遵循前后端分离原则"
    echo ""
    exit 1
fi

echo "✅ 代码规范检查通过！"
exit 0
