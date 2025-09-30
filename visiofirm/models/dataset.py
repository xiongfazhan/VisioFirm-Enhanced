import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from visiofirm.config import get_cache_folder

class Dataset:
    """数据集模型类"""
    
    def __init__(self, dataset_id=None, name=None, description=None, 
                 dataset_type=None, source_url=None, file_path=None,
                 file_size=None, image_count=None, class_count=None,
                 annotation_format=None, created_at=None, updated_at=None,
                 status='ready'):
        self.dataset_id = dataset_id
        self.name = name
        self.description = description
        self.dataset_type = dataset_type  # 'custom', 'downloaded', 'imported'
        self.source_url = source_url
        self.file_path = file_path
        self.file_size = file_size
        self.image_count = image_count or 0
        self.class_count = class_count or 0
        self.annotation_format = annotation_format  # 'yolo', 'coco', 'pascal_voc', 'none'
        self.created_at = created_at
        self.updated_at = updated_at
        self.status = status  # 'downloading', 'ready', 'error'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'dataset_id': self.dataset_id,
            'name': self.name,
            'description': self.description,
            'dataset_type': self.dataset_type,
            'source_url': self.source_url,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'image_count': self.image_count,
            'class_count': self.class_count,
            'annotation_format': self.annotation_format,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建Dataset实例"""
        return cls(
            dataset_id=data.get('dataset_id'),
            name=data.get('name'),
            description=data.get('description'),
            dataset_type=data.get('dataset_type'),
            source_url=data.get('source_url'),
            file_path=data.get('file_path'),
            file_size=data.get('file_size'),
            image_count=data.get('image_count'),
            class_count=data.get('class_count'),
            annotation_format=data.get('annotation_format'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            status=data.get('status', 'ready')
        )


def get_dataset_db_path():
    """获取数据集数据库路径"""
    return os.path.join(get_cache_folder(), 'datasets.db')


def init_dataset_db():
    """初始化数据集数据库表"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 创建Datasets表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Datasets (
                dataset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                dataset_type TEXT NOT NULL,
                source_url TEXT,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                image_count INTEGER DEFAULT 0,
                class_count INTEGER DEFAULT 0,
                annotation_format TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'ready'
            )
        ''')
        
        # 创建Dataset_Classes表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Dataset_Classes (
                dataset_id INTEGER,
                class_name TEXT,
                PRIMARY KEY (dataset_id, class_name),
                FOREIGN KEY (dataset_id) REFERENCES Datasets(dataset_id) ON DELETE CASCADE
            )
        ''')
        
        # 创建Project_Datasets表（项目数据集关联）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Project_Datasets (
                project_name TEXT,
                dataset_id INTEGER,
                linked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_name, dataset_id),
                FOREIGN KEY (dataset_id) REFERENCES Datasets(dataset_id) ON DELETE CASCADE
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasets_type ON Datasets(dataset_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasets_status ON Datasets(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_datasets_name ON Datasets(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_datasets_project ON Project_Datasets(project_name)')
        
        conn.commit()


def create_dataset(name: str, description: str, dataset_type: str, file_path: str,
                  source_url: str = None, file_size: int = None, 
                  annotation_format: str = None) -> Optional[int]:
    """创建新数据集"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Datasets (name, description, dataset_type, source_url, 
                                    file_path, file_size, annotation_format)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, dataset_type, source_url, file_path, 
                  file_size, annotation_format))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None


def get_dataset_by_id(dataset_id: int) -> Optional[Dataset]:
    """根据ID获取数据集"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dataset_id, name, description, dataset_type, source_url, 
                   file_path, file_size, image_count, class_count, 
                   annotation_format, created_at, updated_at, status
            FROM Datasets WHERE dataset_id = ?
        ''', (dataset_id,))
        row = cursor.fetchone()
        if row:
            return Dataset(*row)
        return None


def get_dataset_by_name(name: str) -> Optional[Dataset]:
    """根据名称获取数据集"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT dataset_id, name, description, dataset_type, source_url, 
                   file_path, file_size, image_count, class_count, 
                   annotation_format, created_at, updated_at, status
            FROM Datasets WHERE name = ?
        ''', (name,))
        row = cursor.fetchone()
        if row:
            return Dataset(*row)
        return None


def get_datasets(page: int = 1, limit: int = 20, dataset_type: str = None) -> Tuple[List[Dataset], int]:
    """获取数据集列表"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # 构建查询条件
        where_clause = ''
        params = []
        if dataset_type:
            where_clause = 'WHERE dataset_type = ?'
            params.append(dataset_type)
        
        # 获取总数
        cursor.execute(f'SELECT COUNT(*) FROM Datasets {where_clause}', params)
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * limit
        cursor.execute(f'''
            SELECT dataset_id, name, description, dataset_type, source_url, 
                   file_path, file_size, image_count, class_count, 
                   annotation_format, created_at, updated_at, status
            FROM Datasets {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [limit, offset])
        
        datasets = [Dataset(*row) for row in cursor.fetchall()]
        return datasets, total


def update_dataset(dataset_id: int, updates: Dict) -> bool:
    """更新数据集信息"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            # 自动更新updated_at字段
            updates['updated_at'] = datetime.now().isoformat()
            
            set_clause = ', '.join(f"{key} = ?" for key in updates)
            values = list(updates.values()) + [dataset_id]
            
            cursor.execute(f'''
                UPDATE Datasets
                SET {set_clause}
                WHERE dataset_id = ?
            ''', values)
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False


def delete_dataset(dataset_id: int) -> bool:
    """删除数据集"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM Datasets WHERE dataset_id = ?', (dataset_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False


def search_datasets(query: str, page: int = 1, limit: int = 20) -> Tuple[List[Dataset], int]:
    """搜索数据集"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        search_pattern = f'%{query}%'
        
        # 获取总数
        cursor.execute('''
            SELECT COUNT(*) FROM Datasets 
            WHERE name LIKE ? OR description LIKE ?
        ''', (search_pattern, search_pattern))
        total = cursor.fetchone()[0]
        
        # 获取分页数据
        offset = (page - 1) * limit
        cursor.execute('''
            SELECT dataset_id, name, description, dataset_type, source_url, 
                   file_path, file_size, image_count, class_count, 
                   annotation_format, created_at, updated_at, status
            FROM Datasets 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (search_pattern, search_pattern, limit, offset))
        
        datasets = [Dataset(*row) for row in cursor.fetchall()]
        return datasets, total


def add_dataset_classes(dataset_id: int, class_names: List[str]) -> bool:
    """添加数据集类别"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            for class_name in class_names:
                cursor.execute('''
                    INSERT OR IGNORE INTO Dataset_Classes (dataset_id, class_name)
                    VALUES (?, ?)
                ''', (dataset_id, class_name))
            conn.commit()
            return True
        except sqlite3.Error:
            return False


def get_dataset_classes(dataset_id: int) -> List[str]:
    """获取数据集类别"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT class_name FROM Dataset_Classes WHERE dataset_id = ?
            ORDER BY class_name
        ''', (dataset_id,))
        return [row[0] for row in cursor.fetchall()]


def link_dataset_to_project(dataset_id: int, project_name: str) -> bool:
    """关联数据集到项目"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO Project_Datasets (project_name, dataset_id)
                VALUES (?, ?)
            ''', (project_name, dataset_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False


def unlink_dataset_from_project(dataset_id: int, project_name: str) -> bool:
    """取消数据集与项目的关联"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM Project_Datasets 
                WHERE project_name = ? AND dataset_id = ?
            ''', (project_name, dataset_id))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False


def get_project_datasets(project_name: str) -> List[Dataset]:
    """获取项目关联的数据集"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.dataset_id, d.name, d.description, d.dataset_type, d.source_url, 
                   d.file_path, d.file_size, d.image_count, d.class_count, 
                   d.annotation_format, d.created_at, d.updated_at, d.status
            FROM Datasets d
            JOIN Project_Datasets pd ON d.dataset_id = pd.dataset_id
            WHERE pd.project_name = ?
            ORDER BY pd.linked_at DESC
        ''', (project_name,))
        return [Dataset(*row) for row in cursor.fetchall()]


def get_dataset_projects(dataset_id: int) -> List[str]:
    """获取使用该数据集的项目列表"""
    db_path = get_dataset_db_path()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT project_name FROM Project_Datasets 
            WHERE dataset_id = ?
            ORDER BY linked_at DESC
        ''', (dataset_id,))
        return [row[0] for row in cursor.fetchall()]