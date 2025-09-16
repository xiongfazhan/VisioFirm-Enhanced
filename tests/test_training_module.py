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
            
            # 测试更新任务状态
            task.update_task_status(task_id, 'running', 50)
            updated_task = task.get_task_details(task_id)
            assert updated_task['status'] == 'running'
            assert updated_task['progress'] == 50
            
            # 测试保存训练配置
            config_id = task.save_training_config(
                "test_config",
                "yolov8s",
                20,
                16,
                0.001,
                640,
                "auto",
                "Adam",
                {},
                {}
            )
            
            configs = task.get_training_configs()
            assert len(configs) == 1
            assert configs[0]['config_name'] == "test_config"
            
            print("✓ TrainingTask模型测试通过")
            return True
            
    except Exception as e:
        print(f"✗ TrainingTask模型测试失败: {e}")
        return False

def test_project_model():
    """测试Project模型的训练相关功能"""
    if not IMPORTS_SUCCESSFUL or Project is None:
        print("✗ Project模型训练功能测试失败: 模块导入失败")
        return False
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "test_project"
            project_path = temp_dir
            
            # 初始化Project
            project = Project(project_name, "test description", "Bounding Box", project_path)
            
            # 添加类别
            project.add_classes(["car", "person", "bike"])
            classes = project.get_classes()
            assert len(classes) == 3
            
            # 测试get_annotated_images方法（应该返回空列表）
            annotated_images = project.get_annotated_images()
            assert isinstance(annotated_images, list)
            assert len(annotated_images) == 0
            
            print("✓ Project模型训练功能测试通过")
            return True
            
    except Exception as e:
        print(f"✗ Project模型训练功能测试失败: {e}")
        return False

def test_training_engine_basic():
    """测试TrainingEngine基本功能"""
    if not IMPORTS_SUCCESSFUL or TrainingEngine is None:
        print("✗ TrainingEngine基本功能测试失败: 模块导入失败")
        return False
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "test_project"
            project_path = temp_dir
            
            # 初始化TrainingEngine
            engine = TrainingEngine(project_name, project_path)
            
            # 测试获取可用模型
            models = engine.get_available_models()
            assert isinstance(models, list)
            assert len(models) > 0
            
            # 测试获取设备信息
            devices = engine.get_device_info()
            assert isinstance(devices, list)
            assert len(devices) > 0
            
            print("✓ TrainingEngine基本功能测试通过")
            return True
            
    except Exception as e:
        print(f"✗ TrainingEngine基本功能测试失败: {e}")
        return False

def test_database_schema():
    """测试数据库架构"""
    if not IMPORTS_SUCCESSFUL or TrainingTask is None:
        print("✗ 数据库架构测试失败: 模块导入失败")
        return False
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "test_project"
            project_path = temp_dir
            
            # 初始化TrainingTask（会创建数据库表）
            task = TrainingTask(project_name, project_path)
            
            # 检查数据库文件存在
            db_path = os.path.join(project_path, 'config.db')
            assert os.path.exists(db_path)
            
            # 检查表结构
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # 检查训练任务表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_tasks'")
                assert cursor.fetchone() is not None
                
                # 检查训练配置表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_configs'")
                assert cursor.fetchone() is not None
                
                # 检查训练日志表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_logs'")
                assert cursor.fetchone() is not None
            
            print("✓ 数据库架构测试通过")
            return True
            
    except Exception as e:
        print(f"✗ 数据库架构测试失败: {e}")
        return False

def test_flask_routes():
    """测试Flask路由定义"""
    try:
        from visiofirm.routes.training import bp
        
        # 检查蓝图存在
        assert bp is not None
        assert bp.name == 'training'
        
        # 简单检查蓝图是否有路由规则
        # 注意: Blueprint本身没有url_map，只有注册到app后才有
        from visiofirm.routes.training import training_dashboard
        from visiofirm.routes.training import create_training_task
        from visiofirm.routes.training import start_training_task
        
        # 检查关键函数存在
        assert callable(training_dashboard)
        assert callable(create_training_task)
        assert callable(start_training_task)
        
        print("✓ Flask路由测试通过")
        return True
        
    except Exception as e:
        print(f"✗ Flask路由测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试VisioFirm训练模块...")
    print("=" * 50)
    
    tests = [
        test_import_modules,
        test_database_schema,
        test_training_task_model,
        test_project_model,
        test_training_engine_basic,
        test_flask_routes
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 测试 {test.__name__} 出现异常: {e}")
    
    print("=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！训练模块基本功能正常。")
        return True
    else:
        print("⚠️  部分测试失败，请检查相关功能。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)