from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
import os
import json
import logging
from werkzeug.utils import secure_filename
from visiofirm.config import PROJECTS_FOLDER
from visiofirm.models.training import TrainingTask
from visiofirm.utils.TrainingEngine import TrainingEngine
from visiofirm.models.project import Project
import threading
import zipfile
from io import BytesIO

bp = Blueprint('training', __name__, url_prefix='/training')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局训练引擎实例存储
training_engines = {}

def get_training_engine(project_name):
    """获取或创建训练引擎实例"""
    if project_name not in training_engines:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_engines[project_name] = TrainingEngine(project_name, project_path)
    return training_engines[project_name]

@bp.route('/<project_name>')
@login_required
def training_dashboard(project_name):
    """训练仪表板页面"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_path):
            return "项目不存在", 404
        
        # 获取项目信息
        project = Project(project_name, "", "", project_path)
        classes = project.get_classes()
        annotated_count = len(project.get_annotated_images())
        
        # 获取训练任务
        training_task = TrainingTask(project_name, project_path)
        tasks = training_task.get_training_tasks()
        configs = training_task.get_training_configs()
        
        # 获取可用模型和设备
        engine = get_training_engine(project_name)
        available_models = engine.get_available_models()
        available_devices = engine.get_device_info()
        
        return render_template('training.html',
                             project_name=project_name,
                             classes=classes,
                             annotated_count=annotated_count,
                             tasks=tasks,
                             configs=configs,
                             available_models=available_models,
                             available_devices=available_devices)
                             
    except Exception as e:
        logger.error(f"加载训练仪表板失败: {e}")
        return f"加载失败: {str(e)}", 500

@bp.route('/create_task', methods=['POST'])
@login_required
def create_training_task():
    """创建新的训练任务"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        task_name = data.get('task_name')
        model_type = data.get('model_type')
        
        # 数据集分割配置
        dataset_split = {
            'train': float(data.get('train_ratio', 0.7)),
            'val': float(data.get('val_ratio', 0.2)),
            'test': float(data.get('test_ratio', 0.1))
        }
        
        # 训练配置
        config = {
            'epochs': int(data.get('epochs', 100)),
            'batch_size': int(data.get('batch_size', 16)),
            'learning_rate': float(data.get('learning_rate', 0.01)),
            'image_size': int(data.get('image_size', 640)),
            'device': data.get('device', 'auto'),
            'optimizer': data.get('optimizer', 'auto'),
            'augmentation': data.get('augmentation', {}),
            'other_params': data.get('other_params', {})
        }
        
        if not all([project_name, task_name, model_type]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 检查项目是否存在
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_path):
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        # 检查是否有已标注的图片
        project = Project(project_name, "", "", project_path)
        annotated_images = project.get_annotated_images()
        if not annotated_images:
            return jsonify({'success': False, 'error': '没有已标注的图片，请先完成图片标注'}), 400
        
        if len(annotated_images) < 2:
            return jsonify({
                'success': False, 
                'error': f'数据集太小，需要至少2张已标注的图片。\n'
                        f'当前只有{len(annotated_images)}张已标注图片。\n'
                        f'请先完成更多图片的标注后再开始训练。'
            }), 400
        
        # 创建训练任务
        training_task = TrainingTask(project_name, project_path)
        task_id = training_task.create_training_task(task_name, model_type, dataset_split, config)
        
        logger.info(f"创建训练任务成功: {task_name} (ID: {task_id})")
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        logger.error(f"创建训练任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/start_task', methods=['POST'])
@login_required
def start_training_task():
    """启动训练任务"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        task_id = int(data.get('task_id'))
        
        if not project_name or not task_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 获取任务详情
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        task_details = training_task.get_task_details(task_id)
        
        if not task_details:
            return jsonify({'success': False, 'error': '训练任务不存在'}), 404
        
        if task_details['status'] == 'running':
            return jsonify({'success': False, 'error': '训练任务已在运行中'}), 400
        
        # 启动训练
        engine = get_training_engine(project_name)
        success = engine.start_training(
            task_id,
            task_details['model_type'],
            task_details['dataset_split'],
            task_details['config']
        )
        
        if success:
            return jsonify({'success': True, 'message': '训练任务已启动'})
        else:
            return jsonify({'success': False, 'error': '启动训练任务失败'}), 500
            
    except Exception as e:
        logger.error(f"启动训练任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/stop_task', methods=['POST'])
@login_required
def stop_training_task():
    """停止训练任务"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        task_id = int(data.get('task_id'))
        
        if not project_name or not task_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        # 停止训练
        engine = get_training_engine(project_name)
        success = engine.stop_training_task(task_id)
        
        if success:
            return jsonify({'success': True, 'message': '训练任务已停止'})
        else:
            return jsonify({'success': False, 'error': '停止训练任务失败'}), 500
            
    except Exception as e:
        logger.error(f"停止训练任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/task_status/<project_name>/<int:task_id>')
@login_required
def get_task_status(project_name, task_id):
    """获取训练任务状态"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        task_details = training_task.get_task_details(task_id)
        
        if not task_details:
            return jsonify({'success': False, 'error': '训练任务不存在'}), 404
        
        # 获取训练日志
        logs = training_task.get_training_logs(task_id)
        task_details['logs'] = logs
        
        return jsonify({'success': True, 'task': task_details})
        
    except Exception as e:
        logger.error(f"获取训练任务状态失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/tasks/<project_name>')
@login_required
def get_training_tasks(project_name):
    """获取所有训练任务"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        tasks = training_task.get_training_tasks()
        
        return jsonify({'success': True, 'tasks': tasks})
        
    except Exception as e:
        logger.error(f"获取训练任务列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/delete_task', methods=['POST'])
@login_required
def delete_training_task():
    """删除训练任务"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        task_id = int(data.get('task_id'))
        
        if not project_name or not task_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        
        # 检查任务是否在运行
        task_details = training_task.get_task_details(task_id)
        if task_details and task_details['status'] == 'running':
            return jsonify({'success': False, 'error': '无法删除正在运行的训练任务'}), 400
        
        training_task.delete_training_task(task_id)
        return jsonify({'success': True, 'message': '训练任务已删除'})
        
    except Exception as e:
        logger.error(f"删除训练任务失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/save_config', methods=['POST'])
@login_required
def save_training_config():
    """保存训练配置"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        config_name = data.get('config_name')
        
        if not project_name or not config_name:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        
        config_id = training_task.save_training_config(
            config_name=config_name,
            model_type=data.get('model_type', 'yolov8n'),
            epochs=int(data.get('epochs', 100)),
            batch_size=int(data.get('batch_size', 16)),
            learning_rate=float(data.get('learning_rate', 0.01)),
            image_size=int(data.get('image_size', 640)),
            device=data.get('device', 'auto'),
            optimizer=data.get('optimizer', 'auto'),
            augmentation=data.get('augmentation', {}),
            other_params=data.get('other_params', {})
        )
        
        return jsonify({'success': True, 'config_id': config_id})
        
    except Exception as e:
        logger.error(f"保存训练配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/configs/<project_name>')
@login_required
def get_training_configs(project_name):
    """获取训练配置列表"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        configs = training_task.get_training_configs()
        
        return jsonify({'success': True, 'configs': configs})
        
    except Exception as e:
        logger.error(f"获取训练配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/export_model', methods=['POST'])
@login_required
def export_model():
    """导出训练好的模型"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        task_id = int(data.get('task_id'))
        export_format = data.get('format', 'onnx')
        
        # 导出参数
        export_options = {
            'half': data.get('half', False),
            'int8': data.get('int8', False),
            'dynamic': data.get('dynamic', False),
            'simplify': data.get('simplify', True),
            'opset': data.get('opset', 12),
            'workspace': data.get('workspace', 4),
            'batch': data.get('batch', 1)
        }
        
        if not project_name or not task_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        task_details = training_task.get_task_details(task_id)
        
        if not task_details or not task_details.get('model_path'):
            return jsonify({'success': False, 'error': '模型文件不存在'}), 404
        
        # 导出模型
        engine = get_training_engine(project_name)
        result = engine.export_model(task_details['model_path'], export_format, **export_options)
        
        if result['success']:
            return jsonify({
                'success': True, 
                'export_path': result['export_path'],
                'format': result['format'],
                'file_size_mb': result['file_size_mb'],
                'description': result['description']
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
        
    except Exception as e:
        logger.error(f"导出模型失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/download_model/<project_name>/<int:task_id>')
@login_required
def download_model(project_name, task_id):
    """下载训练好的模型"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        task_details = training_task.get_task_details(task_id)
        
        if not task_details or not task_details.get('model_path'):
            return "模型文件不存在", 404
        
        model_path = task_details['model_path']
        if not os.path.exists(model_path):
            return "模型文件不存在", 404
        
        # 创建包含模型和相关文件的ZIP包
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 添加最佳模型
            zf.write(model_path, f"best.pt")
            
            # 添加训练结果目录中的其他文件
            results_dir = os.path.dirname(os.path.dirname(model_path))
            if os.path.exists(results_dir):
                for root, dirs, files in os.walk(results_dir):
                    for file in files:
                        if file.endswith(('.pt', '.yaml', '.txt', '.png', '.jpg')):
                            file_path = os.path.join(root, file)
                            arc_name = os.path.relpath(file_path, results_dir)
                            zf.write(file_path, arc_name)
        
        memory_file.seek(0)
        
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f"{project_name}_task_{task_id}_model.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"下载模型失败: {e}")
        return f"下载失败: {str(e)}", 500

@bp.route('/validate_model', methods=['POST'])
@login_required
def validate_model():
    """验证训练好的模型"""
    try:
        data = request.get_json()
        project_name = data.get('project_name')
        task_id = int(data.get('task_id'))
        
        # 验证参数
        validation_options = {
            'imgsz': data.get('imgsz', 640),
            'batch': data.get('batch', 16),
            'conf': data.get('conf', 0.001),
            'iou': data.get('iou', 0.6),
            'half': data.get('half', False),
            'plots': data.get('plots', True),
            'save_json': data.get('save_json', True)
        }
        
        if not project_name or not task_id:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        training_task = TrainingTask(project_name, project_path)
        task_details = training_task.get_task_details(task_id)
        
        if not task_details or not task_details.get('model_path'):
            return jsonify({'success': False, 'error': '模型文件不存在'}), 404
        
        # 验证模型
        engine = get_training_engine(project_name)
        dataset_yaml = os.path.join(project_path, 'dataset', 'dataset.yaml')
        
        if not os.path.exists(dataset_yaml):
            return jsonify({'success': False, 'error': '数据集配置文件不存在'}), 404
        
        result = engine.validate_model(task_details['model_path'], dataset_yaml, **validation_options)
        
        if result['success']:
            return jsonify({
                'success': True, 
                'metrics': result['metrics'],
                'results_path': result.get('results_path')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 500
        
    except Exception as e:
        logger.error(f"验证模型失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/available_models/<project_name>')
@login_required
def get_available_models(project_name):
    """获取可用的模型列表"""
    try:
        engine = get_training_engine(project_name)
        models = engine.get_available_models()
        devices = engine.get_device_info()
        
        return jsonify({
            'success': True,
            'models': models,
            'devices': devices
        })
        
    except Exception as e:
        logger.error(f"获取可用模型失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/export_formats')
@login_required
def get_export_formats():
    """获取支持的导出格式"""
    try:
        formats = {
            'onnx': {
                'name': 'ONNX',
                'description': '跨平台推理格式，广泛支持',
                'extension': '.onnx',
                'recommended': True
            },
            'torchscript': {
                'name': 'TorchScript',
                'description': 'PyTorch优化格式，高性能',
                'extension': '.torchscript',
                'recommended': False
            },
            'tflite': {
                'name': 'TensorFlow Lite',
                'description': '移动端和嵌入式设备部署',
                'extension': '.tflite',
                'recommended': False
            },
            'coreml': {
                'name': 'Core ML',
                'description': 'iOS和macOS平台部署',
                'extension': '.mlmodel',
                'recommended': False
            },
            'tensorrt': {
                'name': 'TensorRT',
                'description': 'NVIDIA GPU加速推理',
                'extension': '.engine',
                'recommended': False,
                'requires': 'NVIDIA GPU'
            }
        }
        
        return jsonify({
            'success': True,
            'formats': formats
        })
        
    except Exception as e:
        logger.error(f"获取导出格式失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/system_resources/<project_name>', methods=['GET'])
@login_required
def get_system_resources(project_name):
    """获取系统资源使用情况"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_path):
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        engine = get_training_engine(project_name)
        resource_usage = engine.get_resource_usage()
        
        return jsonify({
            'success': True,
            'data': resource_usage
        })
        
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/performance_suggestions/<project_name>', methods=['POST'])
@login_required
def get_performance_suggestions(project_name):
    """获取性能优化建议"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_path):
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        data = request.get_json()
        model_type = data.get('model_type', 'yolov8n')
        current_config = data.get('config', {})
        
        engine = get_training_engine(project_name)
        suggestions = engine.get_performance_suggestions(model_type, current_config)
        
        return jsonify({
            'success': True,
            'data': {
                'suggestions': suggestions,
                'resource_usage': engine.get_resource_usage()
            }
        })
        
    except Exception as e:
        logger.error(f"获取性能建议失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/optimal_config/<project_name>', methods=['POST'])
@login_required
def get_optimal_config(project_name):
    """获取优化的训练配置"""
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_path):
            return jsonify({'success': False, 'error': '项目不存在'}), 404
        
        data = request.get_json()
        model_type = data.get('model_type', 'yolov8n')
        epochs = data.get('epochs', 100)
        device = data.get('device', 'auto')
        
        engine = get_training_engine(project_name)
        optimal_config = engine.get_optimal_config(model_type, epochs, device)
        
        return jsonify({
            'success': True,
            'data': optimal_config
        })
        
    except Exception as e:
        logger.error(f"获取优化配置失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500