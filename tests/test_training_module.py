#!/usr/bin/env python3
"""
VisioFirm训练模块测试脚本
测试训练模块的核心功能是否正常工作
"""

import sys
import os
import tempfile
import json
import sqlite3
from pathlib import Path

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

# 全局导入
try:
    from visiofirm.models.training import TrainingTask
    from visiofirm.utils.TrainingEngine import TrainingEngine
    from visiofirm.models.project import Project
    IMPORTS_SUCCESSFUL = True
except ImportError as e:
    print(f"导入错误: {e}")
    IMPORTS_SUCCESSFUL = False
    TrainingTask = None
    TrainingEngine = None
    Project = None

def test_import_modules():
    """测试模块导入"""
    if IMPORTS_SUCCESSFUL:
        print("✓ 模块导入成功")
        return True
    else:
        print("✗ 模块导入失败")
        return False

def test_training_task_model():
    """测试TrainingTask模型"""
    if not IMPORTS_SUCCESSFUL or TrainingTask is None:
        print("✗ TrainingTask模型测试失败: 模块导入失败")
        return False
    try:
        # 创建临时项目目录
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "test_project"
            project_path = temp_dir
            
            # 初始化TrainingTask
            task = TrainingTask(project_name, project_path)
            
            # 测试创建训练任务
            dataset_split = {'train': 0.7, 'val': 0.2, 'test': 0.1}
            config = {
                'epochs': 10,
                'batch_size': 8,
                'learning_rate': 0.01,
                'image_size': 640,
                'device': 'cpu'
            }
            
            task_id = task.create_training_task(
                "test_task",
                "yolov8n",
                dataset_split,
                config
            )
            
            # 测试获取任务详情
            task_details = task.get_task_details(task_id)
            assert task_details is not None
            assert task_details['task_name'] == "test_task"
            assert task_details['model_type'] == "yolov8n"
            
            print("✓ TrainingTask模型测试通过")
            return True
            
    except Exception as e:
        print(f"✗ TrainingTask模型测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 VisioFirm 训练模块测试开始...")
    
    tests = [
        test_import_modules,
        test_training_task_model,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ 测试 {test.__name__} 失败: {e}")
            failed += 1
    
    print(f"\n📊 测试结果:")
    print(f"✓ 成功: {passed}")
    print(f"✗ 失败: {failed}")
    print(f"🏆 总计: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)