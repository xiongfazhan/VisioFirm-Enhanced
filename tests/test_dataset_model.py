#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集模型测试模块
测试数据集模型的CRUD操作和数据库交互功能
"""

import unittest
import tempfile
import os
import shutil
import sqlite3
from datetime import datetime
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from visiofirm.models.dataset import (
    Dataset, 
    init_dataset_db, 
    create_dataset, 
    get_dataset_by_id,
    get_datasets,
    update_dataset,
    delete_dataset,
    search_datasets,
    get_dataset_classes,
    add_dataset_classes,
    link_dataset_to_project,
    unlink_dataset_from_project,
    get_project_datasets
)


class TestDatasetModel(unittest.TestCase):
    """数据集模型测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        # 创建临时目录
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, 'test_datasets.db')
        
        # 初始化测试数据库
        cls.setup_test_database()
        
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        # 清理临时目录
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def setup_test_database(cls):
        """设置测试数据库"""
        # 创建数据集表
        init_dataset_db(cls.test_db_path)
        
        # 创建测试数据集文件
        cls.create_test_dataset_files()
    
    @classmethod
    def create_test_dataset_files(cls):
        """创建测试数据集文件"""
        # 创建测试数据集目录
        cls.test_dataset_dir = os.path.join(cls.temp_dir, 'test_dataset')
        os.makedirs(cls.test_dataset_dir, exist_ok=True)
        
        # 创建测试图片目录
        images_dir = os.path.join(cls.test_dataset_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # 创建一些测试图片文件（空文件）
        for i in range(5):
            with open(os.path.join(images_dir, f'test_image_{i}.jpg'), 'w') as f:
                f.write('')
        
        # 创建标注文件
        annotations_dir = os.path.join(cls.test_dataset_dir, 'annotations')
        os.makedirs(annotations_dir, exist_ok=True)
        
        # 创建类别文件
        with open(os.path.join(cls.test_dataset_dir, 'classes.txt'), 'w') as f:
            f.write('cat\ndog\nbird\n')
    
    def setUp(self):
        """每个测试方法的设置"""
        # 清理数据库数据
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Project_Datasets')
            cursor.execute('DELETE FROM Dataset_Classes')
            cursor.execute('DELETE FROM Datasets')
            conn.commit()
    
    def test_dataset_class_creation(self):
        """测试Dataset类的创建"""
        dataset = Dataset(
            name="Test Dataset",
            description="A test dataset",
            dataset_type="custom",
            file_path=self.test_dataset_dir
        )
        
        self.assertEqual(dataset.name, "Test Dataset")
        self.assertEqual(dataset.description, "A test dataset")
        self.assertEqual(dataset.dataset_type, "custom")
        self.assertEqual(dataset.file_path, self.test_dataset_dir)
        self.assertIsNone(dataset.dataset_id)
    
    def test_create_dataset(self):
        """测试创建数据集"""
        dataset_data = {
            'name': 'Test Dataset 1',
            'description': 'First test dataset',
            'dataset_type': 'custom',
            'file_path': self.test_dataset_dir,
            'file_size': 1024000,
            'image_count': 5,
            'class_count': 3,
            'annotation_format': 'yolo'
        }
        
        dataset_id = create_dataset(self.test_db_path, **dataset_data)
        self.assertIsNotNone(dataset_id)
        self.assertIsInstance(dataset_id, int)
        
        # 验证数据集已创建
        dataset = get_dataset_by_id(self.test_db_path, dataset_id)
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.name, 'Test Dataset 1')
        self.assertEqual(dataset.description, 'First test dataset')
        self.assertEqual(dataset.dataset_type, 'custom')
        self.assertEqual(dataset.file_size, 1024000)
        self.assertEqual(dataset.image_count, 5)
        self.assertEqual(dataset.class_count, 3)
        self.assertEqual(dataset.annotation_format, 'yolo')
    
    def test_get_dataset_by_id(self):
        """测试根据ID获取数据集"""
        # 创建测试数据集
        dataset_id = create_dataset(
            self.test_db_path,
            name='Test Dataset 2',
            description='Second test dataset',
            dataset_type='downloaded',
            file_path=self.test_dataset_dir
        )
        
        # 获取数据集
        dataset = get_dataset_by_id(self.test_db_path, dataset_id)
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.dataset_id, dataset_id)
        self.assertEqual(dataset.name, 'Test Dataset 2')
        
        # 测试不存在的ID
        nonexistent_dataset = get_dataset_by_id(self.test_db_path, 99999)
        self.assertIsNone(nonexistent_dataset)
    
    def test_get_all_datasets(self):
        """测试获取所有数据集"""
        # 创建多个测试数据集
        dataset_ids = []
        for i in range(3):
            dataset_id = create_dataset(
                name=f'Test Dataset {i+1}',
                description=f'Dataset number {i+1}',
                dataset_type='custom',
                file_path=self.test_dataset_dir
            )
            dataset_ids.append(dataset_id)
        
        # 获取所有数据集
        datasets, total = get_datasets()
        self.assertEqual(total, 3)
        
        # 验证数据集内容
        dataset_names = [d.name for d in datasets]
        self.assertIn('Test Dataset 1', dataset_names)
        self.assertIn('Test Dataset 2', dataset_names)
        self.assertIn('Test Dataset 3', dataset_names)
    
    def test_update_dataset(self):
        """测试更新数据集"""
        # 创建测试数据集
        dataset_id = create_dataset(
            self.test_db_path,
            name='Original Name',
            description='Original description',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        # 更新数据集
        update_data = {
            'description': 'Updated description',
            'image_count': 10,
            'class_count': 5,
            'annotation_format': 'coco'
        }
        
        success = update_dataset(self.test_db_path, dataset_id, **update_data)
        self.assertTrue(success)
        
        # 验证更新
        updated_dataset = get_dataset_by_id(self.test_db_path, dataset_id)
        self.assertEqual(updated_dataset.description, 'Updated description')
        self.assertEqual(updated_dataset.image_count, 10)
        self.assertEqual(updated_dataset.class_count, 5)
        self.assertEqual(updated_dataset.annotation_format, 'coco')
        # 名称应该保持不变
        self.assertEqual(updated_dataset.name, 'Original Name')
    
    def test_delete_dataset(self):
        """测试删除数据集"""
        # 创建测试数据集
        dataset_id = create_dataset(
            self.test_db_path,
            name='Dataset to Delete',
            description='This dataset will be deleted',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        # 验证数据集存在
        dataset = get_dataset_by_id(self.test_db_path, dataset_id)
        self.assertIsNotNone(dataset)
        
        # 删除数据集
        success = delete_dataset(self.test_db_path, dataset_id)
        self.assertTrue(success)
        
        # 验证数据集已删除
        deleted_dataset = get_dataset_by_id(self.test_db_path, dataset_id)
        self.assertIsNone(deleted_dataset)
    
    def test_search_datasets(self):
        """测试搜索数据集"""
        # 创建多个测试数据集
        datasets_data = [
            {'name': 'COCO Dataset', 'description': 'Common Objects in Context'},
            {'name': 'ImageNet Dataset', 'description': 'Large scale image recognition'},
            {'name': 'Custom Cat Dataset', 'description': 'Custom dataset with cat images'},
            {'name': 'Dog Classification', 'description': 'Dataset for dog breed classification'}
        ]
        
        for data in datasets_data:
            create_dataset(
                self.test_db_path,
                name=data['name'],
                description=data['description'],
                dataset_type='custom',
                file_path=self.test_dataset_dir
            )
        
        # 测试按名称搜索
        results = search_datasets(self.test_db_path, 'COCO')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'COCO Dataset')
        
        # 测试按描述搜索
        results = search_datasets(self.test_db_path, 'classification')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Dog Classification')
        
        # 测试部分匹配
        results = search_datasets(self.test_db_path, 'Dataset')
        self.assertEqual(len(results), 3)  # COCO Dataset, ImageNet Dataset, Custom Cat Dataset
        
        # 测试不存在的搜索
        results = search_datasets(self.test_db_path, 'nonexistent')
        self.assertEqual(len(results), 0)
    
    def test_dataset_classes_management(self):
        """测试数据集类别管理"""
        # 创建测试数据集
        dataset_id = create_dataset(
            self.test_db_path,
            name='Dataset with Classes',
            description='Dataset for testing classes',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        # 添加类别
        class_names = ['cat', 'dog', 'bird', 'fish']
        for class_name in class_names:
            success = add_dataset_class(self.test_db_path, dataset_id, class_name)
            self.assertTrue(success)
        
        # 获取类别
        classes = get_dataset_classes(self.test_db_path, dataset_id)
        self.assertEqual(len(classes), 4)
        self.assertEqual(set(classes), set(class_names))
        
        # 删除类别
        success = remove_dataset_class(self.test_db_path, dataset_id, 'fish')
        self.assertTrue(success)
        
        # 验证删除
        classes = get_dataset_classes(self.test_db_path, dataset_id)
        self.assertEqual(len(classes), 3)
        self.assertNotIn('fish', classes)
        self.assertIn('cat', classes)
        self.assertIn('dog', classes)
        self.assertIn('bird', classes)
    
    def test_project_dataset_linking(self):
        """测试项目数据集关联"""
        # 创建测试数据集
        dataset_id = create_dataset(
            self.test_db_path,
            name='Project Dataset',
            description='Dataset for project linking test',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        project_name = 'test_project'
        
        # 关联项目和数据集
        success = link_dataset_to_project(self.test_db_path, dataset_id, project_name)
        self.assertTrue(success)
        
        # 获取项目的数据集
        project_datasets = get_project_datasets(self.test_db_path, project_name)
        self.assertEqual(len(project_datasets), 1)
        self.assertEqual(project_datasets[0].dataset_id, dataset_id)
        
        # 解除关联
        success = unlink_dataset_from_project(self.test_db_path, dataset_id, project_name)
        self.assertTrue(success)
        
        # 验证解除关联
        project_datasets = get_project_datasets(self.test_db_path, project_name)
        self.assertEqual(len(project_datasets), 0)
    
    def test_duplicate_dataset_name(self):
        """测试重复数据集名称处理"""
        # 创建第一个数据集
        dataset_id1 = create_dataset(
            self.test_db_path,
            name='Duplicate Name',
            description='First dataset',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        self.assertIsNotNone(dataset_id1)
        
        # 尝试创建同名数据集，应该失败
        with self.assertRaises(Exception):
            create_dataset(
                self.test_db_path,
                name='Duplicate Name',
                description='Second dataset',
                dataset_type='custom',
                file_path=self.test_dataset_dir
            )
    
    def test_dataset_with_special_characters(self):
        """测试包含特殊字符的数据集"""
        special_name = "数据集 with 特殊字符 & symbols!"
        special_description = "描述 with émojis 🚀 and symbols @#$%"
        
        dataset_id = create_dataset(
            self.test_db_path,
            name=special_name,
            description=special_description,
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        self.assertIsNotNone(dataset_id)
        
        # 验证特殊字符正确保存
        dataset = get_dataset_by_id(self.test_db_path, dataset_id)
        self.assertEqual(dataset.name, special_name)
        self.assertEqual(dataset.description, special_description)
    
    def test_large_dataset_values(self):
        """测试大数值的数据集"""
        large_size = 1024 * 1024 * 1024 * 50  # 50GB
        large_image_count = 1000000  # 100万图片
        
        dataset_id = create_dataset(
            self.test_db_path,
            name='Large Dataset',
            description='Dataset with large values',
            dataset_type='downloaded',
            file_path=self.test_dataset_dir,
            file_size=large_size,
            image_count=large_image_count
        )
        
        self.assertIsNotNone(dataset_id)
        
        dataset = get_dataset_by_id(self.test_db_path, dataset_id)
        self.assertEqual(dataset.file_size, large_size)
        self.assertEqual(dataset.image_count, large_image_count)


if __name__ == '__main__':
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDatasetModel)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print(f"测试完成: 运行 {result.testsRun} 个测试")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split(chr(10))[-2]}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n总体结果: {'通过' if success else '失败'}")