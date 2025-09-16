#!/bin/bash
set -e

BACKUP_DIR="./backup/refactor_project_structure"
echo "正在回滚项目结构到备份: $BACKUP_DIR"

# 恢复测试文件到根目录
if [ -f "$BACKUP_DIR/test_training_module.py" ]; then
    cp "$BACKUP_DIR/test_training_module.py" ./
    echo "已恢复 test_training_module.py"
fi

# 恢复文档文件
for file in "$BACKUP_DIR"/*.md; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        cp "$file" "./$(basename "$file")"
        echo "已恢复 $filename"
    fi
done

# 删除可能创建的目录结构
if [ -d "./tests" ] && [ -z "$(ls -A ./tests)" ]; then
    rmdir ./tests
    echo "已删除空的 tests 目录"
fi

echo "项目结构回滚完成"