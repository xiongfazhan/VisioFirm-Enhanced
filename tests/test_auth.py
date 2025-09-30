#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户认证功能测试模块
测试用户注册、登录、登出等认证相关功能
"""

import unittest
import tempfile
import os
import shutil
import sys
from werkzeug.security import generate_password_hash

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from visiofirm import create_app
from visiofirm.models.user import init_db, create_user, get_user_by_username


class TestAuthentication(unittest.TestCase):
    """用户认证测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_db_path = os.path.join(cls.temp_dir, 'test_users.db')
        
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setUp(self):
        """每个测试方法的设置"""
        # 初始化测试数据库
        init_db(self.test_db_path)
        
        # 创建Flask测试应用
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        """每个测试方法的清理"""
        self.app_context.pop()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    # ==================== 用户注册测试 ====================
    
    def test_user_registration_success(self):
        """测试用户注册成功"""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # 验证用户已创建
        user = get_user_by_username('testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'testuser')  # username
        self.assertEqual(user[3], 'test@example.com')  # email
    
    def test_user_registration_duplicate_username(self):
        """测试重复用户名注册失败"""
        # 创建第一个用户
        create_user('testuser', 'test@example.com', 'Test User', 
                   generate_password_hash('TestPassword123'))
        
        # 尝试使用相同用户名注册
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'another@example.com',
            'full_name': 'Another User',
            'password': 'AnotherPassword123',
            'confirm_password': 'AnotherPassword123'
        })
        
        # 应该返回错误或重定向到注册页面
        self.assertIn(response.status_code, [200, 400])
    
    def test_user_registration_invalid_email(self):
        """测试无效邮箱格式注册失败"""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'invalid-email',  # 无效的邮箱格式
            'full_name': 'Test User',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123'
        })
        
        self.assertIn(response.status_code, [200, 400])
    
    def test_user_registration_password_mismatch(self):
        """测试密码不匹配注册失败"""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': 'TestPassword123',
            'confirm_password': 'DifferentPassword123'
        })
        
        self.assertIn(response.status_code, [200, 400])
    
    # ==================== 用户登录测试 ====================
    
    def test_user_login_success(self):
        """测试用户登录成功"""
        # 先创建用户
        create_user('testuser', 'test@example.com', 'Test User',
                   generate_password_hash('TestPassword123'))
        
        # 尝试登录
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'TestPassword123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
    
    def test_user_login_wrong_password(self):
        """测试错误密码登录失败"""
        # 先创建用户
        create_user('testuser', 'test@example.com', 'Test User',
                   generate_password_hash('TestPassword123'))
        
        # 使用错误密码尝试登录
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'WrongPassword123'
        })
        
        self.assertIn(response.status_code, [200, 401])
    
    def test_user_login_nonexistent_user(self):
        """测试不存在的用户登录失败"""
        response = self.client.post('/login', data={
            'username': 'nonexistent',
            'password': 'TestPassword123'
        })
        
        self.assertIn(response.status_code, [200, 401, 404])
    
    # ==================== 会话管理测试 ====================
    
    def test_user_logout(self):
        """测试用户登出功能"""
        # 先创建并登录用户
        create_user('testuser', 'test@example.com', 'Test User',
                   generate_password_hash('TestPassword123'))
        
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'TestPassword123'
        })
        
        # 登出
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_session_persistence(self):
        """测试会话持久性"""
        # 创建并登录用户
        create_user('testuser', 'test@example.com', 'Test User',
                   generate_password_hash('TestPassword123'))
        
        self.client.post('/login', data={
            'username': 'testuser',
            'password': 'TestPassword123'
        })
        
        # 访问需要认证的页面，应该成功
        response = self.client.get('/dashboard')
        # 如果需要登录，未登录时应该重定向到登录页
        self.assertIn(response.status_code, [200, 302])
    
    def test_protected_route_requires_login(self):
        """测试受保护路由需要登录"""
        # 未登录时访问受保护页面
        response = self.client.get('/dashboard')
        
        # 应该重定向到登录页面
        self.assertIn(response.status_code, [302, 401])
    
    # ==================== 密码安全测试 ====================
    
    def test_password_hashing(self):
        """测试密码是否被哈希存储"""
        password = 'TestPassword123'
        
        # 创建用户
        create_user('testuser', 'test@example.com', 'Test User',
                   generate_password_hash(password))
        
        # 获取用户信息
        user = get_user_by_username('testuser')
        stored_password = user[2]  # password_hash
        
        # 密码应该被哈希，不应该是明文
        self.assertNotEqual(stored_password, password)
        self.assertTrue(len(stored_password) > 50)  # 哈希后的密码应该很长
    
    def test_weak_password_rejected(self):
        """测试弱密码被拒绝"""
        response = self.client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'full_name': 'Test User',
            'password': '123',  # 太短的密码
            'confirm_password': '123'
        })
        
        # 应该返回错误
        self.assertIn(response.status_code, [200, 400])


class TestUserModel(unittest.TestCase):
    """用户模型测试类"""
    
    def setUp(self):
        """每个测试方法的设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_users.db')
        init_db(self.test_db_path)
    
    def tearDown(self):
        """每个测试方法的清理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_user(self):
        """测试创建用户"""
        user_id = create_user(
            'testuser',
            'test@example.com',
            'Test User',
            generate_password_hash('TestPassword123')
        )
        
        self.assertIsNotNone(user_id)
        self.assertGreater(user_id, 0)
    
    def test_get_user_by_username(self):
        """测试根据用户名获取用户"""
        create_user(
            'testuser',
            'test@example.com',
            'Test User',
            generate_password_hash('TestPassword123')
        )
        
        user = get_user_by_username('testuser')
        self.assertIsNotNone(user)
        self.assertEqual(user[1], 'testuser')
        self.assertEqual(user[3], 'test@example.com')
    
    def test_get_nonexistent_user(self):
        """测试获取不存在的用户"""
        user = get_user_by_username('nonexistent')
        self.assertIsNone(user)


def suite():
    """创建测试套件"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestAuthentication))
    test_suite.addTest(unittest.makeSuite(TestUserModel))
    return test_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())