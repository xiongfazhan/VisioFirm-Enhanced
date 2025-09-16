#!/bin/bash
set -e

BACKUP_DIR="./backup/refactor_add_training_module"
PROJECT_ROOT="."

echo "开始回滚VisioFirm训练功能模块变更..."
echo "备份目录: $BACKUP_DIR"

# 检查备份目录是否存在
if [ ! -d "$BACKUP_DIR" ]; then
    echo "错误: 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# 恢复修改的文件
echo "恢复修改的文件..."

if [ -f "$BACKUP_DIR/create_app.py" ]; then
    cp "$BACKUP_DIR/create_app.py" "$PROJECT_ROOT/visiofirm/create_app.py"
    echo "已恢复: visiofirm/create_app.py"
fi

if [ -f "$BACKUP_DIR/index.html" ]; then
    cp "$BACKUP_DIR/index.html" "$PROJECT_ROOT/visiofirm/templates/index.html"
    echo "已恢复: visiofirm/templates/index.html"
fi

if [ -f "$BACKUP_DIR/labeler_base.html" ]; then
    cp "$BACKUP_DIR/labeler_base.html" "$PROJECT_ROOT/visiofirm/templates/labeler_base.html"
    echo "已恢复: visiofirm/templates/labeler_base.html"
fi

# 删除新增的文件
echo "删除新增的文件..."

# 删除训练相关的新文件
rm -f "$PROJECT_ROOT/visiofirm/models/training.py"
echo "已删除: visiofirm/models/training.py"

rm -f "$PROJECT_ROOT/visiofirm/routes/training.py"
echo "已删除: visiofirm/routes/training.py"

rm -f "$PROJECT_ROOT/visiofirm/utils/TrainingEngine.py"
echo "已删除: visiofirm/utils/TrainingEngine.py"

rm -f "$PROJECT_ROOT/visiofirm/templates/training.html"
echo "已删除: visiofirm/templates/training.html"

rm -f "$PROJECT_ROOT/visiofirm/static/js/training.js"
echo "已删除: visiofirm/static/js/training.js"

# 恢复utils/__init__.py文件
echo "恢复utils模块导入..."
cat > "$PROJECT_ROOT/visiofirm/utils/__init__.py" << 'EOF'
from .file_utils import CocoAnnotationParser, YoloAnnotationParser, NameMatcher, is_valid_image
from .export_utils import generate_coco_export, generate_yolo_export, generate_pascal_voc_export, generate_csv_export

__all__ = [
    'CocoAnnotationParser',
    'YoloAnnotationParser',
    'NameMatcher',
    'is_valid_image',
    'generate_coco_export',
    'generate_yolo_export',
    'generate_pascal_voc_export',
    'generate_csv_export',
    'split_images'
]
EOF
echo "已恢复: visiofirm/utils/__init__.py"

# 清理可能的Python缓存
echo "清理Python缓存..."
find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "回滚完成！"
echo ""
echo "变更已成功回滚到训练功能添加之前的状态。"
echo "注意事项："
echo "1. 请重启应用服务以确保变更生效"
echo "2. 训练相关的数据库表将保留，不会影响现有功能"
echo "3. 如果有正在进行的训练任务，请手动停止"
echo ""
echo "如需重新应用训练功能，请重新运行相应的部署脚本。"