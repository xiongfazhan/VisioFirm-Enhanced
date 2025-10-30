import os
import json
import yaml
import logging
import threading
import time
import os
from datetime import datetime
from pathlib import Path
import torch
from ultralytics import YOLO
from visiofirm.models.training import TrainingTask
from visiofirm.utils.performance_config import performance_manager
import shutil

# Configure logging with less verbose output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# 设置ultralytics日志级别，减少冗余输出
import logging
ultralytics_logger = logging.getLogger('ultralytics')
ultralytics_logger.setLevel(logging.ERROR)

# 设置torch日志级别
torch_logger = logging.getLogger('torch')
torch_logger.setLevel(logging.ERROR)

class TrainingEngine:
    def __init__(self, project_name, project_path):
        self.project_name = project_name
        self.project_path = project_path
        self.training_task = TrainingTask(project_name, project_path)
        self.current_task_id = None
        self.training_thread = None
        self.stop_training = False
        self._project = None

    @property
    def project(self):
        """延迟加载Project实例以避免循环导入"""
        if self._project is None:
            from visiofirm.models.project import Project
            self._project = Project(self.project_name, "", "", self.project_path)
        return self._project

    def prepare_dataset(self, dataset_split):
        """准备训练数据集"""
        try:
            # 验证数据集分割比例
            train_ratio = dataset_split.get('train', 0.7)
            val_ratio = dataset_split.get('val', 0.2)
            test_ratio = dataset_split.get('test', 0.1)
            
            total_ratio = train_ratio + val_ratio + test_ratio
            if abs(total_ratio - 1.0) > 0.01:
                raise ValueError(f"数据集分割比例之和应为1.0，当前为: {total_ratio}")
            
            # 创建数据集目录结构
            dataset_dir = os.path.join(self.project_path, 'dataset')
            os.makedirs(dataset_dir, exist_ok=True)
            
            # 创建训练、验证、测试目录
            for split in ['train', 'val', 'test']:
                split_dir = os.path.join(dataset_dir, split)
                os.makedirs(os.path.join(split_dir, 'images'), exist_ok=True)
                os.makedirs(os.path.join(split_dir, 'labels'), exist_ok=True)

            # 获取所有已标注的图片
            annotated_images = self.project.get_annotated_images()
            
            if not annotated_images:
                raise ValueError("没有找到已标注的图片，请先完成图片标注")
            
            logger.info(f"找到 {len(annotated_images)} 张已标注的图片")
            
            # 验证数据集最小大小
            min_total_images = 2
            if len(annotated_images) < min_total_images:
                raise ValueError(f"数据集太小，需要至少 {min_total_images} 张已标注的图片。\n"
                               f"当前只有 {len(annotated_images)} 张已标注图片。\n"
                               f"请先完成更多图片的标注后再开始训练。")

            # 按比例分割数据集
            total_images = len(annotated_images)
            
            # 对于小数据集，调整分割策略
            if total_images == 2:
                # 只有2张图片时，1张训练，1张验证
                train_count = 1
                val_count = 1
                test_count = 0
            elif total_images <= 5:
                # 3-5张图片时，适当调整比例
                train_count = max(1, total_images - 1)
                val_count = 1
                test_count = 0
            else:
                # 正常按比例分割
                train_count = max(1, int(total_images * train_ratio))
                val_count = max(1, int(total_images * val_ratio))
                test_count = total_images - train_count - val_count
            
            # 分配图片到不同集合
            train_images = annotated_images[:train_count]
            val_images = annotated_images[train_count:train_count + val_count]
            test_images = annotated_images[train_count + val_count:] if test_count > 0 else []

            # 复制图片和标注文件
            self._copy_dataset_files(train_images, os.path.join(dataset_dir, 'train'))
            self._copy_dataset_files(val_images, os.path.join(dataset_dir, 'val'))
            if test_images:
                self._copy_dataset_files(test_images, os.path.join(dataset_dir, 'test'))

            # 创建数据集配置文件
            self._create_dataset_yaml(dataset_dir)
            
            logger.info(f"数据集准备完成: 训练集{len(train_images)}, 验证集{len(val_images)}, 测试集{len(test_images)}")
            return dataset_dir

        except Exception as e:
            logger.error(f"数据集准备失败: {e}")
            raise

    def _copy_dataset_files(self, images, target_dir):
        """复制图片和标注文件到目标目录"""
        images_dir = os.path.join(target_dir, 'images')
        labels_dir = os.path.join(target_dir, 'labels')
        
        success_count = 0
        error_count = 0
        
        for image_info in images:
            try:
                image_name = image_info['name']
                image_path = image_info['path']
                
                # 检查源文件是否存在
                if not os.path.exists(image_path):
                    logger.warning(f"源图片文件不存在: {image_path}")
                    error_count += 1
                    continue
                
                # 复制图片
                target_image_path = os.path.join(images_dir, image_name)
                shutil.copy2(image_path, target_image_path)
                
                # 生成YOLO格式标注文件
                label_name = os.path.splitext(image_name)[0] + '.txt'
                label_path = os.path.join(labels_dir, label_name)
                self._generate_yolo_label(image_info, label_path)
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"复制文件失败 {image_info.get('name', 'unknown')}: {e}")
                error_count += 1
        
        logger.info(f"文件复制完成: 成功{success_count}, 失败{error_count}")
        
        if success_count == 0:
            raise ValueError("没有成功复制任何文件")

    def _generate_yolo_label(self, image_info, label_path):
        """生成YOLO格式的标注文件"""
        try:
            annotations = self.project.get_annotations_by_image_id(image_info['id'])
            classes = self.project.get_classes()
            class_map = {cls: idx for idx, cls in enumerate(classes)}
            
            with open(label_path, 'w') as f:
                for ann in annotations:
                    if ann['class_name'] in class_map:
                        class_id = class_map[ann['class_name']]
                        
                        # 转换坐标为YOLO格式 (相对坐标)
                        img_width = image_info['width']
                        img_height = image_info['height']
                        
                        if ann['type'] in ['rect', 'bbox'] and ann['x'] is not None:
                            # 边界框格式: class_id center_x center_y width height
                            x, y, w, h = ann['x'], ann['y'], ann['width'], ann['height']
                            center_x = (x + w/2) / img_width
                            center_y = (y + h/2) / img_height
                            norm_w = w / img_width
                            norm_h = h / img_height
                            
                            f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {norm_w:.6f} {norm_h:.6f}\n")
                        
                        elif ann['type'] == 'polygon' and ann.get('points'):
                            # 分割格式: class_id x1 y1 x2 y2 ... xn yn
                            points = ann['points']
                            normalized_points = []
                            for point in points:
                                norm_x = point['x'] / img_width
                                norm_y = point['y'] / img_height
                                normalized_points.extend([f"{norm_x:.6f}", f"{norm_y:.6f}"])
                            
                            f.write(f"{class_id} {' '.join(normalized_points)}\n")
                            
        except Exception as e:
            logger.error(f"生成YOLO标注文件失败: {e}")

    def _create_dataset_yaml(self, dataset_dir):
        """创建数据集配置文件"""
        try:
            classes = self.project.get_classes()
            # 确保 classes 是字符串列表
            if classes and isinstance(classes[0], dict):
                class_names = [cls['name'] for cls in classes]
            else:
                class_names = classes if classes else []
            
            dataset_config = {
                'path': dataset_dir,
                'train': 'train/images',
                'val': 'val/images',
                'test': 'test/images',
                'nc': len(class_names),
                'names': class_names
            }
            
            yaml_path = os.path.join(dataset_dir, 'dataset.yaml')
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(dataset_config, f, default_flow_style=False, allow_unicode=True)
                
            logger.info(f"数据集配置文件已创建: {yaml_path}")
            return yaml_path
            
        except Exception as e:
            logger.error(f"创建数据集配置文件失败: {e}")
            raise

    def start_training(self, task_id, model_type, dataset_split, config):
        """开始训练任务"""
        try:
            # 检查是否可以启动新任务
            can_start, message = performance_manager.can_start_task(task_id)
            if not can_start:
                logger.warning(f"无法启动任务 {task_id}: {message}")
                self.training_task.update_task_status(task_id, 'failed', 0, message)
                return False
            
            self.current_task_id = task_id
            self.stop_training = False
            
            # 获取优化的训练配置
            optimized_config = performance_manager.get_memory_efficient_config(
                model_type, 
                config.get('epochs', 100), 
                config.get('device', 'auto')
            )
            
            # 合并用户配置和优化配置
            final_config = {**optimized_config, **config}
            
            # 注册任务到性能管理器
            task_info = {
                'start_time': datetime.now(),
                'model_type': model_type,
                'device': final_config.get('device', 'auto'),
                'batch_size': final_config.get('batch', 16)
            }
            performance_manager.register_task(task_id, task_info)
            
            # 更新任务状态为运行中
            self.training_task.update_task_status(task_id, 'running', 0)
            
            # 在后台线程中执行训练
            self.training_thread = threading.Thread(
                target=self._run_training,
                args=(task_id, model_type, dataset_split, final_config)
            )
            self.training_thread.start()
            
            logger.info(f"训练任务 {task_id} 已启动，使用优化配置")
            return True
            
        except Exception as e:
            logger.error(f"启动训练失败: {e}")
            performance_manager.unregister_task(task_id)
            self.training_task.update_task_status(task_id, 'failed', 0, str(e))
            return False

    def _get_optimal_device(self, requested_device='auto'):
        """获取最优的训练设备"""
        if requested_device != 'auto':
            return requested_device
        
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            optimal_device = 'cuda:0'
            logger.info(f"检测到CUDA设备，使用: {optimal_device}")
            return optimal_device
        else:
            logger.info("未检测到CUDA设备，使用CPU训练")
            return 'cpu'

    def _run_training(self, task_id, model_type, dataset_split, config):
        """执行训练过程"""
        try:
            # 准备数据集
            dataset_dir = self.prepare_dataset(dataset_split)
            dataset_yaml = os.path.join(dataset_dir, 'dataset.yaml')
            
            # 确保模型可用
            if model_type.startswith('yolo'):
                model_path = self.ensure_model_available(model_type)
                model = YOLO(model_path)
            else:
                raise ValueError(f"不支持的模型类型: {model_type}")
            
            # 获取最优设备
            optimal_device = self._get_optimal_device(config.get('device', 'auto'))
            
            # 设置训练参数
            train_args = {
                'data': dataset_yaml,
                'epochs': config.get('epochs', 100),
                'batch': config.get('batch_size', 16),
                'imgsz': config.get('image_size', 640),
                'lr0': config.get('learning_rate', 0.01),
                'device': optimal_device,
                'project': os.path.join(self.project_path, 'training_runs'),
                'name': f"task_{task_id}",
                'save_period': 10,  # 每10个epoch保存一次
                'patience': 50,     # 早停耐心值
                'verbose': True
            }
            
            # 添加其他参数
            if 'optimizer' in config and config['optimizer'] != 'auto':
                train_args['optimizer'] = config['optimizer']
            
            # 自定义回调函数来监控训练进度
            def on_train_epoch_end(trainer):
                try:
                    if self.stop_training:
                        trainer.stop = True
                        return
                    
                    epoch = trainer.epoch + 1  # YOLO的epoch从0开始，显示时+1
                    total_epochs = trainer.epochs
                    progress = int((epoch / total_epochs) * 100)
                    
                    # 更新进度
                    self.training_task.update_task_status(task_id, 'running', progress)
                    
                    # 记录训练日志
                    try:
                        # 从训练器中提取损失值
                        loss = None
                        if hasattr(trainer, 'loss') and trainer.loss is not None:
                            loss = float(trainer.loss.item()) if hasattr(trainer.loss, 'item') else float(trainer.loss)
                        elif hasattr(trainer, 'losses') and trainer.losses:
                            loss = float(trainer.losses[-1]) if trainer.losses else None
                        elif hasattr(trainer, 'tloss') and trainer.tloss is not None:
                            loss = float(trainer.tloss)
                        
                        # 记录训练进度到数据库
                        if loss is not None:
                            self.training_task.log_training_progress(task_id, epoch, loss)
                            # 只在每5个epoch或最后一个epoch时输出日志
                            if epoch % 5 == 0 or epoch == total_epochs:
                                logger.info(f"📈 Epoch {epoch}/{total_epochs} | Loss: {loss:.4f} | Progress: {progress}%")
                        else:
                            # 只在每5个epoch或最后一个epoch时输出日志
                            if epoch % 5 == 0 or epoch == total_epochs:
                                logger.info(f"📈 Epoch {epoch}/{total_epochs} | Progress: {progress}%")
                            
                    except Exception as log_error:
                        logger.warning(f"记录训练日志时出错: {log_error}")
                        
                except Exception as callback_error:
                    logger.error(f"训练回调函数出错: {callback_error}")
            
            def on_train_end(trainer):
                try:
                    # 训练结束时的处理
                    logger.info(f"✅ 训练任务 {task_id} 完成")
                except Exception as e:
                    logger.error(f"❌ 训练结束回调出错: {e}")
            
            # 添加回调
            model.add_callback('on_train_epoch_end', on_train_epoch_end)
            model.add_callback('on_train_end', on_train_end)
            
            # 开始训练
            logger.info(f"🚀 开始训练任务 {task_id}")
            logger.info(f"📊 模型: {model_type} | 设备: {optimal_device} | 轮数: {config.get('epochs', 100)}")
            
            # 临时重定向stdout来减少训练过程中的冗余输出
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                results = model.train(**train_args)
            finally:
                # 恢复stdout
                sys.stdout = old_stdout
            
            if not self.stop_training:
                # 训练完成，保存模型路径和指标
                weights_dir = os.path.join(train_args['project'], train_args['name'], 'weights')
                best_model_path = os.path.join(weights_dir, 'best.pt')
                
                # 检查模型文件是否生成
                if not os.path.exists(best_model_path):
                    # 如果 best.pt 不存在，尝试使用 last.pt
                    last_model_path = os.path.join(weights_dir, 'last.pt')
                    if os.path.exists(last_model_path):
                        best_model_path = last_model_path
                        logger.warning(f"⚠️ best.pt 不存在，使用 last.pt: {best_model_path}")
                    else:
                        logger.error(f"❌ 训练完成但没有找到模型文件: {weights_dir}")
                        self.training_task.update_task_status(task_id, 'failed', None, "训练完成但模型文件丢失")
                        return
                
                # 提取训练指标
                metrics = {}
                try:
                    if hasattr(results, 'results_dict'):
                        metrics = results.results_dict
                    elif hasattr(results, 'maps') and results.maps:
                        metrics = {'mAP50': float(results.maps[0])}
                    elif hasattr(results, 'box') and hasattr(results.box, 'map50'):
                        metrics = {
                            'mAP50': float(results.box.map50),
                            'mAP50-95': float(results.box.map) if hasattr(results.box, 'map') else 0.0
                        }
                    
                    # 添加更多指标
                    if hasattr(results, 'box'):
                        if hasattr(results.box, 'mp'):
                            metrics['precision'] = float(results.box.mp)
                        if hasattr(results.box, 'mr'):
                            metrics['recall'] = float(results.box.mr)
                            
                except Exception as metrics_error:
                    logger.warning(f"⚠️ 提取训练指标时出错: {metrics_error}")
                    metrics = {'note': '训练完成但指标提取失败'}
                
                self.training_task.update_task_status(
                    task_id, 'completed', 100, 
                    model_path=best_model_path, 
                    metrics=metrics
                )
                
                logger.info(f"🎯 训练任务 {task_id} 完成，模型保存在: {best_model_path}")
            else:
                self.training_task.update_task_status(task_id, 'stopped', None, "训练被用户停止")
                logger.info(f"⏹️ 训练任务 {task_id} 被停止")
                
        except Exception as e:
            logger.error(f"❌ 训练过程出错: {e}")
            self.training_task.update_task_status(task_id, 'failed', None, str(e))
        finally:
            # 确保任务在结束时被注销
            performance_manager.unregister_task(task_id)

    def _check_and_fix_task_status(self, task_id):
        """检查并修复任务状态不一致问题"""
        try:
            db_task = self.training_task.get_task_details(task_id)
            if not db_task:
                return None, "任务不存在"
            
            # 检查状态一致性
            db_running = db_task['status'] == 'running'
            thread_running = (self.current_task_id == task_id and 
                             self.training_thread and 
                             self.training_thread.is_alive())
            
            # 状态不一致时自动修复
            if db_running and not thread_running:
                logger.warning(f"检测到状态不一致，自动修复任务 {task_id}")
                self.training_task.update_task_status(task_id, 'failed', None, "训练进程异常结束")
                performance_manager.unregister_task(task_id)  # 清理性能管理器
                return 'fixed', "状态已自动修复"
            
            return db_task['status'], None
            
        except Exception as e:
            logger.error(f"检查任务状态失败: {e}")
            return None, str(e)

    def stop_training_task(self, task_id):
        """停止训练任务（增强版）"""
        try:
            # 检查并修复状态
            status, message = self._check_and_fix_task_status(task_id)
            
            if status is None:
                logger.error(f"任务 {task_id} 不存在或检查失败: {message}")
                return False
            
            if status == 'fixed':
                logger.info(f"任务 {task_id} 状态已修复: {message}")
                return True
            
            if status != 'running':
                logger.warning(f"任务 {task_id} 当前状态为 {status}，无需停止")
                return False
            
            # 正常停止流程
            if self.current_task_id == task_id and self.training_thread and self.training_thread.is_alive():
                self.stop_training = True
                self.training_thread.join(timeout=30)  # 等待最多30秒
                
                # 从性能管理器中注销任务
                performance_manager.unregister_task(task_id)
                
                self.training_task.update_task_status(task_id, 'stopped', None, "训练被用户停止")
                logger.info(f"训练任务 {task_id} 已停止")
                return True
            else:
                # 强制状态修复 - 数据库显示运行但线程已结束
                logger.warning(f"强制修复任务 {task_id} 状态")
                self.training_task.update_task_status(task_id, 'stopped', None, "强制停止")
                performance_manager.unregister_task(task_id)
                return True
                
        except Exception as e:
            logger.error(f"停止训练任务失败: {e}")
            performance_manager.unregister_task(task_id)  # 确保清理
            return False

    def get_training_status(self, task_id):
        """获取训练状态"""
        return self.training_task.get_task_details(task_id)

    def get_available_models(self):
        """获取可用的模型列表"""
        models = [
            {'name': 'yolov8n', 'description': 'YOLOv8 Nano - 最快，精度较低', 'size': '6MB'},
            {'name': 'yolov8s', 'description': 'YOLOv8 Small - 平衡速度和精度', 'size': '22MB'},
            {'name': 'yolov8m', 'description': 'YOLOv8 Medium - 较高精度', 'size': '50MB'},
            {'name': 'yolov8l', 'description': 'YOLOv8 Large - 高精度', 'size': '87MB'},
            {'name': 'yolov8x', 'description': 'YOLOv8 Extra Large - 最高精度', 'size': '136MB'},
            {'name': 'yolov10n', 'description': 'YOLOv10 Nano - 最新版本，最快', 'size': '5MB'},
            {'name': 'yolov10s', 'description': 'YOLOv10 Small - 最新版本，平衡', 'size': '20MB'},
            {'name': 'yolov10m', 'description': 'YOLOv10 Medium - 最新版本，较高精度', 'size': '45MB'},
            {'name': 'yolov10l', 'description': 'YOLOv10 Large - 最新版本，高精度', 'size': '80MB'},
            {'name': 'yolov10x', 'description': 'YOLOv10 Extra Large - 最新版本，最高精度', 'size': '125MB'}
        ]
        
        # 检查模型是否已下载
        for model in models:
            model_path = self._get_model_path(model['name'])
            model['downloaded'] = os.path.exists(model_path)
            model['path'] = model_path
        
        return models

    def _get_model_path(self, model_name):
        """获取模型文件路径"""
        from visiofirm.config import WEIGHTS_FOLDER
        return os.path.join(WEIGHTS_FOLDER, f"{model_name}.pt")

    def download_model(self, model_name, progress_callback=None):
        """下载指定的预训练模型"""
        try:
            model_path = self._get_model_path(model_name)
            
            # 如果模型已存在，直接返回
            if os.path.exists(model_path):
                logger.info(f"模型 {model_name} 已存在: {model_path}")
                return model_path
            
            # 确保权重目录存在
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
            logger.info(f"开始下载模型: {model_name}")
            
            # 使用YOLO自动下载功能，但禁用进度条
            import os
            import sys
            from io import StringIO
            
            # 临时重定向stdout来隐藏YOLO的下载进度
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                model = YOLO(f"{model_name}.pt")
                
                # 将下载的模型移动到指定位置
                if hasattr(model, 'ckpt_path') and os.path.exists(model.ckpt_path):
                    shutil.move(model.ckpt_path, model_path)
                    logger.info(f"模型 {model_name} 下载完成: {model_path}")
                else:
                    # 如果YOLO没有自动下载，手动下载
                    import requests
                    
                    # YOLO官方模型下载URL
                    model_urls = {
                        'yolov8n': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt',
                        'yolov8s': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt',
                        'yolov8m': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8m.pt',
                        'yolov8l': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8l.pt',
                        'yolov8x': 'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8x.pt',
                        'yolov10n': 'https://github.com/ultralytics/assets/releases/download/v0.1.0/yolo10n.pt',
                        'yolov10s': 'https://github.com/ultralytics/assets/releases/download/v0.1.0/yolo10s.pt',
                        'yolov10m': 'https://github.com/ultralytics/assets/releases/download/v0.1.0/yolo10m.pt',
                        'yolov10l': 'https://github.com/ultralytics/assets/releases/download/v0.1.0/yolo10l.pt',
                        'yolov10x': 'https://github.com/ultralytics/assets/releases/download/v0.1.0/yolo10x.pt'
                    }
                    
                    if model_name in model_urls:
                        url = model_urls[model_name]
                        logger.info(f"开始下载模型 {model_name}...")
                        response = requests.get(url, stream=True)
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        with open(model_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    if progress_callback:
                                        progress_callback(downloaded, total_size)
                        
                        logger.info(f"模型 {model_name} 下载完成 ({downloaded/1024/1024:.1f}MB)")
                    else:
                        raise ValueError(f"不支持的模型: {model_name}")
            finally:
                # 恢复stdout
                sys.stdout = old_stdout
            
            logger.info(f"模型下载完成: {model_path}")
            return model_path
            
        except Exception as e:
            logger.error(f"下载模型失败: {e}")
            raise

    def ensure_model_available(self, model_name):
        """确保模型可用，如果不存在则自动下载"""
        model_path = self._get_model_path(model_name)
        
        if not os.path.exists(model_path):
            logger.info(f"模型 {model_name} 不存在，开始自动下载...")
            return self.download_model(model_name)
        
        return model_path

    def get_device_info(self):
        """获取可用的计算设备信息"""
        devices = [{'name': 'auto', 'description': '自动选择最佳设备'}]
        
        # 检查CUDA可用性
        if torch.cuda.is_available():
            for i in range(torch.cuda.device_count()):
                device_name = torch.cuda.get_device_name(i)
                devices.append({
                    'name': f'cuda:{i}',
                    'description': f'GPU {i}: {device_name}'
                })
        
        # 添加CPU选项
        devices.append({'name': 'cpu', 'description': 'CPU (较慢但兼容性好)'})
        
        return devices

    def export_model(self, model_path, export_format='onnx', **kwargs):
        """导出训练好的模型"""
        supported_formats = {
            'onnx': {
                'extension': '.onnx',
                'description': 'ONNX - 跨平台推理格式'
            },
            'torchscript': {
                'extension': '.torchscript',
                'description': 'TorchScript - PyTorch优化格式'
            },
            'tflite': {
                'extension': '.tflite',
                'description': 'TensorFlow Lite - 移动端部署'
            },
            'coreml': {
                'extension': '.mlmodel',
                'description': 'Core ML - iOS/macOS部署'
            },
            'tensorrt': {
                'extension': '.engine',
                'description': 'TensorRT - NVIDIA GPU加速'
            }
        }
        
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
            
            if export_format not in supported_formats:
                raise ValueError(f"不支持的导出格式: {export_format}. 支持的格式: {list(supported_formats.keys())}")
            
            logger.info(f"开始导出模型为 {export_format} 格式...")
            
            model = YOLO(model_path)
            
            # 设置导出参数
            export_kwargs = {
                'format': export_format,
                'half': kwargs.get('half', False),  # FP16量化
                'int8': kwargs.get('int8', False),  # INT8量化
                'dynamic': kwargs.get('dynamic', False),  # 动态输入尺寸
                'simplify': kwargs.get('simplify', True),  # 简化ONNX模型
                'opset': kwargs.get('opset', 12),  # ONNX opset版本
                'workspace': kwargs.get('workspace', 4),  # TensorRT工作空间(GB)
                'batch': kwargs.get('batch', 1),  # 批处理大小
                'device': kwargs.get('device', None),  # 设备
            }
            
            # 移除None值参数
            export_kwargs = {k: v for k, v in export_kwargs.items() if v is not None}
            
            export_path = model.export(**export_kwargs)
            
            if not os.path.exists(export_path):
                raise RuntimeError(f"导出失败，文件未生成: {export_path}")
            
            # 获取文件大小
            file_size = os.path.getsize(export_path) / (1024 * 1024)  # MB
            
            logger.info(f"模型已成功导出为 {export_format} 格式")
            logger.info(f"导出路径: {export_path}")
            logger.info(f"文件大小: {file_size:.2f} MB")
            
            return {
                'success': True,
                'export_path': export_path,
                'format': export_format,
                'file_size_mb': round(file_size, 2),
                'description': supported_formats[export_format]['description']
            }
            
        except Exception as e:
            logger.error(f"模型导出失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'format': export_format
            }

    def get_resource_usage(self):
        """获取系统资源使用情况"""
        return performance_manager.monitor_resources()

    def get_performance_suggestions(self, model_type, current_config):
        """获取性能优化建议"""
        resource_usage = self.get_resource_usage()
        return performance_manager.suggest_optimization(model_type, current_config, resource_usage)

    def get_optimal_config(self, model_type, epochs, device='auto'):
        """获取优化的训练配置"""
        return performance_manager.get_memory_efficient_config(model_type, epochs, device)
    def validate_model(self, model_path, dataset_yaml, **kwargs):
        """验证训练好的模型"""
        try:
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型文件不存在: {model_path}")
            
            if not os.path.exists(dataset_yaml):
                raise FileNotFoundError(f"数据集配置文件不存在: {dataset_yaml}")
            
            logger.info(f"开始验证模型: {model_path}")
            
            model = YOLO(model_path)
            
            # 设置验证参数
            val_kwargs = {
                'data': dataset_yaml,
                'imgsz': kwargs.get('imgsz', 640),  # 图像尺寸
                'batch': kwargs.get('batch', 16),   # 批处理大小
                'conf': kwargs.get('conf', 0.001),  # 置信度阈值
                'iou': kwargs.get('iou', 0.6),      # IoU阈值
                'device': kwargs.get('device', None), # 设备
                'half': kwargs.get('half', False),   # FP16推理
                'save_json': kwargs.get('save_json', True),  # 保存JSON结果
                'save_hybrid': kwargs.get('save_hybrid', False), # 保存混合标签
                'plots': kwargs.get('plots', True),  # 生成图表
                'verbose': kwargs.get('verbose', True) # 详细输出
            }
            
            # 移除None值参数
            val_kwargs = {k: v for k, v in val_kwargs.items() if v is not None}
            
            results = model.val(**val_kwargs)
            
            # 提取验证指标
            metrics = {}
            
            if hasattr(results, 'box') and results.box:
                box_metrics = results.box
                
                # 基本指标
                metrics.update({
                    'mAP50': float(box_metrics.map50) if hasattr(box_metrics, 'map50') else 0.0,
                    'mAP50-95': float(box_metrics.map) if hasattr(box_metrics, 'map') else 0.0,
                    'precision': float(box_metrics.mp) if hasattr(box_metrics, 'mp') else 0.0,
                    'recall': float(box_metrics.mr) if hasattr(box_metrics, 'mr') else 0.0,
                    'f1_score': 0.0
                })
                
                # 计算F1分数
                if metrics['precision'] > 0 and metrics['recall'] > 0:
                    metrics['f1_score'] = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
                
                # 每个类别的指标
                if hasattr(box_metrics, 'ap') and hasattr(box_metrics, 'ap50'):
                    try:
                        # 读取数据集配置获取类别名称
                        with open(dataset_yaml, 'r', encoding='utf-8') as f:
                            dataset_config = yaml.safe_load(f)
                            class_names = dataset_config.get('names', [])
                        
                        if class_names and hasattr(box_metrics, 'ap50'):
                            class_metrics = {}
                            ap50_values = box_metrics.ap50 if hasattr(box_metrics.ap50, '__iter__') else [box_metrics.ap50]
                            
                            for i, class_name in enumerate(class_names):
                                if i < len(ap50_values):
                                    class_metrics[class_name] = {
                                        'AP50': float(ap50_values[i]) if ap50_values[i] is not None else 0.0
                                    }
                            
                            metrics['class_metrics'] = class_metrics
                            
                    except Exception as e:
                        logger.warning(f"无法获取每个类别的指标: {e}")
            
            # 添加验证信息
            metrics.update({
                'validation_date': datetime.now().isoformat(),
                'model_path': model_path,
                'dataset_yaml': dataset_yaml,
                'validation_params': val_kwargs
            })
            
            logger.info(f"模型验证完成")
            logger.info(f"mAP50: {metrics.get('mAP50', 0):.4f}, mAP50-95: {metrics.get('mAP50-95', 0):.4f}")
            logger.info(f"Precision: {metrics.get('precision', 0):.4f}, Recall: {metrics.get('recall', 0):.4f}")
            
            return {
                'success': True,
                'metrics': metrics,
                'results_path': getattr(results, 'save_dir', None)
            }
            
        except Exception as e:
            logger.error(f"模型验证失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }