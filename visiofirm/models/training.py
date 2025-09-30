import sqlite3
import os
import json
import logging
from datetime import datetime
from visiofirm.config import PROJECTS_FOLDER

# Configure logging with less verbose output - 强制设置根logger级别
logging.basicConfig(level=logging.WARNING, force=True)
logger = logging.getLogger(__name__)
# 额外确保当前模块的logger级别正确
logger.setLevel(logging.WARNING)

class TrainingTask:
    def __init__(self, project_name, project_path):
        self.project_name = project_name
        self.project_path = project_path
        self.db_path = os.path.join(project_path, 'config.db')
        self._initialize_training_db()

    def _initialize_training_db(self):
        """初始化训练相关的数据库表"""
        try:
            # 确保数据库目录存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # 检查数据库文件是否可访问
            if not os.path.exists(self.db_path):
                # 如果数据库文件不存在，创建一个基本的项目数据库
                from visiofirm.models.project import Project
                temp_project = Project(self.project_name, "", "detection", self.project_path)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建训练任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_name TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        dataset_split TEXT NOT NULL,
                        config TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        model_path TEXT,
                        metrics TEXT
                    )
                ''')
                
                # 创建训练配置表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_name TEXT NOT NULL,
                        model_type TEXT NOT NULL,
                        epochs INTEGER DEFAULT 100,
                        batch_size INTEGER DEFAULT 16,
                        learning_rate REAL DEFAULT 0.001,
                        image_size INTEGER DEFAULT 640,
                        device TEXT DEFAULT 'auto',
                        optimizer TEXT DEFAULT 'auto',
                        augmentation TEXT DEFAULT '{}',
                        other_params TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建训练日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS training_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER,
                        epoch INTEGER,
                        loss REAL,
                        accuracy REAL,
                        val_loss REAL,
                        val_accuracy REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_id) REFERENCES training_tasks (id)
                    )
                ''')
                
                conn.commit()
                # 初始化成功，不输出日志避免重复信息
                
        except Exception as e:
            logger.error(f"Failed to initialize training database: {e}")
            # 尝试修复权限问题
            try:
                if os.path.exists(self.db_path):
                    os.chmod(self.db_path, 0o666)
                    logger.info(f"已修复数据库文件权限: {self.db_path}")
                    # 重试初始化
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS training_tasks (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                task_name TEXT NOT NULL,
                                model_type TEXT NOT NULL,
                                dataset_split TEXT NOT NULL,
                                config TEXT NOT NULL,
                                status TEXT DEFAULT 'pending',
                                progress INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                started_at TIMESTAMP,
                                completed_at TIMESTAMP,
                                error_message TEXT,
                                model_path TEXT,
                                metrics TEXT
                            )
                        ''')
                        conn.commit()
                        # 数据库修复成功，不输出重复日志
                else:
                    raise
            except Exception as retry_error:
                logger.error(f"Failed to fix database permissions: {retry_error}")
                raise e

    def create_training_task(self, task_name, model_type, dataset_split, config):
        """创建新的训练任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO training_tasks 
                    (task_name, model_type, dataset_split, config, status)
                    VALUES (?, ?, ?, ?, 'pending')
                ''', (task_name, model_type, json.dumps(dataset_split), json.dumps(config)))
                
                task_id = cursor.lastrowid
                conn.commit()
                # 任务创建成功，不输出日志避免干扰
                return task_id
                
        except Exception as e:
            logger.error(f"Failed to create training task: {e}")
            raise

    def get_training_tasks(self):
        """获取所有训练任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, task_name, model_type, status, progress, 
                           created_at, started_at, completed_at, error_message
                    FROM training_tasks 
                    ORDER BY created_at DESC
                ''')
                
                tasks = []
                for row in cursor.fetchall():
                    tasks.append({
                        'id': row[0],
                        'task_name': row[1],
                        'model_type': row[2],
                        'status': row[3],
                        'progress': row[4],
                        'created_at': row[5],
                        'started_at': row[6],
                        'completed_at': row[7],
                        'error_message': row[8]
                    })
                
                return tasks
                
        except Exception as e:
            logger.error(f"Failed to get training tasks: {e}")
            return []

    def update_task_status(self, task_id, status, progress=None, error_message=None, model_path=None, metrics=None):
        """更新训练任务状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ['status = ?']
                update_values = [status]
                
                if progress is not None:
                    update_fields.append('progress = ?')
                    update_values.append(progress)
                
                if error_message is not None:
                    update_fields.append('error_message = ?')
                    update_values.append(error_message)
                
                if model_path is not None:
                    update_fields.append('model_path = ?')
                    update_values.append(model_path)
                
                if metrics is not None:
                    update_fields.append('metrics = ?')
                    update_values.append(json.dumps(metrics))
                
                if status == 'running' and progress == 0:
                    update_fields.append('started_at = ?')
                    update_values.append(datetime.now().isoformat())
                elif status == 'completed':
                    update_fields.append('completed_at = ?')
                    update_values.append(datetime.now().isoformat())
                
                update_values.append(task_id)
                
                query = f"UPDATE training_tasks SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, update_values)
                conn.commit()
                
                # 任务状态更新成功，不输出日志避免干扰
                
        except Exception as e:
            logger.error(f"Failed to update task status: {e}")
            raise

    def get_task_details(self, task_id):
        """获取训练任务详细信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM training_tasks WHERE id = ?
                ''', (task_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'task_name': row[1],
                        'model_type': row[2],
                        'dataset_split': json.loads(row[3]) if row[3] else {},
                        'config': json.loads(row[4]) if row[4] else {},
                        'status': row[5],
                        'progress': row[6],
                        'created_at': row[7],
                        'started_at': row[8],
                        'completed_at': row[9],
                        'error_message': row[10],
                        'model_path': row[11],
                        'metrics': json.loads(row[12]) if row[12] else {}
                    }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get task details: {e}")
            return None

    def save_training_config(self, config_name, model_type, epochs, batch_size, learning_rate, 
                           image_size, device, optimizer, augmentation, other_params):
        """保存训练配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO training_configs 
                    (config_name, model_type, epochs, batch_size, learning_rate, 
                     image_size, device, optimizer, augmentation, other_params)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (config_name, model_type, epochs, batch_size, learning_rate,
                      image_size, device, optimizer, json.dumps(augmentation), 
                      json.dumps(other_params)))
                
                config_id = cursor.lastrowid
                conn.commit()
                # 配置保存成功，不输出日志避免干扰
                return config_id
                
        except Exception as e:
            logger.error(f"Failed to save training config: {e}")
            raise

    def get_training_configs(self):
        """获取所有训练配置"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM training_configs ORDER BY created_at DESC
                ''')
                
                configs = []
                for row in cursor.fetchall():
                    configs.append({
                        'id': row[0],
                        'config_name': row[1],
                        'model_type': row[2],
                        'epochs': row[3],
                        'batch_size': row[4],
                        'learning_rate': row[5],
                        'image_size': row[6],
                        'device': row[7],
                        'optimizer': row[8],
                        'augmentation': json.loads(row[9]) if row[9] else {},
                        'other_params': json.loads(row[10]) if row[10] else {},
                        'created_at': row[11]
                    })
                
                return configs
                
        except Exception as e:
            logger.error(f"Failed to get training configs: {e}")
            return []

    def log_training_progress(self, task_id, epoch, loss, accuracy=None, val_loss=None, val_accuracy=None):
        """记录训练进度"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO training_logs 
                    (task_id, epoch, loss, accuracy, val_loss, val_accuracy)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_id, epoch, loss, accuracy, val_loss, val_accuracy))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to log training progress: {e}")

    def get_training_logs(self, task_id):
        """获取训练日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT epoch, loss, accuracy, val_loss, val_accuracy, timestamp
                    FROM training_logs 
                    WHERE task_id = ? 
                    ORDER BY epoch
                ''', (task_id,))
                
                logs = []
                for row in cursor.fetchall():
                    logs.append({
                        'epoch': row[0],
                        'loss': row[1],
                        'accuracy': row[2],
                        'val_loss': row[3],
                        'val_accuracy': row[4],
                        'timestamp': row[5]
                    })
                
                return logs
                
        except Exception as e:
            logger.error(f"Failed to get training logs: {e}")
            return []

    def delete_training_task(self, task_id):
        """删除训练任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 删除相关日志
                cursor.execute('DELETE FROM training_logs WHERE task_id = ?', (task_id,))
                
                # 删除任务
                cursor.execute('DELETE FROM training_tasks WHERE id = ?', (task_id,))
                
                conn.commit()
                logger.info(f"Deleted training task: {task_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete training task: {e}")
            raise