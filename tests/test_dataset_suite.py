#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集管理模块完整测试套件
运行所有数据集相关的测试用例
"""

import unittest
import sys
import os
import time
from io import StringIO

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入所有测试模块
from test_dataset_model import TestDatasetModel
from test_dataset_service import TestDatasetManager, TestDatasetAnalyzer
from test_dataset_api import TestDatasetAPI, TestDatasetRouteIntegration
from test_dataset_downloader import TestDatasetDownloader, TestDatasetDownloaderIntegration


class ColoredTestResult(unittest.TextTestResult):
    """带颜色输出的测试结果类"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write(f"\033[92m✓\033[0m ")
            self.stream.writeln(f"PASS: {self.getDescription(test)}")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[91m✗\033[0m ")
            self.stream.writeln(f"ERROR: {self.getDescription(test)}")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[93m✗\033[0m ")
            self.stream.writeln(f"FAIL: {self.getDescription(test)}")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(f"\033[94m-\033[0m ")
            self.stream.writeln(f"SKIP: {self.getDescription(test)} ({reason})")


class ColoredTestRunner(unittest.TextTestRunner):
    """带颜色输出的测试运行器"""
    
    def __init__(self, **kwargs):
        kwargs['resultclass'] = ColoredTestResult
        super().__init__(**kwargs)
    
    def run(self, test):
        """运行测试并返回结果"""
        result = super().run(test)
        
        # 输出详细的测试结果
        self._print_test_summary(result)
        
        return result
    
    def _print_test_summary(self, result):
        """打印测试摘要"""
        print(f"\n{'='*80}")
        print(f"\033[1m测试结果摘要\033[0m")
        print(f"{'='*80}")
        
        # 基本统计
        total_tests = result.testsRun
        passed = result.success_count
        failed = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)
        
        print(f"运行测试总数: {total_tests}")
        print(f"\033[92m通过: {passed}\033[0m")
        if failed > 0:
            print(f"\033[93m失败: {failed}\033[0m")
        if errors > 0:
            print(f"\033[91m错误: {errors}\033[0m")
        if skipped > 0:
            print(f"\033[94m跳过: {skipped}\033[0m")
        
        # 成功率
        if total_tests > 0:
            success_rate = (passed / total_tests) * 100
            print(f"成功率: {success_rate:.1f}%")
        
        # 失败详情
        if result.failures:
            print(f"\n\033[93m失败的测试:\033[0m")
            for i, (test, traceback) in enumerate(result.failures, 1):
                print(f"{i}. {test}")
                # 提取关键错误信息
                lines = traceback.split('\n')
                for line in lines:
                    if 'AssertionError' in line:
                        print(f"   → {line.strip()}")
                        break
        
        # 错误详情
        if result.errors:
            print(f"\n\033[91m错误的测试:\033[0m")
            for i, (test, traceback) in enumerate(result.errors, 1):
                print(f"{i}. {test}")
                # 提取关键错误信息
                lines = traceback.split('\n')
                for line in lines:
                    if any(word in line for word in ['Error:', 'Exception:', 'ImportError:', 'ModuleNotFoundError:']):
                        print(f"   → {line.strip()}")
                        break
        
        # 总体结果
        overall_success = failed == 0 and errors == 0
        if overall_success:
            print(f"\n\033[1;92m🎉 所有测试通过！\033[0m")
        else:
            print(f"\n\033[1;91m❌ 有测试失败，请检查上述错误信息\033[0m")
        
        print(f"{'='*80}")


def create_test_suite():
    """创建完整的测试套件"""
    suite = unittest.TestSuite()
    
    # 定义测试用例组
    test_cases = [
        # 数据集模型测试
        ('数据集模型', TestDatasetModel),
        
        # 数据集服务测试
        ('数据集管理服务', TestDatasetManager),
        ('数据集分析服务', TestDatasetAnalyzer),
        
        # 数据集API测试
        ('数据集API', TestDatasetAPI),
        ('数据集路由集成', TestDatasetRouteIntegration),
        
        # 数据集下载器测试
        ('数据集下载器', TestDatasetDownloader),
        ('下载器集成测试', TestDatasetDownloaderIntegration),
    ]
    
    # 添加测试用例到套件
    loader = unittest.TestLoader()
    for name, test_class in test_cases:
        print(f"加载测试组: {name}")
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    return suite


def run_specific_test_group(group_name):
    """运行特定的测试组"""
    test_groups = {
        'model': [TestDatasetModel],
        'service': [TestDatasetManager, TestDatasetAnalyzer],
        'api': [TestDatasetAPI, TestDatasetRouteIntegration],
        'downloader': [TestDatasetDownloader, TestDatasetDownloaderIntegration],
    }
    
    if group_name not in test_groups:
        print(f"未知的测试组: {group_name}")
        print(f"可用的测试组: {', '.join(test_groups.keys())}")
        return False
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    for test_class in test_groups[group_name]:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = ColoredTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0


def run_all_tests():
    """运行所有测试"""
    print("\033[1;36m" + "="*80 + "\033[0m")
    print("\033[1;36m" + "VisioFirm 数据集管理模块测试套件".center(80) + "\033[0m")
    print("\033[1;36m" + "="*80 + "\033[0m")
    
    start_time = time.time()
    
    # 创建并运行测试套件
    suite = create_test_suite()
    runner = ColoredTestRunner(verbosity=2)
    result = runner.run(suite)
    
    end_time = time.time()
    
    # 输出执行时间
    duration = end_time - start_time
    print(f"\n总执行时间: {duration:.2f} 秒")
    
    # 返回测试是否全部通过
    return len(result.failures) == 0 and len(result.errors) == 0


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='VisioFirm 数据集管理模块测试套件')
    parser.add_argument(
        '--group', '-g',
        choices=['model', 'service', 'api', 'downloader'],
        help='运行特定的测试组'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='详细输出模式'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='安静模式，只输出结果'
    )
    
    args = parser.parse_args()
    
    # 设置详细程度
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1
    
    # 运行测试
    try:
        if args.group:
            success = run_specific_test_group(args.group)
        else:
            success = run_all_tests()
        
        # 根据结果设置退出码
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n\033[93m测试被用户中断\033[0m")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n\033[91m测试运行时发生错误: {e}\033[0m")
        sys.exit(1)


if __name__ == '__main__':
    main()