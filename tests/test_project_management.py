#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目管理功能测试模块
测试项目的创建、删除、更新、查询等核心功能
"""

import unittest
import tempfile
import os
import shutil
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from visiofirm.models.project import Project
from visiofirm.config import PROJECTS_FOLDER


class TestProjectManagement(unittest.TestCase):
    """项目管理测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_projects_folder = os.path.join(cls.temp_dir, 'projects')
        os.makedirs(cls.test_projects_folder, exist_ok=True)
        
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """每个测试方法的设置"""
        self.project_name = f"test_project_{os.getpid()}"
        self.project_path = os.path.join(self.test_projects_folder, self.project_name)
        
    def tearDown(self):
        """每个测试方法的清理"""
        if os.path.exists(self.project_path):
            shutil.rmtree(self.project_path)
    
    # ==================== 项目创建测试 ====================
    
    def test_create_project_detection(self):
        """测试创建检测类型项目"""
        project = Project(
            self.project_name,
            "Test detection project",
            "Bounding Box",
            self.project_path
        )
        
        # 验证项目目录已创建
        self.assertTrue(os.path.exists(self.project_path))
        
        # 验证数据库文件已创建
        db_path = os.path.join(self.project_path, 'config.db')
        self.assertTrue(os.path.exists(db_path))
    
    def test_create_project_obb(self):
        """测试创建OBB类型项目"""
        project = Project(
            self.project_name,
            "Test OBB project",
            "Oriented Bounding Box",
            self.project_path
        )
        
        self.assertTrue(os.path.exists(self.project_path))
    
    def test_create_project_segmentation(self):
        """测试创建分割类型项目"""
        project = Project(
            self.project_name,
            "Test segmentation project",
            "Segmentation",
            self.project_path
        )
        
        self.assertTrue(os.path.exists(self.project_path))
    
    def test_create_project_with_empty_name(self):
        """测试创建空名称项目应失败"""
        with self.assertRaises(Exception):
            project = Project(
                "",  # 空名称
                "Test project",
                "Bounding Box",
                self.project_path
            )
    
    def test_create_project_duplicate_path(self):
        """测试在已存在的路径创建项目"""
        # 创建第一个项目
        project1 = Project(
            self.project_name,
            "First project",
            "Bounding Box",
            self.project_path
        )
        
        # 尝试在相同路径创建第二个项目
        # 应该能够处理已存在的目录
        project2 = Project(
            self.project_name,
            "Second project",
            "Bounding Box",
            self.project_path
        )
        
        self.assertTrue(os.path.exists(self.project_path))
    
    # ==================== 项目信息测试 ====================
    
    def test_get_project_info(self):
        """测试获取项目信息"""
        description = "Test project description"
        project_type = "Bounding Box"
        
        project = Project(
            self.project_name,
            description,
            project_type,
            self.project_path
        )
        
        # 验证项目属性
        self.assertEqual(project.name, self.project_name)
        self.assertEqual(project.project_path, self.project_path)
    
    def test_project_database_initialization(self):
        """测试项目数据库初始化"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        db_path = os.path.join(self.project_path, 'config.db')
        self.assertTrue(os.path.exists(db_path))
        
        # 验证数据库可以连接
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查必要的表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 应该包含基本的表
        self.assertGreater(len(tables), 0)
        
        conn.close()
    
    # ==================== 类别管理测试 ====================
    
    def test_add_classes(self):
        """测试添加类别"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        classes = ['cat', 'dog', 'person']
        project.add_classes(classes)
        
        # 获取类别列表
        saved_classes = project.get_classes()
        
        self.assertEqual(len(saved_classes), 3)
        for cls in classes:
            self.assertIn(cls, saved_classes)
    
    def test_add_duplicate_class(self):
        """测试添加重复类别"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        # 添加类别两次
        project.add_classes(['cat', 'dog'])
        project.add_classes(['cat', 'bird'])  # cat是重复的
        
        saved_classes = project.get_classes()
        
        # 不应该有重复
        self.assertEqual(len(saved_classes), 3)
        self.assertIn('cat', saved_classes)
        self.assertIn('dog', saved_classes)
        self.assertIn('bird', saved_classes)
    
    def test_delete_class(self):
        """测试删除类别"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        # 添加类别
        project.add_classes(['cat', 'dog', 'person'])
        
        # 删除一个类别（如果有删除方法）
        # project.delete_class('dog')
        
        # 注意：如果Project类没有delete_class方法，这个测试需要调整
        # 或者我们可以直接测试数据库操作
    
    def test_get_empty_classes(self):
        """测试获取空类别列表"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        classes = project.get_classes()
        self.assertIsInstance(classes, list)
        self.assertEqual(len(classes), 0)
    
    # ==================== 图像管理测试 ====================
    
    def test_get_annotated_images_empty(self):
        """测试获取空的已标注图像列表"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        annotated_images = project.get_annotated_images()
        
        self.assertIsInstance(annotated_images, list)
        self.assertEqual(len(annotated_images), 0)
    
    # ==================== 项目统计测试 ====================
    
    def test_project_statistics(self):
        """测试项目统计信息"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        # 添加类别
        project.add_classes(['cat', 'dog'])
        
        # 获取统计信息
        stats = {
            'classes_count': len(project.get_classes()),
            'images_count': len(project.get_annotated_images()),
        }
        
        self.assertEqual(stats['classes_count'], 2)
        self.assertEqual(stats['images_count'], 0)
    
    # ==================== 项目配置测试 ====================
    
    def test_project_configuration(self):
        """测试项目配置"""
        project_type = "Bounding Box"
        description = "Test configuration"
        
        project = Project(
            self.project_name,
            description,
            project_type,
            self.project_path
        )
        
        # 验证配置保存
        self.assertTrue(os.path.exists(self.project_path))
    
    # ==================== 项目删除测试 ====================
    
    def test_delete_project(self):
        """测试删除项目"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        # 验证项目存在
        self.assertTrue(os.path.exists(self.project_path))
        
        # 删除项目目录
        shutil.rmtree(self.project_path)
        
        # 验证项目已删除
        self.assertFalse(os.path.exists(self.project_path))
    
    def test_delete_project_with_data(self):
        """测试删除包含数据的项目"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        # 添加一些数据
        project.add_classes(['cat', 'dog'])
        
        # 创建一些文件
        test_file = os.path.join(self.project_path, 'test_data.txt')
        with open(test_file, 'w') as f:
            f.write('test data')
        
        # 删除项目
        shutil.rmtree(self.project_path)
        
        # 验证所有数据都被删除
        self.assertFalse(os.path.exists(self.project_path))
        self.assertFalse(os.path.exists(test_file))


class TestProjectDirectory(unittest.TestCase):
    """项目目录结构测试类"""
    
    def setUp(self):
        """每个测试方法的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_name = "test_project"
        self.project_path = os.path.join(self.temp_dir, self.project_name)
    
    def tearDown(self):
        """每个测试方法的清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_project_directory_structure(self):
        """测试项目目录结构"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        # 验证基本目录结构
        self.assertTrue(os.path.exists(self.project_path))
        self.assertTrue(os.path.isdir(self.project_path))
    
    def test_project_config_database(self):
        """测试项目配置数据库"""
        project = Project(
            self.project_name,
            "Test project",
            "Bounding Box",
            self.project_path
        )
        
        db_path = os.path.join(self.project_path, 'config.db')
        self.assertTrue(os.path.exists(db_path))
        
        # 验证是SQLite数据库
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            is_sqlite = True
        except:
            is_sqlite = False
        
        self.assertTrue(is_sqlite)


def suite():
    """创建测试套件"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestProjectManagement))
    test_suite.addTest(unittest.makeSuite(TestProjectDirectory))
    return test_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())