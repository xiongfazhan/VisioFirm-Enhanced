import os
import requests
import threading
import time
import uuid
import zipfile
import tarfile
import shutil
from typing import Dict, Optional, Any
from urllib.parse import urlparse
from datetime import datetime
from tqdm import tqdm
import logging

from visiofirm.config import PROJECTS_FOLDER
from visiofirm.models.dataset import create_dataset, update_dataset
from visiofirm.utils.dataset_service import DatasetAnalyzer

# Configure logging with less verbose output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class DatasetDownloader:
    """数据集下载服务类"""
    
    def __init__(self):
        self.download_tasks = {}  # 存储下载任务状态
        self.temp_folder = os.path.join(PROJECTS_FOLDER, 'datasets', 'temp')
        self.download_folder = os.path.join(PROJECTS_FOLDER, 'datasets', 'downloaded')
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.temp_folder, exist_ok=True)
        os.makedirs(self.download_folder, exist_ok=True)
    
    def start_download(self, url: str, name: str, description: str = '') -> Optional[str]:
        """启动数据集下载任务"""
        try:
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 初始化任务状态
            self.download_tasks[task_id] = {
                'status': 'initializing',
                'progress': 0.0,
                'downloaded_size': 0,
                'total_size': 0,
                'speed': '0 B/s',
                'eta': 'unknown',
                'message': '正在初始化下载任务...',
                'url': url,
                'name': name,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'error': None,
                'dataset_id': None
            }
            
            # 启动下载线程
            download_thread = threading.Thread(
                target=self._download_worker,
                args=(task_id, url, name, description),
                daemon=True
            )
            download_thread.start()
            
            logger.info(f"Started download task {task_id} for {name}")
            return task_id
            
        except Exception as e:
            logger.error(f"Error starting download task: {e}")
            return None
    
    def _download_worker(self, task_id: str, url: str, name: str, description: str):
        """下载工作线程"""
        try:
            self._update_task_status(task_id, 'downloading', 0.0, message='正在连接服务器...')
            
            # 获取文件信息
            response = requests.head(url, allow_redirects=True, timeout=30)
            if response.status_code != 200:
                raise Exception(f"无法访问下载链接: HTTP {response.status_code}")
            
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                logger.warning(f"Cannot determine file size for {url}")
            
            # 确定文件名
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or f"{name}.zip"
            if not any(filename.endswith(ext) for ext in ['.zip', '.tar', '.tar.gz', '.rar']):
                filename += '.zip'
            
            temp_path = os.path.join(self.temp_folder, f"{task_id}_{filename}")
            
            # 开始下载
            self._update_task_status(
                task_id, 'downloading', 0.0, 
                total_size=total_size,
                message='正在下载数据集文件...'
            )
            
            downloaded_size = self._download_file_with_progress(url, temp_path, task_id, total_size)
            
            if self.download_tasks[task_id]['status'] == 'cancelled':
                self._cleanup_temp_files(temp_path)
                return
            
            # 下载完成，开始解压
            self._update_task_status(task_id, 'extracting', 90.0, message='正在解压数据集...')
            
            dataset_dir = os.path.join(self.download_folder, name)
            if os.path.exists(dataset_dir):
                dataset_dir = f"{dataset_dir}_{int(time.time())}"
            
            os.makedirs(dataset_dir, exist_ok=True)
            
            self._extract_archive(temp_path, dataset_dir)
            
            # 分析数据集
            self._update_task_status(task_id, 'analyzing', 95.0, message='正在分析数据集结构...')
            
            analyzer = DatasetAnalyzer()
            analysis_result = analyzer.analyze_structure(dataset_dir)
            
            # 创建数据集记录
            dataset_id = create_dataset(
                name=name,
                description=description,
                dataset_type='downloaded',
                source_url=url,
                file_path=dataset_dir,
                file_size=downloaded_size,
                annotation_format=analysis_result.get('annotation_format', 'none')
            )
            
            if dataset_id:
                # 更新统计信息
                update_dataset(dataset_id, {
                    'image_count': analysis_result.get('image_count', 0),
                    'class_count': analysis_result.get('class_count', 0)
                })
                
                self.download_tasks[task_id]['dataset_id'] = dataset_id
            
            # 清理临时文件
            self._cleanup_temp_files(temp_path)
            
            # 下载完成
            self._update_task_status(
                task_id, 'completed', 100.0,
                message=f'数据集下载完成！共{analysis_result.get("image_count", 0)}张图片'
            )
            
            logger.info(f"Download task {task_id} completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download task {task_id} failed: {error_msg}")
            
            # 清理文件
            if 'temp_path' in locals():
                self._cleanup_temp_files(temp_path)
            if 'dataset_dir' in locals() and os.path.exists(dataset_dir):
                shutil.rmtree(dataset_dir, ignore_errors=True)
            
            self._update_task_status(
                task_id, 'error', 0.0,
                message=f'下载失败: {error_msg}',
                error=error_msg
            )
    
    def _download_file_with_progress(self, url: str, file_path: str, task_id: str, total_size: int) -> int:
        """带进度条的文件下载"""
        chunk_size = 8192
        downloaded_size = 0
        start_time = time.time()
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            with tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc="下载进度",
                disable=True  # 禁用tqdm的输出，我们用自己的进度更新
            ) as pbar:
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self.download_tasks.get(task_id, {}).get('status') == 'cancelled':
                        break
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        pbar.update(len(chunk))
                        
                        # 更新进度
                        if time.time() - start_time > 0:
                            speed = downloaded_size / (time.time() - start_time)
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 85  # 85%用于下载
                                eta_seconds = (total_size - downloaded_size) / speed if speed > 0 else 0
                                eta = self._format_time(eta_seconds)
                            else:
                                progress = 0
                                eta = 'unknown'
                            
                            self._update_task_status(
                                task_id, 'downloading', progress,
                                downloaded_size=downloaded_size,
                                total_size=total_size,
                                speed=self._format_size(speed) + '/s',
                                eta=eta
                            )
        
        return downloaded_size
    
    def _extract_archive(self, archive_path: str, extract_path: str):
        """解压归档文件"""
        ext = os.path.splitext(archive_path)[1].lower()
        
        if ext == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        elif ext in ['.tar', '.gz']:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
        else:
            raise Exception(f"不支持的归档格式: {ext}")
        
        # 检查解压后的结构，如果只有一个子目录，则将其内容移到上级
        items = os.listdir(extract_path)
        if len(items) == 1 and os.path.isdir(os.path.join(extract_path, items[0])):
            sub_dir = os.path.join(extract_path, items[0])
            temp_dir = extract_path + '_temp'
            os.rename(sub_dir, temp_dir)
            shutil.rmtree(extract_path)
            os.rename(temp_dir, extract_path)
    
    def _update_task_status(self, task_id: str, status: str, progress: float,
                          downloaded_size: int = None, total_size: int = None,
                          speed: str = None, eta: str = None, message: str = None,
                          error: str = None):
        """更新任务状态"""
        if task_id in self.download_tasks:
            task = self.download_tasks[task_id]
            task['status'] = status
            task['progress'] = progress
            
            if downloaded_size is not None:
                task['downloaded_size'] = downloaded_size
            if total_size is not None:
                task['total_size'] = total_size
            if speed is not None:
                task['speed'] = speed
            if eta is not None:
                task['eta'] = eta
            if message is not None:
                task['message'] = message
            if error is not None:
                task['error'] = error
            
            task['updated_at'] = datetime.now().isoformat()
    
    def get_download_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取下载进度"""
        return self.download_tasks.get(task_id)
    
    def cancel_download(self, task_id: str) -> bool:
        """取消下载任务"""
        if task_id in self.download_tasks:
            task = self.download_tasks[task_id]
            if task['status'] in ['downloading', 'extracting', 'analyzing']:
                self._update_task_status(task_id, 'cancelled', 0.0, message='下载已取消')
                logger.info(f"Cancelled download task {task_id}")
                return True
        return False
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的任务"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.download_tasks.items():
            if task['status'] in ['completed', 'error', 'cancelled']:
                created_at = datetime.fromisoformat(task['created_at'])
                age_hours = (current_time - created_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.download_tasks[task_id]
            logger.info(f"Cleaned up old task {task_id}")
    
    def _cleanup_temp_files(self, file_path: str):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
    
    def _format_size(self, size_bytes: float) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        
        while size_bytes >= 1024 and unit_index < len(units) - 1:
            size_bytes /= 1024
            unit_index += 1
        
        return f"{size_bytes:.1f} {units[unit_index]}"
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds <= 0:
            return "unknown"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有下载任务"""
        return self.download_tasks.copy()
    
    def resume_download(self, task_id: str) -> bool:
        """恢复下载任务（断点续传）"""
        task = self.download_tasks.get(task_id)
        if not task or task['status'] != 'error':
            return False
        
        try:
            # 重新启动下载
            download_thread = threading.Thread(
                target=self._download_worker,
                args=(task_id, task['url'], task['name'], task['description']),
                daemon=True
            )
            download_thread.start()
            
            logger.info(f"Resumed download task {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming download task {task_id}: {e}")
            return False


class DatasetDownloadManager:
    """数据集下载管理器"""
    
    def __init__(self):
        self.downloader = DatasetDownloader()
        self._start_cleanup_scheduler()
    
    def _start_cleanup_scheduler(self):
        """启动清理调度器"""
        def cleanup_worker():
            while True:
                time.sleep(3600)  # 每小时清理一次
                self.downloader.cleanup_completed_tasks()
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def download_from_url(self, url: str, name: str, description: str = '') -> Optional[str]:
        """从URL下载数据集"""
        return self.downloader.start_download(url, name, description)
    
    def get_download_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取下载状态"""
        return self.downloader.get_download_progress(task_id)
    
    def cancel_download(self, task_id: str) -> bool:
        """取消下载"""
        return self.downloader.cancel_download(task_id)
    
    def list_downloads(self) -> Dict[str, Dict[str, Any]]:
        """列出所有下载任务"""
        return self.downloader.get_all_tasks()
    
    def resume_download(self, task_id: str) -> bool:
        """恢复下载"""
        return self.downloader.resume_download(task_id)


# 全局下载管理器实例
download_manager = DatasetDownloadManager()