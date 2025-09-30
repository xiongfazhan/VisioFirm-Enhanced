from flask import Blueprint, request, jsonify, render_template, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import json
import uuid
import threading
from datetime import datetime
from visiofirm.config import PROJECTS_FOLDER
from visiofirm.models.dataset import init_dataset_db, get_dataset_by_id
from visiofirm.utils.dataset_service import DatasetManager, DatasetAnalyzer
from visiofirm.utils.dataset_downloader import DatasetDownloader
import logging

# Configure logging with less verbose output  
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

bp = Blueprint('dataset', __name__, url_prefix='/datasets')

# 初始化数据集数据库
init_dataset_db()

# 全局服务实例
dataset_manager = DatasetManager()
dataset_analyzer = DatasetAnalyzer()
dataset_downloader = DatasetDownloader()


@bp.route('/')
@login_required
def index():
    """数据集管理主页面"""
    return render_template('datasets.html')


@bp.route('/api/list')
@login_required
def list_datasets():
    """获取数据集列表API"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        dataset_type = request.args.get('type')
        
        # 限制分页参数
        page = max(1, page)
        limit = min(100, max(1, limit))
        
        result = dataset_manager.get_dataset_list(page, limit, dataset_type)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/<int:dataset_id>')
@login_required
def get_dataset_detail(dataset_id):
    """获取数据集详情API"""
    try:
        dataset = dataset_manager.get_dataset_detail(dataset_id)
        if not dataset:
            return jsonify({
                'success': False,
                'error': '数据集不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': dataset
        })
    except Exception as e:
        logger.error(f"Error getting dataset detail {dataset_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/create', methods=['POST'])
@login_required
def create_dataset():
    """创建数据集API"""
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        description = data.get('description', '')
        file_paths = data.get('file_paths', [])
        dataset_type = data.get('dataset_type', 'custom')
        
        if not name:
            return jsonify({
                'success': False,
                'error': '数据集名称不能为空'
            }), 400
        
        if not file_paths:
            return jsonify({
                'success': False,
                'error': '文件路径不能为空'
            }), 400
        
        dataset_id = dataset_manager.create_dataset_from_files(
            name, description, file_paths, dataset_type
        )
        
        if dataset_id:
            return jsonify({
                'success': True,
                'data': {'dataset_id': dataset_id}
            })
        else:
            return jsonify({
                'success': False,
                'error': '创建数据集失败，可能名称已存在或文件无效'
            }), 400
        
    except Exception as e:
        logger.error(f"Error creating dataset: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/<int:dataset_id>', methods=['PUT'])
@login_required
def update_dataset(dataset_id):
    """更新数据集API"""
    try:
        data = request.get_json()
        
        # 只允许更新特定字段
        allowed_fields = ['description', 'status']
        updates = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not updates:
            return jsonify({
                'success': False,
                'error': '没有有效的更新字段'
            }), 400
        
        success = dataset_manager.update_dataset_info(dataset_id, updates)
        
        if success:
            return jsonify({
                'success': True,
                'message': '数据集更新成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '数据集不存在或更新失败'
            }), 404
        
    except Exception as e:
        logger.error(f"Error updating dataset {dataset_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/<int:dataset_id>', methods=['DELETE'])
@login_required
def delete_dataset(dataset_id):
    """删除数据集API"""
    try:
        success = dataset_manager.delete_dataset_by_id(dataset_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '数据集删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '数据集不存在或删除失败'
            }), 404
        
    except Exception as e:
        logger.error(f"Error deleting dataset {dataset_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/search')
@login_required
def search_datasets():
    """搜索数据集API"""
    try:
        query = request.args.get('query', '').strip()
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '搜索查询不能为空'
            }), 400
        
        # 限制分页参数
        page = max(1, page)
        limit = min(100, max(1, limit))
        
        result = dataset_manager.search_datasets_by_query(query, page, limit)
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error searching datasets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/download', methods=['POST'])
@login_required
def download_dataset():
    """下载开源数据集API"""
    try:
        data = request.get_json()
        
        url = data.get('url', '').strip()
        name = data.get('name', '').strip()
        description = data.get('description', '')
        
        if not url or not name:
            return jsonify({
                'success': False,
                'error': 'URL和名称不能为空'
            }), 400
        
        # 启动下载任务
        task_id = dataset_downloader.start_download(url, name, description)
        
        if task_id:
            return jsonify({
                'success': True,
                'data': {'task_id': task_id}
            })
        else:
            return jsonify({
                'success': False,
                'error': '启动下载任务失败'
            }), 500
        
    except Exception as e:
        logger.error(f"Error starting dataset download: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/download/status/<task_id>')
@login_required
def get_download_status(task_id):
    """获取下载进度API"""
    try:
        status = dataset_downloader.get_download_progress(task_id)
        
        if status:
            return jsonify({
                'success': True,
                'data': status
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务不存在'
            }), 404
        
    except Exception as e:
        logger.error(f"Error getting download status {task_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/download/cancel/<task_id>', methods=['POST'])
@login_required
def cancel_download(task_id):
    """取消下载任务API"""
    try:
        success = dataset_downloader.cancel_download(task_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '下载任务已取消'
            })
        else:
            return jsonify({
                'success': False,
                'error': '任务不存在或无法取消'
            }), 404
        
    except Exception as e:
        logger.error(f"Error cancelling download {task_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/<int:dataset_id>/link-project', methods=['POST'])
@login_required
def link_dataset_to_project(dataset_id):
    """关联数据集到项目API"""
    try:
        data = request.get_json()
        project_name = data.get('project_name', '').strip()
        
        if not project_name:
            return jsonify({
                'success': False,
                'error': '项目名称不能为空'
            }), 400
        
        success = dataset_manager.link_to_project(dataset_id, project_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': '数据集关联成功'
            })
        else:
            return jsonify({
                'success': False,
                'error': '关联失败，可能数据集不存在或已关联'
            }), 400
        
    except Exception as e:
        logger.error(f"Error linking dataset {dataset_id} to project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/<int:dataset_id>/unlink-project', methods=['POST'])
@login_required
def unlink_dataset_from_project(dataset_id):
    """取消数据集与项目的关联API"""
    try:
        data = request.get_json()
        project_name = data.get('project_name', '').strip()
        
        if not project_name:
            return jsonify({
                'success': False,
                'error': '项目名称不能为空'
            }), 400
        
        success = dataset_manager.unlink_from_project(dataset_id, project_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': '数据集关联已取消'
            })
        else:
            return jsonify({
                'success': False,
                'error': '取消关联失败，可能关联不存在'
            }), 400
        
    except Exception as e:
        logger.error(f"Error unlinking dataset {dataset_id} from project: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/project/<project_name>')
@login_required
def get_project_datasets(project_name):
    """获取项目关联的数据集API"""
    try:
        datasets = dataset_manager.get_project_linked_datasets(project_name)
        
        return jsonify({
            'success': True,
            'data': datasets
        })
    except Exception as e:
        logger.error(f"Error getting project datasets for {project_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/<int:dataset_id>/validate')
@login_required
def validate_dataset(dataset_id):
    """验证数据集API"""
    try:
        dataset = get_dataset_by_id(dataset_id)
        if not dataset:
            return jsonify({
                'success': False,
                'error': '数据集不存在'
            }), 404
        
        validation_result = dataset_analyzer.validate_dataset(dataset.file_path)
        
        return jsonify({
            'success': True,
            'data': validation_result
        })
    except Exception as e:
        logger.error(f"Error validating dataset {dataset_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/public/search')
def search_public_datasets():
    """搜索公开数据集API（开源数据集搜索）"""
    try:
        query = request.args.get('query', '').strip()
        source = request.args.get('source', 'all')  # kaggle, github, huggingface, all
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '搜索查询不能为空'
            }), 400
        
        # 限制结果数量
        limit = min(50, max(1, limit))
        
        # 这里应该实现真正的公开数据集搜索
        # 为了演示，返回模拟数据
        mock_results = [
            {
                'name': f'{query}_dataset_1',
                'description': f'关于{query}的数据集1',
                'source': 'kaggle',
                'url': 'https://example.com/dataset1.zip',
                'size': '100MB',
                'format': 'COCO',
                'downloads': 1234
            },
            {
                'name': f'{query}_dataset_2', 
                'description': f'关于{query}的数据集2',
                'source': 'github',
                'url': 'https://example.com/dataset2.zip',
                'size': '50MB',
                'format': 'YOLO',
                'downloads': 567
            }
        ]
        
        filtered_results = mock_results
        if source != 'all':
            filtered_results = [r for r in mock_results if r['source'] == source]
        
        return jsonify({
            'success': True,
            'data': {
                'results': filtered_results[:limit],
                'total': len(filtered_results),
                'query': query,
                'source': source
            }
        })
    except Exception as e:
        logger.error(f"Error searching public datasets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/analyze/<int:dataset_id>')
@login_required
def analyze_dataset(dataset_id):
    """分析数据集API"""
    try:
        dataset = get_dataset_by_id(dataset_id)
        if not dataset:
            return jsonify({
                'success': False,
                'error': '数据集不存在'
            }), 404
        
        analysis_result = dataset_analyzer.analyze_structure(dataset.file_path)
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
    except Exception as e:
        logger.error(f"Error analyzing dataset {dataset_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 错误处理
@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': '请求的资源不存在'
    }), 404


@bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': '请求参数错误'
    }), 400


@bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500