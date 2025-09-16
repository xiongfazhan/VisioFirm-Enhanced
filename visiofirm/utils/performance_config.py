"""
VisioFirm训练模块性能优化配置
优化内存使用、训练速度和资源管理
"""

import os
import psutil
import torch
import logging
from threading import Lock

logger = logging.getLogger(__name__)

class PerformanceManager:
    """性能管理器 - 优化资源使用和训练性能"""
    
    def __init__(self):
        self.resource_lock = Lock()
        self.active_tasks = {}
        self.max_concurrent_tasks = self._calculate_max_concurrent_tasks()
        
    def _calculate_max_concurrent_tasks(self):
        """根据系统资源计算最大并发任务数"""
        try:
            # 获取系统内存 (GB)
            memory_gb = psutil.virtual_memory().total / (1024**3)
            
            # 获取GPU内存 (如果有)
            gpu_memory_gb = 0
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    gpu_memory_gb += torch.cuda.get_device_properties(i).total_memory / (1024**3)
            
            # 根据内存估算最大并发任务数
            # 假设每个训练任务需要2-4GB内存
            memory_based_limit = max(1, int(memory_gb / 4))
            gpu_based_limit = max(1, int(gpu_memory_gb / 6)) if gpu_memory_gb > 0 else 1
            
            # 取较小值，但至少为1
            max_tasks = min(memory_based_limit, gpu_based_limit, 3)  # 硬限制为3
            
            logger.info(f"系统内存: {memory_gb:.1f}GB, GPU内存: {gpu_memory_gb:.1f}GB")
            logger.info(f"计算得出的最大并发任务数: {max_tasks}")
            
            return max_tasks
            
        except Exception as e:
            logger.warning(f"计算最大并发任务数失败，使用默认值: {e}")
            return 1

    def can_start_task(self, task_id):
        """检查是否可以启动新任务"""
        with self.resource_lock:
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                return False, f"已达到最大并发任务数限制 ({self.max_concurrent_tasks})"
            
            if task_id in self.active_tasks:
                return False, "任务已在运行中"
            
            return True, "可以启动任务"

    def register_task(self, task_id, task_info):
        """注册活跃任务"""
        with self.resource_lock:
            self.active_tasks[task_id] = {
                'start_time': task_info.get('start_time'),
                'model_type': task_info.get('model_type'),
                'device': task_info.get('device', 'auto'),
                'batch_size': task_info.get('batch_size', 16)
            }
            logger.info(f"已注册任务 {task_id}，当前活跃任务数: {len(self.active_tasks)}")

    def unregister_task(self, task_id):
        """注销任务"""
        with self.resource_lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                logger.info(f"已注销任务 {task_id}，当前活跃任务数: {len(self.active_tasks)}")

    def get_optimal_batch_size(self, model_type, device):
        """根据模型类型和设备获取最优批量大小"""
        # 基础批量大小配置
        base_batch_sizes = {
            'yolov8n': 32,
            'yolov8s': 24,
            'yolov8m': 16,
            'yolov8l': 12,
            'yolov8x': 8,
            'yolov10n': 32,
            'yolov10s': 24,
            'yolov10m': 16,
            'yolov10l': 12,
            'yolov10x': 8,
        }
        
        base_batch = base_batch_sizes.get(model_type, 16)
        
        # 如果使用CPU，减少批量大小
        if device == 'cpu':
            base_batch = min(base_batch, 8)
        
        # 根据当前活跃任务数调整
        active_count = len(self.active_tasks)
        if active_count > 1:
            # 有多个任务运行时，减少批量大小以节省内存
            base_batch = max(4, base_batch // (active_count + 1))
        
        return base_batch

    def get_memory_efficient_config(self, model_type, epochs, device='auto'):
        """获取内存优化的训练配置"""
        config = {
            # 基础参数
            'epochs': epochs,
            'device': device,
            'amp': True,  # 自动混合精度训练
            'half': False,  # 不使用FP16（避免数值不稳定）
            
            # 内存优化
            'cache': False,  # 不缓存图像到内存
            'workers': min(4, os.cpu_count() // 2),  # 数据加载线程数
            'pin_memory': True if device != 'cpu' else False,
            
            # 模型优化
            'save_period': 20,  # 减少保存频率
            'plots': False,  # 训练期间不生成图表（节省内存）
            'val': True,  # 启用验证
            'patience': 30,  # 早停耐心值
            
            # 数据增强 - 适度使用以平衡性能和训练时间
            'augment': True,
            'mosaic': 0.5,  # 减少mosaic增强概率
            'mixup': 0.0,   # 关闭mixup（节省内存）
            'copy_paste': 0.0,  # 关闭copy-paste
            
            # 优化器设置
            'optimizer': 'AdamW',
            'momentum': 0.937,
            'weight_decay': 0.0005,
            'warmup_epochs': 3,
            'warmup_momentum': 0.8,
            'warmup_bias_lr': 0.1,
            
            # 损失函数权重
            'box': 7.5,
            'cls': 0.5,
            'dfl': 1.5,
        }
        
        # 根据模型类型调整批量大小
        config['batch'] = self.get_optimal_batch_size(model_type, device)
        
        # 根据模型复杂度调整学习率
        lr_map = {
            'yolov8n': 0.01,
            'yolov8s': 0.01,
            'yolov8m': 0.01,
            'yolov8l': 0.01,
            'yolov8x': 0.01,
            'yolov10n': 0.01,
            'yolov10s': 0.01,
            'yolov10m': 0.01,
            'yolov10l': 0.01,
            'yolov10x': 0.01,
        }
        config['lr0'] = lr_map.get(model_type, 0.01)
        
        return config

    def monitor_resources(self):
        """监控系统资源使用情况"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # GPU使用情况
            gpu_info = []
            if torch.cuda.is_available():
                for i in range(torch.cuda.device_count()):
                    try:
                        memory_used = torch.cuda.memory_allocated(i) / (1024**3)
                        memory_total = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                        memory_percent_gpu = (memory_used / memory_total) * 100
                        
                        gpu_info.append({
                            'device': f'cuda:{i}',
                            'name': torch.cuda.get_device_name(i),
                            'memory_used_gb': round(memory_used, 2),
                            'memory_total_gb': round(memory_total, 2),
                            'memory_percent': round(memory_percent_gpu, 1)
                        })
                    except Exception as e:
                        logger.warning(f"获取GPU {i} 信息失败: {e}")
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_available_gb': round(memory_available_gb, 2),
                'gpu_info': gpu_info,
                'active_tasks': len(self.active_tasks),
                'max_concurrent_tasks': self.max_concurrent_tasks
            }
            
        except Exception as e:
            logger.error(f"监控资源使用失败: {e}")
            return {}

    def suggest_optimization(self, model_type, current_config, resource_usage):
        """基于当前资源使用情况建议优化方案"""
        suggestions = []
        
        try:
            # 内存使用过高
            if resource_usage.get('memory_percent', 0) > 85:
                suggestions.append({
                    'type': 'memory',
                    'issue': '内存使用率过高',
                    'suggestion': '建议减少批量大小或关闭图像缓存',
                    'config_changes': {
                        'batch': max(4, current_config.get('batch', 16) // 2),
                        'cache': False,
                        'workers': max(1, current_config.get('workers', 4) // 2)
                    }
                })
            
            # CPU使用过高
            if resource_usage.get('cpu_percent', 0) > 90:
                suggestions.append({
                    'type': 'cpu',
                    'issue': 'CPU使用率过高',
                    'suggestion': '建议减少数据加载线程数',
                    'config_changes': {
                        'workers': max(1, current_config.get('workers', 4) // 2)
                    }
                })
            
            # GPU内存使用过高
            for gpu in resource_usage.get('gpu_info', []):
                if gpu.get('memory_percent', 0) > 90:
                    suggestions.append({
                        'type': 'gpu_memory',
                        'issue': f'GPU {gpu["device"]} 内存使用率过高',
                        'suggestion': '建议减少批量大小或启用梯度累积',
                        'config_changes': {
                            'batch': max(4, current_config.get('batch', 16) // 2),
                            'accumulate': 2  # 梯度累积
                        }
                    })
            
            # 并发任务过多
            if len(self.active_tasks) >= self.max_concurrent_tasks:
                suggestions.append({
                    'type': 'concurrency',
                    'issue': '并发任务数已达上限',
                    'suggestion': '建议等待当前任务完成后再启动新任务'
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
            return []

# 全局性能管理器实例
performance_manager = PerformanceManager()