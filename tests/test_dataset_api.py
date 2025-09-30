#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集API测试模块
测试数据集相关的Flask API端点
"""

import unittest
import tempfile
import os
import shutil
import json
import sqlite3
from unittest.mock import patch, MagicMock
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from visiofirm import create_app
from visiofirm.models.dataset import init_dataset_tables, create_dataset
from visiofirm.config import Config


class TestDatasetAPI(unittest.TestCase):
    """数据集API测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        # 创建临时目录
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, 'test_api.db')
        cls.projects_dir = os.path.join(cls.temp_dir, 'projects')
        cls.datasets_dir = os.path.join(cls.projects_dir, 'datasets')
        
        os.makedirs(cls.projects_dir, exist_ok=True)
        os.makedirs(cls.datasets_dir, exist_ok=True)
        
        # 创建测试配置
        cls.create_test_config()
        
        # 初始化数据库
        init_dataset_tables(cls.test_db_path)
        
        # 创建测试数据集文件
        cls.create_test_dataset_files()
        
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def create_test_config(cls):
        """创建测试配置"""
        class TestConfig(Config):
            TESTING = True
            WTF_CSRF_ENABLED = False
            SECRET_KEY = 'test-secret-key'
            DATABASE_PATH = cls.test_db_path
            PROJECTS_FOLDER = cls.projects_dir
            DATASETS_FOLDER = cls.datasets_dir
            LOGIN_DISABLED = True  # 禁用登录要求
        
        cls.test_config = TestConfig
    
    @classmethod
    def create_test_dataset_files(cls):
        """创建测试数据集文件"""
        # 创建测试数据集目录
        cls.test_dataset_dir = os.path.join(cls.datasets_dir, 'test_dataset')
        os.makedirs(cls.test_dataset_dir, exist_ok=True)
        
        # 创建图片目录
        images_dir = os.path.join(cls.test_dataset_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # 创建测试图片文件
        test_images = ['cat1.jpg', 'cat2.png', 'dog1.jpg', 'dog2.jpeg']
        for img in test_images:
            img_path = os.path.join(images_dir, img)
            with open(img_path, 'wb') as f:
                f.write(b'fake image data for testing')
        
        # 创建标注目录
        annotations_dir = os.path.join(cls.test_dataset_dir, 'annotations')
        os.makedirs(annotations_dir, exist_ok=True)
        
        # 创建YOLO格式标注文件
        for img in test_images:
            txt_file = os.path.splitext(img)[0] + '.txt'
            with open(os.path.join(annotations_dir, txt_file), 'w') as f:
                f.write('0 0.5 0.5 0.3 0.4\n')  # class_id x y w h
        
        # 创建类别文件
        with open(os.path.join(cls.test_dataset_dir, 'classes.txt'), 'w') as f:
            f.write('cat\ndog\n')
        
        # 创建用于上传测试的图片文件
        cls.upload_test_files = []
        upload_dir = os.path.join(cls.temp_dir, 'upload_files')
        os.makedirs(upload_dir, exist_ok=True)
        
        for i in range(3):
            file_path = os.path.join(upload_dir, f'upload_image_{i}.jpg')
            with open(file_path, 'wb') as f:
                f.write(b'test upload image data')
            cls.upload_test_files.append(file_path)
    
    def setUp(self):
        """每个测试方法的设置"""
        # 创建Flask应用
        self.app = create_app(self.test_config)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # 清理数据库
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Project_Datasets')
            cursor.execute('DELETE FROM Dataset_Classes')
            cursor.execute('DELETE FROM Datasets')
            conn.commit()
    
    def tearDown(self):
        """每个测试方法的清理"""
        self.app_context.pop()
    
    def test_list_datasets_empty(self):
        """测试获取空数据集列表"""
        response = self.client.get('/datasets/api/list')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 0)
        self.assertEqual(len(data['datasets']), 0)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 20)
    
    def test_list_datasets_with_data(self):
        """测试获取数据集列表"""
        # 创建测试数据集
        dataset_ids = []
        for i in range(5):
            dataset_id = create_dataset(
                self.test_db_path,
                name=f'Test Dataset {i+1}',
                description=f'Test dataset number {i+1}',
                dataset_type='custom',
                file_path=self.test_dataset_dir,
                image_count=4,
                class_count=2
            )
            dataset_ids.append(dataset_id)
        
        # 测试获取所有数据集
        response = self.client.get('/datasets/api/list')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 5)
        self.assertEqual(len(data['datasets']), 5)
        
        # 验证数据集信息
        dataset_names = [d['name'] for d in data['datasets']]
        self.assertIn('Test Dataset 1', dataset_names)
        self.assertIn('Test Dataset 5', dataset_names)
    
    def test_list_datasets_pagination(self):
        """测试数据集列表分页"""
        # 创建10个测试数据集
        for i in range(10):
            create_dataset(
                self.test_db_path,
                name=f'Dataset {i+1:02d}',
                description=f'Dataset number {i+1}',
                dataset_type='custom',
                file_path=self.test_dataset_dir
            )
        
        # 测试第一页
        response = self.client.get('/datasets/api/list?page=1&limit=4')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 10)
        self.assertEqual(len(data['datasets']), 4)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 4)
        
        # 测试第二页
        response = self.client.get('/datasets/api/list?page=2&limit=4')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['datasets']), 4)
        self.assertEqual(data['page'], 2)
        
        # 测试最后一页
        response = self.client.get('/datasets/api/list?page=3&limit=4')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['datasets']), 2)
        self.assertEqual(data['page'], 3)
    
    def test_list_datasets_filter_by_type(self):
        """测试按类型筛选数据集"""
        # 创建不同类型的数据集
        create_dataset(
            self.test_db_path,
            name='Custom Dataset',
            description='Custom dataset',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        create_dataset(
            self.test_db_path,
            name='Downloaded Dataset',
            description='Downloaded dataset',
            dataset_type='downloaded',
            file_path=self.test_dataset_dir
        )
        
        create_dataset(
            self.test_db_path,
            name='Imported Dataset',
            description='Imported dataset',
            dataset_type='imported',
            file_path=self.test_dataset_dir
        )
        
        # 筛选custom类型
        response = self.client.get('/datasets/api/list?type=custom')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['datasets'][0]['name'], 'Custom Dataset')
        
        # 筛选downloaded类型
        response = self.client.get('/datasets/api/list?type=downloaded')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['datasets'][0]['name'], 'Downloaded Dataset')
    
    def test_get_dataset_detail(self):
        """测试获取数据集详情"""
        # 创建测试数据集
        dataset_id = create_dataset(
            self.test_db_path,
            name='Detail Test Dataset',
            description='Dataset for testing detail API',
            dataset_type='custom',
            file_path=self.test_dataset_dir,
            file_size=2048000,
            image_count=4,
            class_count=2,
            annotation_format='yolo'
        )
        
        # 获取数据集详情
        response = self.client.get(f'/datasets/api/detail/{dataset_id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['dataset_id'], dataset_id)
        self.assertEqual(data['name'], 'Detail Test Dataset')
        self.assertEqual(data['description'], 'Dataset for testing detail API')
        self.assertEqual(data['dataset_type'], 'custom')
        self.assertEqual(data['file_size'], 2048000)
        self.assertEqual(data['image_count'], 4)
        self.assertEqual(data['class_count'], 2)
        self.assertEqual(data['annotation_format'], 'yolo')
    
    def test_get_nonexistent_dataset_detail(self):
        """测试获取不存在的数据集详情"""
        response = self.client.get('/datasets/api/detail/99999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('not found', data['error'].lower())
    
    def test_search_datasets(self):
        """测试搜索数据集"""
        # 创建测试数据集
        datasets_info = [
            ('COCO Detection Dataset', 'Object detection with COCO format'),
            ('ImageNet Classification', 'Image classification dataset'),
            ('Custom Cat Dataset', 'Custom dataset with cat images'),
            ('Dog Breeds Dataset', 'Dataset for dog breed classification')
        ]
        
        for name, desc in datasets_info:
            create_dataset(
                self.test_db_path,
                name=name,
                description=desc,
                dataset_type='custom',
                file_path=self.test_dataset_dir
            )
        
        # 搜索"COCO"
        response = self.client.get('/datasets/api/search?q=COCO')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['datasets'][0]['name'], 'COCO Detection Dataset')
        
        # 搜索"classification"
        response = self.client.get('/datasets/api/search?q=classification')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 2)  # ImageNet Classification, Dog Breeds Dataset
        
        # 搜索"cat"（不区分大小写）
        response = self.client.get('/datasets/api/search?q=cat')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['datasets'][0]['name'], 'Custom Cat Dataset')
    
    def test_search_datasets_empty_query(self):
        """测试空查询搜索数据集"""
        response = self.client.get('/datasets/api/search')
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    @patch('visiofirm.utils.dataset_service.DatasetManager.create_dataset_from_files')
    def test_create_dataset_from_upload(self, mock_create):
        """测试从上传文件创建数据集"""
        mock_create.return_value = 123
        
        # 准备上传数据
        data = {
            'name': 'Uploaded Dataset',
            'description': 'Dataset created from uploaded files',
            'dataset_type': 'custom'
        }
        
        # 模拟文件上传
        with open(self.upload_test_files[0], 'rb') as f:
            data['files'] = [
                (f, 'test_image.jpg')
            ]
            
            response = self.client.post(
                '/datasets/api/create',
                data=data,
                content_type='multipart/form-data'
            )
        
        self.assertEqual(response.status_code, 201)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['dataset_id'], 123)
        self.assertIn('success', response_data['message'].lower())
    
    def test_create_dataset_missing_fields(self):
        """测试创建数据集缺少必填字段"""
        # 缺少名称
        data = {
            'description': 'Dataset without name',
            'dataset_type': 'custom'
        }
        
        response = self.client.post('/datasets/api/create', data=data)
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
    
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
        
        # 删除数据集
        response = self.client.delete(f'/datasets/api/delete/{dataset_id}')
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('success', response_data['message'].lower())
        
        # 验证数据集已删除
        response = self.client.get(f'/datasets/api/detail/{dataset_id}')
        self.assertEqual(response.status_code, 404)
    
    def test_delete_nonexistent_dataset(self):
        """测试删除不存在的数据集"""
        response = self.client.delete('/datasets/api/delete/99999')
        self.assertEqual(response.status_code, 404)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
    
    def test_link_dataset_to_project(self):
        """测试关联数据集到项目"""
        # 创建测试数据集
        dataset_id = create_dataset(
            self.test_db_path,
            name='Project Dataset',
            description='Dataset for project linking',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        # 关联到项目
        data = {'project_name': 'test_project'}
        response = self.client.post(
            f'/datasets/api/link/{dataset_id}',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('success', response_data['message'].lower())
    
    def test_link_nonexistent_dataset_to_project(self):
        """测试关联不存在的数据集到项目"""
        data = {'project_name': 'test_project'}
        response = self.client.post(
            '/datasets/api/link/99999',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_unlink_dataset_from_project(self):
        """测试解除数据集与项目的关联"""
        # 创建测试数据集并关联到项目
        dataset_id = create_dataset(
            self.test_db_path,
            name='Linked Dataset',
            description='Dataset linked to project',
            dataset_type='custom',
            file_path=self.test_dataset_dir
        )
        
        # 先关联
        data = {'project_name': 'test_project'}
        self.client.post(
            f'/datasets/api/link/{dataset_id}',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # 解除关联
        response = self.client.post(
            f'/datasets/api/unlink/{dataset_id}',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('success', response_data['message'].lower())
    
    @patch('visiofirm.utils.dataset_downloader.DatasetDownloader.start_download')
    def test_download_dataset(self, mock_download):
        """测试下载数据集"""
        mock_download.return_value = 'download_task_123'
        
        data = {
            'url': 'https://example.com/dataset.zip',
            'name': 'Downloaded Dataset',
            'description': 'Dataset downloaded from URL'
        }
        
        response = self.client.post(
            '/datasets/api/download',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 202)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['task_id'], 'download_task_123')
        self.assertIn('started', response_data['message'].lower())
    
    def test_download_dataset_missing_url(self):
        """测试下载数据集缺少URL"""
        data = {
            'name': 'Dataset without URL',
            'description': 'Missing URL'
        }
        
        response = self.client.post(
            '/datasets/api/download',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
    
    @patch('visiofirm.utils.dataset_downloader.DatasetDownloader.get_download_progress')
    def test_get_download_progress(self, mock_progress):
        """测试获取下载进度"""
        mock_progress.return_value = {
            'status': 'downloading',
            'progress': 45.5,
            'downloaded_size': 11776000000,
            'total_size': 25600000000,
            'speed': '15.2 MB/s',
            'eta': '00:15:23',
            'message': '正在下载数据集文件...'
        }
        
        response = self.client.get('/datasets/api/download/progress/download_task_123')
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertEqual(response_data['status'], 'downloading')
        self.assertEqual(response_data['progress'], 45.5)
        self.assertEqual(response_data['speed'], '15.2 MB/s')
    
    def test_get_download_progress_invalid_task(self):
        """测试获取无效下载任务的进度"""
        response = self.client.get('/datasets/api/download/progress/invalid_task')
        self.assertEqual(response.status_code, 404)
        
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
    
    def test_api_error_handling(self):
        """测试API错误处理"""
        # 测试无效的JSON数据
        response = self.client.post(
            '/datasets/api/link/1',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        
        # 测试不支持的HTTP方法
        response = self.client.patch('/datasets/api/list')
        self.assertEqual(response.status_code, 405)


class TestDatasetRouteIntegration(unittest.TestCase):
    """数据集路由集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, 'test_integration.db')
        cls.projects_dir = os.path.join(cls.temp_dir, 'projects')
        cls.datasets_dir = os.path.join(cls.projects_dir, 'datasets')
        
        os.makedirs(cls.projects_dir, exist_ok=True)
        os.makedirs(cls.datasets_dir, exist_ok=True)
        
        # 创建测试配置
        class TestConfig(Config):
            TESTING = True
            WTF_CSRF_ENABLED = False
            SECRET_KEY = 'test-secret-key'
            DATABASE_PATH = cls.test_db_path
            PROJECTS_FOLDER = cls.projects_dir
            DATASETS_FOLDER = cls.datasets_dir
            LOGIN_DISABLED = True
        
        cls.test_config = TestConfig
        
        # 初始化数据库
        init_dataset_tables(cls.test_db_path)
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """每个测试方法的设置"""
        self.app = create_app(self.test_config)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """每个测试方法的清理"""
        self.app_context.pop()
    
    def test_dataset_main_page(self):
        """测试数据集主页面"""
        response = self.client.get('/datasets/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'datasets', response.data.lower())
    
    def test_dataset_api_endpoints_exist(self):
        """测试数据集API端点存在"""
        # 测试列表端点
        response = self.client.get('/datasets/api/list')
        self.assertNotEqual(response.status_code, 404)
        
        # 测试搜索端点
        response = self.client.get('/datasets/api/search?q=test')
        self.assertNotEqual(response.status_code, 404)
    
    def test_end_to_end_dataset_workflow(self):
        """测试端到端数据集工作流程"""
        # 1. 获取初始空列表
        response = self.client.get('/datasets/api/list')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 0)
        
        # 2. 创建数据集（模拟）
        dataset_id = create_dataset(
            self.test_db_path,
            name='E2E Test Dataset',
            description='End-to-end test dataset',
            dataset_type='custom',
            file_path='/fake/path'
        )
        
        # 3. 验证数据集出现在列表中
        response = self.client.get('/datasets/api/list')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['datasets'][0]['name'], 'E2E Test Dataset')
        
        # 4. 获取数据集详情
        response = self.client.get(f'/datasets/api/detail/{dataset_id}')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['name'], 'E2E Test Dataset')
        
        # 5. 搜索数据集
        response = self.client.get('/datasets/api/search?q=E2E')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        
        # 6. 删除数据集
        response = self.client.delete(f'/datasets/api/delete/{dataset_id}')
        self.assertEqual(response.status_code, 200)
        
        # 7. 验证数据集已删除
        response = self.client.get('/datasets/api/list')
        data = json.loads(response.data)
        self.assertEqual(data['total'], 0)


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加API测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatasetAPI))
    
    # 添加集成测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatasetRouteIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print(f"数据集API测试完成: 运行 {result.testsRun} 个测试")
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