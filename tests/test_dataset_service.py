#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集服务测试模块
测试数据集管理服务和分析服务的功能
"""

import unittest
import tempfile
import os
import shutil
import json
import zipfile
from unittest.mock import patch, MagicMock
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from visiofirm.utils.dataset_service import DatasetManager, DatasetAnalyzer
from visiofirm.models.dataset import init_dataset_tables


class TestDatasetManager(unittest.TestCase):
    """数据集管理器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, 'test_service.db')
        cls.datasets_dir = os.path.join(cls.temp_dir, 'datasets')
        os.makedirs(cls.datasets_dir, exist_ok=True)
        
        # 初始化测试数据库
        init_dataset_tables(cls.test_db_path)
        
        # 创建测试文件
        cls.create_test_files()
        
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def create_test_files(cls):
        """创建测试文件"""
        # 创建测试数据集目录
        cls.test_dataset_dir = os.path.join(cls.datasets_dir, 'test_dataset')
        os.makedirs(cls.test_dataset_dir, exist_ok=True)
        
        # 创建图片目录和文件
        images_dir = os.path.join(cls.test_dataset_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        test_images = ['cat1.jpg', 'cat2.png', 'dog1.jpg', 'dog2.jpeg', 'bird1.bmp']
        for img in test_images:
            with open(os.path.join(images_dir, img), 'wb') as f:
                f.write(b'fake image data')
        
        # 创建标注目录
        annotations_dir = os.path.join(cls.test_dataset_dir, 'annotations')
        os.makedirs(annotations_dir, exist_ok=True)
        
        # 创建YOLO格式标注文件
        for i, img in enumerate(test_images):
            txt_file = os.path.splitext(img)[0] + '.txt'
            with open(os.path.join(annotations_dir, txt_file), 'w') as f:
                f.write(f'{i % 3} 0.5 0.5 0.3 0.4\n')  # class_id x y w h
        
        # 创建类别文件
        with open(os.path.join(cls.test_dataset_dir, 'classes.txt'), 'w') as f:
            f.write('cat\ndog\nbird\n')
        
        # 创建COCO格式数据集
        cls.coco_dataset_dir = os.path.join(cls.datasets_dir, 'coco_dataset')
        os.makedirs(cls.coco_dataset_dir, exist_ok=True)
        
        coco_images_dir = os.path.join(cls.coco_dataset_dir, 'images')
        os.makedirs(coco_images_dir, exist_ok=True)
        
        for i in range(3):
            with open(os.path.join(coco_images_dir, f'image_{i}.jpg'), 'wb') as f:
                f.write(b'fake coco image data')
        
        # 创建COCO注释文件
        coco_annotation = {
            "images": [
                {"id": 1, "file_name": "image_0.jpg", "width": 640, "height": 480},
                {"id": 2, "file_name": "image_1.jpg", "width": 640, "height": 480},
                {"id": 3, "file_name": "image_2.jpg", "width": 640, "height": 480}
            ],
            "annotations": [
                {"id": 1, "image_id": 1, "category_id": 1, "bbox": [100, 100, 200, 150]},
                {"id": 2, "image_id": 2, "category_id": 2, "bbox": [150, 120, 180, 200]}
            ],
            "categories": [
                {"id": 1, "name": "cat"},
                {"id": 2, "name": "dog"}
            ]
        }
        
        with open(os.path.join(cls.coco_dataset_dir, 'annotations.json'), 'w') as f:
            json.dump(coco_annotation, f)
    
    def setUp(self):
        """每个测试方法的设置"""
        self.manager = DatasetManager(self.test_db_path, self.datasets_dir)
        
        # 清理数据库
        self.manager._execute_query('DELETE FROM Project_Datasets')
        self.manager._execute_query('DELETE FROM Dataset_Classes')
        self.manager._execute_query('DELETE FROM Datasets')
    
    def test_create_dataset_from_files(self):
        """测试从文件创建数据集"""
        image_files = [
            os.path.join(self.test_dataset_dir, 'images', 'cat1.jpg'),
            os.path.join(self.test_dataset_dir, 'images', 'dog1.jpg')
        ]
        
        dataset_id = self.manager.create_dataset_from_files(
            name='Test Upload Dataset',
            description='Dataset created from uploaded files',
            file_paths=image_files,
            dataset_type='custom'
        )
        
        self.assertIsNotNone(dataset_id)
        
        # 验证数据集已创建
        dataset = self.manager.get_dataset(dataset_id)
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.name, 'Test Upload Dataset')
        self.assertEqual(dataset.dataset_type, 'custom')
        self.assertGreater(dataset.file_size, 0)
    
    def test_import_existing_dataset(self):
        """测试导入现有数据集"""
        dataset_id = self.manager.import_existing_dataset(
            name='Imported YOLO Dataset',
            description='YOLO format dataset',
            dataset_path=self.test_dataset_dir
        )
        
        self.assertIsNotNone(dataset_id)
        
        # 验证数据集信息
        dataset = self.manager.get_dataset(dataset_id)
        self.assertEqual(dataset.name, 'Imported YOLO Dataset')
        self.assertEqual(dataset.annotation_format, 'yolo')
        self.assertEqual(dataset.image_count, 5)
        
        # 验证类别信息
        classes = self.manager.get_dataset_classes(dataset_id)
        self.assertEqual(len(classes), 3)
        self.assertIn('cat', classes)
        self.assertIn('dog', classes)
        self.assertIn('bird', classes)
    
    def test_get_datasets_with_pagination(self):
        """测试分页获取数据集"""
        # 创建多个数据集
        for i in range(15):
            self.manager.create_dataset_from_files(
                name=f'Dataset {i+1}',
                description=f'Test dataset number {i+1}',
                file_paths=[os.path.join(self.test_dataset_dir, 'images', 'cat1.jpg')],
                dataset_type='custom'
            )
        
        # 测试第一页
        datasets, total = self.manager.get_datasets(page=1, limit=10)
        self.assertEqual(len(datasets), 10)
        self.assertEqual(total, 15)
        
        # 测试第二页
        datasets, total = self.manager.get_datasets(page=2, limit=10)
        self.assertEqual(len(datasets), 5)
        self.assertEqual(total, 15)
        
        # 测试超出范围的页面
        datasets, total = self.manager.get_datasets(page=3, limit=10)
        self.assertEqual(len(datasets), 0)
        self.assertEqual(total, 15)
    
    def test_filter_datasets_by_type(self):
        """测试按类型筛选数据集"""
        # 创建不同类型的数据集
        custom_id = self.manager.create_dataset_from_files(
            name='Custom Dataset',
            description='Custom dataset',
            file_paths=[os.path.join(self.test_dataset_dir, 'images', 'cat1.jpg')],
            dataset_type='custom'
        )
        
        downloaded_id = self.manager.import_existing_dataset(
            name='Downloaded Dataset',
            description='Downloaded dataset',
            dataset_path=self.test_dataset_dir
        )
        
        # 修改第二个数据集类型为downloaded
        self.manager._execute_query(
            'UPDATE Datasets SET dataset_type = ? WHERE dataset_id = ?',
            ('downloaded', downloaded_id)
        )
        
        # 筛选custom类型
        custom_datasets, _ = self.manager.get_datasets(dataset_type='custom')
        self.assertEqual(len(custom_datasets), 1)
        self.assertEqual(custom_datasets[0].dataset_id, custom_id)
        
        # 筛选downloaded类型
        downloaded_datasets, _ = self.manager.get_datasets(dataset_type='downloaded')
        self.assertEqual(len(downloaded_datasets), 1)
        self.assertEqual(downloaded_datasets[0].dataset_id, downloaded_id)
    
    def test_search_datasets(self):
        """测试搜索数据集"""
        # 创建测试数据集
        dataset_ids = []
        datasets_info = [
            ('COCO Detection', 'Object detection with COCO format'),
            ('ImageNet Classification', 'Image classification dataset'),
            ('Custom Cat Dataset', 'Custom dataset with cat images'),
            ('Dog Breeds', 'Dataset for dog breed classification')
        ]
        
        for name, desc in datasets_info:
            dataset_id = self.manager.create_dataset_from_files(
                name=name,
                description=desc,
                file_paths=[os.path.join(self.test_dataset_dir, 'images', 'cat1.jpg')],
                dataset_type='custom'
            )
            dataset_ids.append(dataset_id)
        
        # 测试按名称搜索
        results, _ = self.manager.search_datasets('COCO')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'COCO Detection')
        
        # 测试按描述搜索
        results, _ = self.manager.search_datasets('classification')
        self.assertEqual(len(results), 2)  # ImageNet Classification, Dog Breeds
        
        # 测试不区分大小写
        results, _ = self.manager.search_datasets('cat')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Custom Cat Dataset')
    
    def test_link_dataset_to_project(self):
        """测试关联数据集到项目"""
        # 创建测试数据集
        dataset_id = self.manager.create_dataset_from_files(
            name='Project Dataset',
            description='Dataset for project linking',
            file_paths=[os.path.join(self.test_dataset_dir, 'images', 'cat1.jpg')],
            dataset_type='custom'
        )
        
        project_name = 'test_project'
        
        # 关联数据集到项目
        success = self.manager.link_dataset_to_project(dataset_id, project_name)
        self.assertTrue(success)
        
        # 验证关联
        project_datasets = self.manager.get_project_datasets(project_name)
        self.assertEqual(len(project_datasets), 1)
        self.assertEqual(project_datasets[0].dataset_id, dataset_id)
        
        # 测试重复关联
        success = self.manager.link_dataset_to_project(dataset_id, project_name)
        self.assertTrue(success)  # 应该仍然成功，但不重复创建
        
        project_datasets = self.manager.get_project_datasets(project_name)
        self.assertEqual(len(project_datasets), 1)  # 仍然只有一个
    
    def test_delete_dataset(self):
        """测试删除数据集"""
        # 创建测试数据集
        dataset_id = self.manager.create_dataset_from_files(
            name='Dataset to Delete',
            description='This dataset will be deleted',
            file_paths=[os.path.join(self.test_dataset_dir, 'images', 'cat1.jpg')],
            dataset_type='custom'
        )
        
        # 验证数据集存在
        dataset = self.manager.get_dataset(dataset_id)
        self.assertIsNotNone(dataset)
        
        # 删除数据集
        success = self.manager.delete_dataset(dataset_id)
        self.assertTrue(success)
        
        # 验证数据集已删除
        dataset = self.manager.get_dataset(dataset_id)
        self.assertIsNone(dataset)


