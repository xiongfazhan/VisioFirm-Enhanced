import os
import shutil
import json
import threading
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from PIL import Image
from visiofirm.config import PROJECTS_FOLDER, VALID_IMAGE_EXTENSIONS
from visiofirm.models.dataset import (
    Dataset, create_dataset, get_dataset_by_id, get_datasets, 
    update_dataset, delete_dataset, search_datasets, add_dataset_classes,
    get_dataset_classes, link_dataset_to_project, unlink_dataset_from_project,
    get_project_datasets, get_dataset_projects
)
import logging

# Configure logging with less verbose output
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class DatasetManager:
    """数据集管理服务类"""
    
    def __init__(self):
        self.datasets_folder = os.path.join(PROJECTS_FOLDER, 'datasets')
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        os.makedirs(self.datasets_folder, exist_ok=True)
        os.makedirs(os.path.join(self.datasets_folder, 'downloaded'), exist_ok=True)
        os.makedirs(os.path.join(self.datasets_folder, 'imported'), exist_ok=True)
        os.makedirs(os.path.join(self.datasets_folder, 'temp'), exist_ok=True)
    
    def create_dataset_from_files(self, name: str, description: str, 
                                file_paths: List[str], dataset_type: str = 'custom') -> Optional[int]:
        """从文件列表创建数据集"""
        try:
            # 创建数据集目录
            dataset_dir = os.path.join(self.datasets_folder, 'imported', name)
            os.makedirs(dataset_dir, exist_ok=True)
            images_dir = os.path.join(dataset_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # 复制文件到数据集目录
            valid_images = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    ext = os.path.splitext(filename)[1].lower()
                    
                    if ext in VALID_IMAGE_EXTENSIONS:
                        dest_path = os.path.join(images_dir, filename)
                        shutil.copy2(file_path, dest_path)
                        valid_images.append(dest_path)
            
            if not valid_images:
                shutil.rmtree(dataset_dir, ignore_errors=True)
                return None
            
            # 分析数据集信息
            analyzer = DatasetAnalyzer()
            info = analyzer.analyze_structure(dataset_dir)
            
            # 创建数据集记录
            dataset_id = create_dataset(
                name=name,
                description=description,
                dataset_type=dataset_type,
                file_path=dataset_dir,
                file_size=info.get('total_size', 0),
                annotation_format=info.get('annotation_format', 'none')
            )
            
            if dataset_id:
                # 更新统计信息
                self._update_dataset_statistics(dataset_id, dataset_dir)
                logger.info(f"Created dataset {name} with {len(valid_images)} images")
                return dataset_id
            
        except Exception as e:
            logger.error(f"Error creating dataset {name}: {e}")
            if 'dataset_dir' in locals():
                shutil.rmtree(dataset_dir, ignore_errors=True)
        
        return None
    
    def get_dataset_list(self, page: int = 1, limit: int = 20, 
                        dataset_type: str = None) -> Dict[str, Any]:
        """获取数据集列表"""
        datasets, total = get_datasets(page, limit, dataset_type)
        
        dataset_list = []
        for dataset in datasets:
            dataset_dict = dataset.to_dict()
            # 添加类别信息
            dataset_dict['classes'] = get_dataset_classes(dataset.dataset_id)
            dataset_list.append(dataset_dict)
        
        return {
            'datasets': dataset_list,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit
        }
    
    def get_dataset_detail(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """获取数据集详情"""
        dataset = get_dataset_by_id(dataset_id)
        if not dataset:
            return None
        
        dataset_dict = dataset.to_dict()
        dataset_dict['classes'] = get_dataset_classes(dataset_id)
        dataset_dict['projects'] = get_dataset_projects(dataset_id)
        
        # 添加样本预览
        if os.path.exists(dataset.file_path):
            dataset_dict['sample_images'] = self._get_sample_images(dataset.file_path, limit=6)
        
        return dataset_dict
    
    def update_dataset_info(self, dataset_id: int, updates: Dict[str, Any]) -> bool:
        """更新数据集信息"""
        return update_dataset(dataset_id, updates)
    
    def delete_dataset_by_id(self, dataset_id: int) -> bool:
        """删除数据集"""
        dataset = get_dataset_by_id(dataset_id)
        if not dataset:
            return False
        
        try:
            # 删除文件
            if os.path.exists(dataset.file_path):
                shutil.rmtree(dataset.file_path, ignore_errors=True)
            
            # 删除数据库记录
            return delete_dataset(dataset_id)
        except Exception as e:
            logger.error(f"Error deleting dataset {dataset_id}: {e}")
            return False
    
    def search_datasets_by_query(self, query: str, page: int = 1, 
                               limit: int = 20) -> Dict[str, Any]:
        """搜索数据集"""
        datasets, total = search_datasets(query, page, limit)
        
        dataset_list = []
        for dataset in datasets:
            dataset_dict = dataset.to_dict()
            dataset_dict['classes'] = get_dataset_classes(dataset.dataset_id)
            dataset_list.append(dataset_dict)
        
        return {
            'datasets': dataset_list,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': (total + limit - 1) // limit,
            'query': query
        }
    
    def link_to_project(self, dataset_id: int, project_name: str) -> bool:
        """关联数据集到项目"""
        return link_dataset_to_project(dataset_id, project_name)
    
    def unlink_from_project(self, dataset_id: int, project_name: str) -> bool:
        """取消数据集与项目的关联"""
        return unlink_dataset_from_project(dataset_id, project_name)
    
    def get_project_linked_datasets(self, project_name: str) -> List[Dict[str, Any]]:
        """获取项目关联的数据集"""
        datasets = get_project_datasets(project_name)
        
        dataset_list = []
        for dataset in datasets:
            dataset_dict = dataset.to_dict()
            dataset_dict['classes'] = get_dataset_classes(dataset.dataset_id)
            dataset_list.append(dataset_dict)
        
        return dataset_list
    
    def _update_dataset_statistics(self, dataset_id: int, dataset_path: str):
        """更新数据集统计信息"""
        try:
            analyzer = DatasetAnalyzer()
            info = analyzer.analyze_structure(dataset_path)
            
            updates = {
                'image_count': info.get('image_count', 0),
                'class_count': info.get('class_count', 0),
                'file_size': info.get('total_size', 0)
            }
            
            update_dataset(dataset_id, updates)
            
            # 添加类别信息
            if info.get('classes'):
                add_dataset_classes(dataset_id, info['classes'])
                
        except Exception as e:
            logger.error(f"Error updating dataset statistics for {dataset_id}: {e}")
    
    def _get_sample_images(self, dataset_path: str, limit: int = 6) -> List[str]:
        """获取数据集样本图片"""
        sample_images = []
        images_dir = os.path.join(dataset_path, 'images')
        
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir)[:limit]:
                if os.path.splitext(filename)[1].lower() in VALID_IMAGE_EXTENSIONS:
                    relative_path = os.path.join('datasets', 
                                                os.path.basename(dataset_path), 
                                                'images', filename)
                    sample_images.append(f'/projects/{relative_path}')
        
        return sample_images


class DatasetAnalyzer:
    """数据集分析服务类"""
    
    def analyze_structure(self, dataset_path: str) -> Dict[str, Any]:
        """分析数据集结构"""
        info = {
            'image_count': 0,
            'class_count': 0,
            'total_size': 0,
            'annotation_format': 'none',
            'classes': []
        }
        
        try:
            # 分析图片
            images_dir = os.path.join(dataset_path, 'images')
            if os.path.exists(images_dir):
                info['image_count'] = self._count_images(images_dir)
                info['total_size'] = self._calculate_directory_size(images_dir)
            
            # 检测标注格式
            annotation_format = self._detect_annotation_format(dataset_path)
            info['annotation_format'] = annotation_format
            
            # 提取类别
            classes = self._extract_classes(dataset_path, annotation_format)
            info['classes'] = classes
            info['class_count'] = len(classes)
            
        except Exception as e:
            logger.error(f"Error analyzing dataset {dataset_path}: {e}")
        
        return info
    
    def _count_images(self, images_dir: str) -> int:
        """统计图片数量"""
        count = 0
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if os.path.splitext(filename)[1].lower() in VALID_IMAGE_EXTENSIONS:
                    image_path = os.path.join(images_dir, filename)
                    if self._is_valid_image(image_path):
                        count += 1
        return count
    
    def _calculate_directory_size(self, directory: str) -> int:
        """计算目录总大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    pass
        return total_size
    
    def _detect_annotation_format(self, dataset_path: str) -> str:
        """检测标注格式"""
        annotations_dir = os.path.join(dataset_path, 'annotations')
        
        # 检查COCO格式
        for filename in ['annotations.json', 'instances.json', 'train.json', 'val.json']:
            if os.path.exists(os.path.join(annotations_dir, filename)):
                return 'coco'
        
        # 检查YOLO格式
        if os.path.exists(annotations_dir):
            for filename in os.listdir(annotations_dir):
                if filename.endswith('.txt'):
                    return 'yolo'
        
        # 检查Pascal VOC格式
        if os.path.exists(os.path.join(annotations_dir, 'xmls')):
            return 'pascal_voc'
        
        return 'none'
    
    def _extract_classes(self, dataset_path: str, annotation_format: str) -> List[str]:
        """提取类别信息"""
        classes = []
        
        try:
            if annotation_format == 'coco':
                classes = self._extract_coco_classes(dataset_path)
            elif annotation_format == 'yolo':
                classes = self._extract_yolo_classes(dataset_path)
            elif annotation_format == 'pascal_voc':
                classes = self._extract_voc_classes(dataset_path)
        except Exception as e:
            logger.error(f"Error extracting classes: {e}")
        
        return sorted(list(set(classes)))
    
    def _extract_coco_classes(self, dataset_path: str) -> List[str]:
        """提取COCO格式类别"""
        classes = []
        annotations_dir = os.path.join(dataset_path, 'annotations')
        
        for filename in ['annotations.json', 'instances.json', 'train.json', 'val.json']:
            json_path = os.path.join(annotations_dir, filename)
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'categories' in data:
                            classes.extend([cat['name'] for cat in data['categories']])
                            break
                except Exception:
                    continue
        
        return classes
    
    def _extract_yolo_classes(self, dataset_path: str) -> List[str]:
        """提取YOLO格式类别"""
        classes = []
        
        # 查找classes.txt或类似文件
        for filename in ['classes.txt', 'class_names.txt', 'labels.txt']:
            class_file = os.path.join(dataset_path, filename)
            if os.path.exists(class_file):
                try:
                    with open(class_file, 'r', encoding='utf-8') as f:
                        classes = [line.strip() for line in f if line.strip()]
                        break
                except Exception:
                    continue
        
        # 如果没有找到类别文件，分析标注文件
        if not classes:
            annotations_dir = os.path.join(dataset_path, 'annotations')
            if os.path.exists(annotations_dir):
                class_ids = set()
                for filename in os.listdir(annotations_dir):
                    if filename.endswith('.txt'):
                        txt_path = os.path.join(annotations_dir, filename)
                        try:
                            with open(txt_path, 'r') as f:
                                for line in f:
                                    parts = line.strip().split()
                                    if parts:
                                        class_ids.add(int(parts[0]))
                        except Exception:
                            continue
                classes = [f'class_{i}' for i in sorted(class_ids)]
        
        return classes
    
    def _extract_voc_classes(self, dataset_path: str) -> List[str]:
        """提取Pascal VOC格式类别"""
        classes = []
        xmls_dir = os.path.join(dataset_path, 'annotations', 'xmls')
        
        if os.path.exists(xmls_dir):
            try:
                import xml.etree.ElementTree as ET
                class_set = set()
                
                for filename in os.listdir(xmls_dir):
                    if filename.endswith('.xml'):
                        xml_path = os.path.join(xmls_dir, filename)
                        try:
                            tree = ET.parse(xml_path)
                            root = tree.getroot()
                            for obj in root.findall('object'):
                                name_elem = obj.find('name')
                                if name_elem is not None:
                                    class_set.add(name_elem.text)
                        except Exception:
                            continue
                
                classes = list(class_set)
            except ImportError:
                logger.warning("xml.etree.ElementTree not available for VOC parsing")
        
        return classes
    
    def _is_valid_image(self, image_path: str) -> bool:
        """验证图片是否有效"""
        try:
            with Image.open(image_path) as img:
                img.verify()
            return True
        except Exception:
            return False
    
    def validate_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """验证数据集完整性"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        try:
            # 检查基本结构
            if not os.path.exists(dataset_path):
                validation_result['valid'] = False
                validation_result['errors'].append(f"数据集路径不存在: {dataset_path}")
                return validation_result
            
            images_dir = os.path.join(dataset_path, 'images')
            if not os.path.exists(images_dir):
                validation_result['valid'] = False
                validation_result['errors'].append("缺少images目录")
                return validation_result
            
            # 验证图片
            image_count = 0
            corrupted_images = []
            
            for filename in os.listdir(images_dir):
                if os.path.splitext(filename)[1].lower() in VALID_IMAGE_EXTENSIONS:
                    image_path = os.path.join(images_dir, filename)
                    if self._is_valid_image(image_path):
                        image_count += 1
                    else:
                        corrupted_images.append(filename)
            
            if image_count == 0:
                validation_result['valid'] = False
                validation_result['errors'].append("没有发现有效的图片文件")
            
            if corrupted_images:
                validation_result['warnings'].append(f"发现{len(corrupted_images)}个损坏的图片文件")
            
            validation_result['summary'] = {
                'total_images': image_count,
                'corrupted_images': len(corrupted_images),
                'annotation_format': self._detect_annotation_format(dataset_path)
            }
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"验证过程中发生错误: {str(e)}")
        
        return validation_result