#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练执行测试模块
测试训练任务的启动、停止、监控等功能
"""

import unittest
import tempfile
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from visiofirm.utils.TrainingEngine import TrainingEngine
    from visiofirm.models.training import TrainingTask
    from visiofirm.models.project import Project
    IMPORTS_OK = True
except ImportError as e:
    print(f"警告: 训练模块导入失败: {e}")
    IMPORTS_OK = False


class TestTrainingExecution(unittest.TestCase):
    """训练执行测试类"""
    
    def setUp(self):
        """每个测试方法的设置"""
        if not IMPORTS_OK:
            self.skipTest("训练模块导入失败")
        
        self.temp_dir = tempfile.mkdtemp()
        self.project_name = "test_training_project"
        self.project_path = os.path.join(self.temp_dir, self.project_name)
        
        # 创建测试项目
        self.project = Project(
            self.project_name,
            "Test training project",
            "Bounding Box",
            self.project_path
        )
        
        # 初始化训练引擎
        self.engine = TrainingEngine(self.project_name, self.project_path)
        
    def tearDown(self):
        """每个测试方法的清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    # ==================== 训练配置测试 ====================
    
    def test_get_available_models(self):
        """测试获取可用模型列表"""
        models = self.engine.get_available_models()
        
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        
        # 验证包含YOLO模型
        model_names = [m['name'] for m in models]
        self.assertIn('yolov8n', model_names)
    
    def test_get_device_info(self):
        """测试获取设备信息"""
        devices = self.engine.get_device_info()
        
        self.assertIsInstance(devices, list)
        self.assertGreater(len(devices), 0)
        
        # 至少应该有CPU和auto选项
        device_names = [d['name'] for d in devices]
        self.assertIn('cpu', device_names)
        self.assertIn('auto', device_names)
    
    # ==================== 数据集准备测试 ====================
    
    def test_dataset_preparation_no_data(self):
        """测试无数据时准备数据集应失败"""
        dataset_split = {'train': 0.7, 'val': 0.2, 'test': 0.1}
        
        with self.assertRaises(Exception):
            self.engine.prepare_dataset(dataset_split)
    
    def test_dataset_split_validation(self):
        """测试数据集分割比例验证"""
        # 分割比例不为1应该失败
        invalid_split = {'train': 0.5, 'val': 0.3, 'test': 0.3}  # 和为1.1
        
        with self.assertRaises(ValueError):
            self.engine.prepare_dataset(invalid_split)
    
    # ==================== 训练任务创建测试 ====================
    
    def test_create_training_task(self):
        """测试创建训练任务"""
        training_task = TrainingTask(self.project_name, self.project_path)
        
        dataset_split = {'train': 0.7, 'val': 0.2, 'test': 0.1}
        config = {
            'epochs': 10,
            'batch_size': 8,
            'learning_rate': 0.01,
            'image_size': 640,
            'device': 'cpu'
        }
        
        task_id = training_task.create_training_task(
            "test_task",
            "yolov8n",
            dataset_split,
            config
        )
        
        self.assertIsNotNone(task_id)
        self.assertGreater(task_id, 0)
    
    def test_get_training_status(self):
        """测试获取训练状态"""
        training_task = TrainingTask(self.project_name, self.project_path)
        
        dataset_split = {'train': 0.7, 'val': 0.2, 'test': 0.1}
        config = {'epochs': 10, 'batch_size': 8}
        
        task_id = training_task.create_training_task(
            "test_task",
            "yolov8n",
            dataset_split,
            config
        )
        
        status = self.engine.get_training_status(task_id)
        
        self.assertIsNotNone(status)
        self.assertEqual(status['status'], 'pending')
    
    # ==================== 训练启动测试 ====================
    
    def test_start_training_without_data(self):
        """测试无数据时启动训练应失败"""
        # 这个测试需要实际的训练数据，暂时跳过
        self.skipTest("需要实际的训练数据")
    
    # ==================== 训练停止测试 ====================
    
    def test_stop_nonexistent_training(self):
        """测试停止不存在的训练任务"""
        result = self.engine.stop_training_task(99999)
        
        # 应该返回False或抛出异常
        self.assertFalse(result)
    
    # ==================== 模型导出测试 ====================
    
    def test_export_model_nonexistent(self):
        """测试导出不存在的模型"""
        with self.assertRaises(FileNotFoundError):
            self.engine.export_model('/nonexistent/model.pt', 'onnx')


if __name__ == '__main__':
    unittest.main(verbosity=2)