class TestDatasetAnalyzer(unittest.TestCase):
    """数据集分析器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.create_test_datasets()
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def create_test_datasets(cls):
        """创建测试数据集"""
        # YOLO格式数据集
        cls.yolo_dir = os.path.join(cls.temp_dir, 'yolo_dataset')
        os.makedirs(cls.yolo_dir, exist_ok=True)
        
        images_dir = os.path.join(cls.yolo_dir, 'images')
        labels_dir = os.path.join(cls.yolo_dir, 'labels')
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(labels_dir, exist_ok=True)
        
        # 创建图片和标注文件
        for i in range(5):
            # 图片文件
            with open(os.path.join(images_dir, f'image_{i}.jpg'), 'wb') as f:
                f.write(b'fake image data')
            
            # YOLO标注文件
            with open(os.path.join(labels_dir, f'image_{i}.txt'), 'w') as f:
                f.write(f'{i % 3} 0.5 0.5 0.3 0.4\n')
        
        # 类别文件
        with open(os.path.join(cls.yolo_dir, 'classes.txt'), 'w') as f:
            f.write('cat\ndog\nbird\n')
        
        # COCO格式数据集
        cls.coco_dir = os.path.join(cls.temp_dir, 'coco_dataset')
        os.makedirs(cls.coco_dir, exist_ok=True)
        
        coco_images_dir = os.path.join(cls.coco_dir, 'images')
        os.makedirs(coco_images_dir, exist_ok=True)
        
        for i in range(3):
            with open(os.path.join(coco_images_dir, f'image_{i}.jpg'), 'wb') as f:
                f.write(b'fake coco image')
        
        # COCO注释文件
        coco_annotation = {
            "images": [
                {"id": 1, "file_name": "image_0.jpg"},
                {"id": 2, "file_name": "image_1.jpg"},
                {"id": 3, "file_name": "image_2.jpg"}
            ],
            "categories": [
                {"id": 1, "name": "person"},
                {"id": 2, "name": "car"}
            ]
        }
        
        with open(os.path.join(cls.coco_dir, 'annotations.json'), 'w') as f:
            json.dump(coco_annotation, f)
        
        # 无标注数据集
        cls.plain_dir = os.path.join(cls.temp_dir, 'plain_dataset')
        os.makedirs(cls.plain_dir, exist_ok=True)
        
        for i in range(4):
            with open(os.path.join(cls.plain_dir, f'photo_{i}.png'), 'wb') as f:
                f.write(b'plain image data')
    
    def setUp(self):
        """每个测试方法的设置"""
        self.analyzer = DatasetAnalyzer()
    
    def test_detect_yolo_format(self):
        """测试检测YOLO格式"""
        format_info = self.analyzer.detect_annotation_format(self.yolo_dir)
        
        self.assertEqual(format_info['format'], 'yolo')
        self.assertTrue(format_info['has_annotations'])
        self.assertGreater(len(format_info['structure']), 0)
    
    def test_detect_coco_format(self):
        """测试检测COCO格式"""
        format_info = self.analyzer.detect_annotation_format(self.coco_dir)
        
        self.assertEqual(format_info['format'], 'coco')
        self.assertTrue(format_info['has_annotations'])
        self.assertIn('annotations.json', format_info['structure'])
    
    def test_detect_plain_format(self):
        """测试检测无标注格式"""
        format_info = self.analyzer.detect_annotation_format(self.plain_dir)
        
        self.assertEqual(format_info['format'], 'none')
        self.assertFalse(format_info['has_annotations'])
    
    def test_count_images(self):
        """测试图片计数"""
        yolo_count = self.analyzer.count_images(self.yolo_dir)
        self.assertEqual(yolo_count, 5)
        
        coco_count = self.analyzer.count_images(self.coco_dir)
        self.assertEqual(coco_count, 3)
        
        plain_count = self.analyzer.count_images(self.plain_dir)
        self.assertEqual(plain_count, 4)
    
    def test_extract_yolo_classes(self):
        """测试提取YOLO类别"""
        classes = self.analyzer.extract_classes(self.yolo_dir, 'yolo')
        
        self.assertEqual(len(classes), 3)
        self.assertIn('cat', classes)
        self.assertIn('dog', classes)
        self.assertIn('bird', classes)
    
    def test_extract_coco_classes(self):
        """测试提取COCO类别"""
        classes = self.analyzer.extract_classes(self.coco_dir, 'coco')
        
        self.assertEqual(len(classes), 2)
        self.assertIn('person', classes)
        self.assertIn('car', classes)
    
    def test_analyze_dataset_structure(self):
        """测试分析数据集结构"""
        # 分析YOLO数据集
        yolo_analysis = self.analyzer.analyze_structure(self.yolo_dir)
        
        self.assertEqual(yolo_analysis['format'], 'yolo')
        self.assertEqual(yolo_analysis['image_count'], 5)
        self.assertEqual(yolo_analysis['class_count'], 3)
        self.assertIn('cat', yolo_analysis['classes'])
        
        # 分析COCO数据集
        coco_analysis = self.analyzer.analyze_structure(self.coco_dir)
        
        self.assertEqual(coco_analysis['format'], 'coco')
        self.assertEqual(coco_analysis['image_count'], 3)
        self.assertEqual(coco_analysis['class_count'], 2)
        self.assertIn('person', coco_analysis['classes'])
    
    def test_calculate_dataset_size(self):
        """测试计算数据集大小"""
        yolo_size = self.analyzer.calculate_dataset_size(self.yolo_dir)
        self.assertGreater(yolo_size, 0)
        
        coco_size = self.analyzer.calculate_dataset_size(self.coco_dir)
        self.assertGreater(coco_size, 0)
    
    def test_validate_dataset_structure(self):
        """测试验证数据集结构"""
        # 验证YOLO数据集
        yolo_validation = self.analyzer.validate_dataset_structure(self.yolo_dir, 'yolo')
        self.assertTrue(yolo_validation['valid'])
        self.assertEqual(len(yolo_validation['errors']), 0)
        
        # 验证COCO数据集
        coco_validation = self.analyzer.validate_dataset_structure(self.coco_dir, 'coco')
        self.assertTrue(coco_validation['valid'])
        self.assertEqual(len(coco_validation['errors']), 0)
        
        # 验证无标注数据集
        plain_validation = self.analyzer.validate_dataset_structure(self.plain_dir, 'none')
        self.assertTrue(plain_validation['valid'])
    
    def test_extract_dataset_metadata(self):
        """测试提取数据集元数据"""
        metadata = self.analyzer.extract_dataset_metadata(self.yolo_dir)
        
        self.assertIn('total_size', metadata)
        self.assertIn('image_formats', metadata)
        self.assertIn('directory_structure', metadata)
        self.assertGreater(metadata['total_size'], 0)
        self.assertIn('.jpg', metadata['image_formats'])


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加DatasetManager测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatasetManager))
    
    # 添加DatasetAnalyzer测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatasetAnalyzer))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print(f"数据集服务测试完成: 运行 {result.testsRun} 个测试")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n总体结果: {'通过' if success else '失败'}")