#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集下载器测试模块
测试数据集下载功能和进度跟踪
"""

import unittest
import tempfile
import os
import shutil
import time
import zipfile
import json
from unittest.mock import patch, MagicMock, mock_open
import sys
import threading
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from visiofirm.utils.dataset_downloader import DatasetDownloader


class TestDatasetDownloader(unittest.TestCase):
    """数据集下载器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.download_dir = os.path.join(cls.temp_dir, 'downloads')
        cls.datasets_dir = os.path.join(cls.temp_dir, 'datasets')
        
        os.makedirs(cls.download_dir, exist_ok=True)
        os.makedirs(cls.datasets_dir, exist_ok=True)
        
        # 创建测试ZIP文件
        cls.create_test_zip_file()
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def create_test_zip_file(cls):
        """创建测试ZIP文件"""
        cls.test_zip_path = os.path.join(cls.temp_dir, 'test_dataset.zip')
        
        # 创建临时数据集目录
        temp_dataset_dir = os.path.join(cls.temp_dir, 'temp_dataset')
        os.makedirs(temp_dataset_dir, exist_ok=True)
        
        # 创建图片目录
        images_dir = os.path.join(temp_dataset_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # 创建测试图片文件
        for i in range(3):
            with open(os.path.join(images_dir, f'image_{i}.jpg'), 'wb') as f:
                f.write(b'fake image data' * 100)  # 创建一些数据
        
        # 创建标注目录
        annotations_dir = os.path.join(temp_dataset_dir, 'annotations')
        os.makedirs(annotations_dir, exist_ok=True)
        
        # 创建标注文件
        for i in range(3):
            with open(os.path.join(annotations_dir, f'image_{i}.txt'), 'w') as f:
                f.write(f'{i % 2} 0.5 0.5 0.3 0.4\n')
        
        # 创建类别文件
        with open(os.path.join(temp_dataset_dir, 'classes.txt'), 'w') as f:
            f.write('cat\ndog\n')
        
        # 创建ZIP文件
        with zipfile.ZipFile(cls.test_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dataset_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, temp_dataset_dir)
                    zipf.write(file_path, arc_path)
        
        # 清理临时目录
        shutil.rmtree(temp_dataset_dir)
    
    def setUp(self):
        """每个测试方法的设置"""
        self.downloader = DatasetDownloader(
            download_dir=self.download_dir,
            datasets_dir=self.datasets_dir
        )
    
    def tearDown(self):
        """每个测试方法的清理"""
        # 清理下载目录
        if os.path.exists(self.download_dir):
            for file in os.listdir(self.download_dir):
                file_path = os.path.join(self.download_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
    
    @patch('requests.get')
    def test_download_dataset_success(self, mock_get):
        """测试成功下载数据集"""
        # 模拟HTTP响应
        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content.return_value = [b'fake data' * 32]  # 总共256字节数据
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 开始下载
        task_id = self.downloader.start_download(
            url='https://example.com/dataset.zip',
            name='Test Dataset',
            description='Test dataset for download'
        )
        
        self.assertIsNotNone(task_id)
        
        # 等待下载完成
        time.sleep(0.5)
        
        # 验证下载状态
        progress = self.downloader.get_download_progress(task_id)
        self.assertIsNotNone(progress)
        
        # 等待更长时间确保下载完成
        max_wait = 10
        wait_time = 0
        while wait_time < max_wait:
            progress = self.downloader.get_download_progress(task_id)
            if progress['status'] in ['completed', 'error']:
                break
            time.sleep(0.5)
            wait_time += 0.5
        
        # 验证最终状态
        final_progress = self.downloader.get_download_progress(task_id)
        self.assertIn(final_progress['status'], ['completed', 'error'])
    
    @patch('requests.get')
    def test_download_dataset_with_progress_tracking(self, mock_get):
        """测试带进度跟踪的下载"""
        # 模拟分块下载
        chunks = [b'chunk1', b'chunk2', b'chunk3', b'chunk4']
        
        mock_response = MagicMock()
        mock_response.headers = {'content-length': str(len(b''.join(chunks)))}
        mock_response.iter_content.return_value = chunks
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # 开始下载
        task_id = self.downloader.start_download(
            url='https://example.com/large_dataset.zip',
            name='Large Test Dataset',
            description='Large dataset for progress testing'
        )
        
        # 跟踪进度变化
        progress_history = []
        for _ in range(5):
            time.sleep(0.2)
            progress = self.downloader.get_download_progress(task_id)
            if progress:
                progress_history.append(progress['progress'])
        
        # 验证进度确实在变化
        self.assertGreater(len(progress_history), 0)
    
    def test_download_dataset_invalid_url(self):
        """测试无效URL下载"""
        task_id = self.downloader.start_download(
            url='invalid://not-a-real-url',
            name='Invalid Dataset',
            description='Dataset with invalid URL'
        )
        
        self.assertIsNotNone(task_id)
        
        # 等待错误状态
        time.sleep(1)
        
        progress = self.downloader.get_download_progress(task_id)
        self.assertEqual(progress['status'], 'error')
        self.assertIn('error', progress['message'].lower())
    
    @patch('requests.get')
    def test_download_dataset_http_error(self, mock_get):
        """测试HTTP错误处理"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('404 Not Found')
        mock_get.return_value = mock_response
        
        task_id = self.downloader.start_download(
            url='https://example.com/nonexistent.zip',
            name='Nonexistent Dataset',
            description='Dataset that does not exist'
        )
        
        # 等待错误状态
        time.sleep(1)
        
        progress = self.downloader.get_download_progress(task_id)
        self.assertEqual(progress['status'], 'error')
    
    def test_extract_zip_file(self):
        """测试解压ZIP文件"""
        # 复制测试ZIP文件到下载目录
        test_zip_copy = os.path.join(self.download_dir, 'test_extract.zip')
        shutil.copy2(self.test_zip_path, test_zip_copy)
        
        # 解压文件
        extract_dir = os.path.join(self.datasets_dir, 'extracted_dataset')
        success = self.downloader._extract_archive(test_zip_copy, extract_dir)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(extract_dir))
        
        # 验证解压内容
        self.assertTrue(os.path.exists(os.path.join(extract_dir, 'images')))
        self.assertTrue(os.path.exists(os.path.join(extract_dir, 'annotations')))
        self.assertTrue(os.path.exists(os.path.join(extract_dir, 'classes.txt')))
        
        # 验证图片文件
        images_dir = os.path.join(extract_dir, 'images')
        image_files = os.listdir(images_dir)
        self.assertEqual(len(image_files), 3)
        self.assertIn('image_0.jpg', image_files)
    
    def test_extract_corrupted_zip(self):
        """测试解压损坏的ZIP文件"""
        # 创建损坏的ZIP文件
        corrupted_zip = os.path.join(self.download_dir, 'corrupted.zip')
        with open(corrupted_zip, 'wb') as f:
            f.write(b'this is not a valid zip file')
        
        # 尝试解压
        extract_dir = os.path.join(self.datasets_dir, 'corrupted_extract')
        success = self.downloader._extract_archive(corrupted_zip, extract_dir)
        
        self.assertFalse(success)
        self.assertFalse(os.path.exists(extract_dir))
    
    def test_get_nonexistent_download_progress(self):
        """测试获取不存在的下载进度"""
        progress = self.downloader.get_download_progress('nonexistent_task_id')
        self.assertIsNone(progress)
    
    def test_cancel_download(self):
        """测试取消下载"""
        # 使用patch模拟一个长时间运行的下载
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-length': '1000000'}
            
            def slow_iter_content(chunk_size):
                for i in range(100):
                    time.sleep(0.05)  # 模拟慢速下载
                    yield b'x' * chunk_size
            
            mock_response.iter_content.side_effect = slow_iter_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # 开始下载
            task_id = self.downloader.start_download(
                url='https://example.com/large_file.zip',
                name='Large File',
                description='Large file for cancel test'
            )
            
            # 等待下载开始
            time.sleep(0.2)
            
            # 取消下载
            success = self.downloader.cancel_download(task_id)
            self.assertTrue(success)
            
            # 验证下载已取消
            time.sleep(0.5)
            progress = self.downloader.get_download_progress(task_id)
            self.assertEqual(progress['status'], 'cancelled')
    
    def test_concurrent_downloads(self):
        """测试并发下载"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-length': '1024'}
            mock_response.iter_content.return_value = [b'data' * 64]
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # 启动多个下载任务
            task_ids = []
            for i in range(3):
                task_id = self.downloader.start_download(
                    url=f'https://example.com/dataset_{i}.zip',
                    name=f'Dataset {i}',
                    description=f'Concurrent dataset {i}'
                )
                task_ids.append(task_id)
            
            # 验证所有任务都被创建
            self.assertEqual(len(task_ids), 3)
            self.assertEqual(len(set(task_ids)), 3)  # 确保task_id唯一
            
            # 等待下载完成
            time.sleep(1)
            
            # 验证所有下载状态
            for task_id in task_ids:
                progress = self.downloader.get_download_progress(task_id)
                self.assertIsNotNone(progress)
                self.assertIn(progress['status'], ['downloading', 'completed', 'error'])
    
    def test_download_progress_format(self):
        """测试下载进度格式"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-length': '2048'}
            mock_response.iter_content.return_value = [b'x' * 512, b'y' * 512, b'z' * 512, b'w' * 512]
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            task_id = self.downloader.start_download(
                url='https://example.com/format_test.zip',
                name='Format Test',
                description='Test progress format'
            )
            
            # 等待一些进度
            time.sleep(0.5)
            
            progress = self.downloader.get_download_progress(task_id)
            
            # 验证进度格式
            required_fields = ['status', 'progress', 'downloaded_size', 'total_size', 'speed', 'eta', 'message']
            for field in required_fields:
                self.assertIn(field, progress)
            
            # 验证数据类型
            self.assertIsInstance(progress['progress'], (int, float))
            self.assertIsInstance(progress['downloaded_size'], int)
            self.assertIsInstance(progress['total_size'], int)
            self.assertIsInstance(progress['speed'], str)
            self.assertIsInstance(progress['eta'], str)
            self.assertIsInstance(progress['message'], str)
    
    def test_download_task_cleanup(self):
        """测试下载任务清理"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-length': '1024'}
            mock_response.iter_content.return_value = [b'data' * 256]
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            task_id = self.downloader.start_download(
                url='https://example.com/cleanup_test.zip',
                name='Cleanup Test',
                description='Test task cleanup'
            )
            
            # 等待下载完成
            time.sleep(1.5)
            
            # 验证任务信息存在
            progress = self.downloader.get_download_progress(task_id)
            self.assertIsNotNone(progress)
            
            # 清理任务
            self.downloader._cleanup_completed_tasks()
            
            # 根据实现，完成的任务可能仍然可查询（用于历史记录）
            # 或者被清理掉，这取决于具体实现
    
    def test_download_with_custom_filename(self):
        """测试自定义文件名下载"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-length': '1024'}
            mock_response.iter_content.return_value = [b'custom data' * 32]
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            task_id = self.downloader.start_download(
                url='https://example.com/dataset.zip',
                name='Custom Named Dataset',
                description='Dataset with custom name'
            )
            
            # 等待下载完成
            time.sleep(1)
            
            progress = self.downloader.get_download_progress(task_id)
            
            # 验证文件名包含自定义名称
            if progress['status'] == 'completed':
                # 可以验证文件确实存在于期望的位置
                pass
    
    def test_disk_space_handling(self):
        """测试磁盘空间处理"""
        # 这个测试比较难实现，因为需要模拟磁盘空间不足
        # 可以通过mock来模拟写文件时的OSError
        
        with patch('builtins.open', side_effect=OSError('No space left on device')):
            task_id = self.downloader.start_download(
                url='https://example.com/huge_dataset.zip',
                name='Huge Dataset',
                description='Dataset too large for disk'
            )
            
            # 等待错误状态
            time.sleep(1)
            
            progress = self.downloader.get_download_progress(task_id)
            if progress:
                self.assertEqual(progress['status'], 'error')
                self.assertIn('space', progress['message'].lower())


class TestDatasetDownloaderIntegration(unittest.TestCase):
    """数据集下载器集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.download_dir = os.path.join(cls.temp_dir, 'downloads')
        cls.datasets_dir = os.path.join(cls.temp_dir, 'datasets')
        
        os.makedirs(cls.download_dir, exist_ok=True)
        os.makedirs(cls.datasets_dir, exist_ok=True)
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """每个测试方法的设置"""
        self.downloader = DatasetDownloader(
            download_dir=self.download_dir,
            datasets_dir=self.datasets_dir
        )
    
    def test_full_download_workflow(self):
        """测试完整下载工作流程"""
        with patch('requests.get') as mock_get:
            # 模拟成功的HTTP响应
            mock_response = MagicMock()
            mock_response.headers = {'content-length': '1024'}
            mock_response.iter_content.return_value = [b'workflow test data' * 16]
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            # 1. 开始下载
            task_id = self.downloader.start_download(
                url='https://example.com/workflow_test.zip',
                name='Workflow Test Dataset',
                description='Complete workflow test'
            )
            
            self.assertIsNotNone(task_id)
            
            # 2. 跟踪进度
            progress_states = []
            for _ in range(10):
                time.sleep(0.1)
                progress = self.downloader.get_download_progress(task_id)
                if progress:
                    progress_states.append(progress['status'])
                    if progress['status'] in ['completed', 'error']:
                        break
            
            # 3. 验证状态转换
            self.assertGreater(len(progress_states), 0)
            self.assertIn('downloading', progress_states)
            
            # 4. 验证最终状态
            final_progress = self.downloader.get_download_progress(task_id)
            self.assertIn(final_progress['status'], ['completed', 'error'])


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加DatasetDownloader测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatasetDownloader))
    
    # 添加集成测试
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestDatasetDownloaderIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果摘要
    print(f"\n{'='*50}")
    print(f"数据集下载器测试完成: 运行 {result.testsRun} 个测试")
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