"""
API辅助工具模块
提供标准化的API响应格式和错误处理机制
"""

from flask import jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class APIResponse:
    """标准化API响应类"""
    
    @staticmethod
    def success(data=None, message="操作成功", code=200):
        """
        成功响应
        
        Args:
            data: 返回的数据
            message: 成功消息
            code: HTTP状态码
            
        Returns:
            tuple: (响应体, 状态码)
        """
        response = {
            'success': True,
            'message': message,
            'data': data
        }
        return jsonify(response), code
    
    @staticmethod
    def error(message="操作失败", code=400, error_type="BadRequest", details=None):
        """
        错误响应
        
        Args:
            message: 错误消息
            code: HTTP状态码
            error_type: 错误类型
            details: 详细错误信息
            
        Returns:
            tuple: (响应体, 状态码)
        """
        response = {
            'success': False,
            'error': {
                'type': error_type,
                'message': message
            }
        }
        if details:
            response['error']['details'] = details
        
        logger.error(f"API Error [{code}]: {message}")
        return jsonify(response), code
    
    @staticmethod
    def created(data=None, message="创建成功", resource_url=None):
        """
        创建成功响应 (201)
        
        Args:
            data: 返回的数据
            message: 成功消息
            resource_url: 新资源的URL
            
        Returns:
            tuple: (响应体, 状态码, 头部)
        """
        response = {
            'success': True,
            'message': message,
            'data': data
        }
        headers = {}
        if resource_url:
            headers['Location'] = resource_url
        
        return jsonify(response), 201, headers
    
    @staticmethod
    def no_content():
        """
        无内容响应 (204)
        用于删除操作等
        
        Returns:
            tuple: ('', 状态码)
        """
        return '', 204


class APIError(Exception):
    """自定义API异常类"""
    
    def __init__(self, message, code=400, error_type="BadRequest", details=None):
        self.message = message
        self.code = code
        self.error_type = error_type
        self.details = details
        super().__init__(self.message)


def handle_api_errors(f):
    """
    API错误处理装饰器
    自动捕获异常并返回标准化错误响应
    
    Usage:
        @bp.route('/api/endpoint')
        @handle_api_errors
        def my_endpoint():
            # 可以直接抛出APIError异常
            raise APIError("参数错误", code=400)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            return APIResponse.error(
                message=e.message,
                code=e.code,
                error_type=e.error_type,
                details=e.details
            )
        except ValueError as e:
            return APIResponse.error(
                message=str(e),
                code=400,
                error_type="ValueError"
            )
        except FileNotFoundError as e:
            return APIResponse.error(
                message="资源不存在",
                code=404,
                error_type="NotFound",
                details=str(e)
            )
        except PermissionError as e:
            return APIResponse.error(
                message="权限不足",
                code=403,
                error_type="Forbidden",
                details=str(e)
            )
        except Exception as e:
            logger.exception(f"Unexpected error in {f.__name__}: {str(e)}")
            return APIResponse.error(
                message="服务器内部错误",
                code=500,
                error_type="InternalServerError",
                details=str(e) if logger.level == logging.DEBUG else None
            )
    
    return decorated_function


def validate_required_fields(data, required_fields):
    """
    验证必需字段
    
    Args:
        data: 请求数据字典
        required_fields: 必需字段列表
        
    Raises:
        APIError: 如果缺少必需字段
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    if missing_fields:
        raise APIError(
            message=f"缺少必需字段: {', '.join(missing_fields)}",
            code=400,
            error_type="ValidationError",
            details={'missing_fields': missing_fields}
        )


def validate_file_upload(file, allowed_extensions=None, max_size_mb=None):
    """
    验证文件上传
    
    Args:
        file: Flask文件对象
        allowed_extensions: 允许的文件扩展名列表
        max_size_mb: 最大文件大小（MB）
        
    Raises:
        APIError: 如果文件验证失败
    """
    if not file or file.filename == '':
        raise APIError(
            message="未提供文件",
            code=400,
            error_type="ValidationError"
        )
    
    if allowed_extensions:
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            raise APIError(
                message=f"不支持的文件类型，仅支持: {', '.join(allowed_extensions)}",
                code=400,
                error_type="ValidationError",
                details={'allowed_extensions': allowed_extensions}
            )
    
    if max_size_mb:
        # Flask会自动限制文件大小，这里只是额外检查
        file.seek(0, 2)  # 移动到文件末尾
        size = file.tell()
        file.seek(0)  # 重置到开始
        if size > max_size_mb * 1024 * 1024:
            raise APIError(
                message=f"文件大小超过限制（最大{max_size_mb}MB）",
                code=413,
                error_type="PayloadTooLarge"
            )


def paginate_response(items, page=1, per_page=20):
    """
    分页响应
    
    Args:
        items: 所有项目列表
        page: 当前页码（从1开始）
        per_page: 每页项目数
        
    Returns:
        dict: 包含分页信息的字典
    """
    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_next': end < total,
            'has_prev': page > 1
        }
    }

