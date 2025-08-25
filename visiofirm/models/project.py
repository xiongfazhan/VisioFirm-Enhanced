import sqlite3
import os
from PIL import Image
import json
import math
import logging
from visiofirm.utils import CocoAnnotationParser, YoloAnnotationParser, NameMatcher, is_valid_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Project:
    def __init__(self, name, description, setup_type, project_path):
        self.name = name
        self.description = description
        self.setup_type = setup_type
        self.db_path = os.path.join(project_path, 'config.db')
        self._initialize_db()
        self.setup_type = self.get_setup_type()
        
    def _initialize_db(self):
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Project_Configuration (
                    project_name TEXT PRIMARY KEY,
                    description TEXT,
                    setup_type TEXT NOT NULL,
                    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Classes (
                    class_name TEXT PRIMARY KEY
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Images (
                    image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    absolute_path TEXT UNIQUE,
                    width INTEGER,
                    height INTEGER
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Annotations (
                    annotation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_id INTEGER,
                    user_id INTEGER,
                    type TEXT NOT NULL,
                    class_name TEXT,
                    x REAL,
                    y REAL,
                    width REAL,
                    height REAL,
                    rotation REAL DEFAULT 0,
                    segmentation TEXT,
                    FOREIGN KEY (image_id) REFERENCES Images(image_id),
                    FOREIGN KEY (class_name) REFERENCES Classes(class_name)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Preannotations (
                    preannotation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_id INTEGER,
                    type TEXT NOT NULL,
                    class_name TEXT,
                    x REAL,
                    y REAL,
                    width REAL,
                    height REAL,
                    rotation REAL DEFAULT 0,
                    segmentation TEXT,
                    confidence REAL NOT NULL,
                    FOREIGN KEY (image_id) REFERENCES Images(image_id),
                    FOREIGN KEY (class_name) REFERENCES Classes(class_name)
                )
            ''')
            # Create or update ReviewedImages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ReviewedImages (
                    image_id INTEGER PRIMARY KEY,
                    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER
                )
            ''')
            # Check if user_id column exists, and add it if not
            cursor.execute("PRAGMA table_info(ReviewedImages)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'user_id' not in columns:
                cursor.execute('''
                    ALTER TABLE ReviewedImages ADD COLUMN user_id INTEGER
                ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_images_absolute_path ON Images(absolute_path)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_annotations_image_id ON Annotations(image_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_preannotations_image_id ON Preannotations(image_id)')
            cursor.execute('''
                INSERT OR IGNORE INTO Project_Configuration (project_name, description, setup_type)
                VALUES (?, ?, ?)
            ''', (self.name, self.description, self.setup_type))
            conn.commit()

    def add_classes(self, class_list):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for cls in class_list:
                cursor.execute('INSERT OR IGNORE INTO Classes (class_name) VALUES (?)', (cls,))
            conn.commit()
            logger.info(f"Added {len(class_list)} classes to project {self.name}")

    def add_image(self, absolute_path):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                with Image.open(absolute_path) as img:
                    img.verify()  # Verify image integrity
                    img = Image.open(absolute_path)  # Reopen after verify
                    width, height = img.size
            except Exception as e:
                logger.error(f"Skipping corrupted image {absolute_path}: {str(e)}")
                return None
            
            cursor.execute('''
                INSERT OR IGNORE INTO Images (absolute_path, width, height)
                VALUES (?, ?, ?)
            ''', (absolute_path, width, height))
            conn.commit()
            cursor.execute('SELECT image_id FROM Images WHERE absolute_path = ?', (absolute_path,))
            result = cursor.fetchone()
            if result:
                logger.info(f"Added image to database: {absolute_path}, image_id: {result[0]}")
                return result[0]
            else:
                logger.error(f"Failed to add image to database: {absolute_path}")
                return None

    def get_images(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT image_id, absolute_path, width, height FROM Images')
            images = cursor.fetchall()
            logger.info(f"Retrieved {len(images)} images from database for project {self.name}")
            return images

    def get_images_with_status(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.absolute_path, 
                       EXISTS (
                           SELECT 1 FROM Annotations a WHERE a.image_id = i.image_id
                       ) as is_annotated
                FROM Images i
            ''')
            return cursor.fetchall()

    def get_classes(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT class_name FROM Classes')
            classes = [row[0] for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(classes)} classes for project {self.name}: {classes}")
            return classes

    def get_setup_type(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT setup_type FROM Project_Configuration WHERE project_name = ?', (self.name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            return None

    def add_images(self, absolute_paths):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            image_data = []
            for path in absolute_paths:
                try:
                    with Image.open(path) as img:
                        img.verify()  # Verify image integrity
                        img = Image.open(path)  # Reopen after verify
                        width, height = img.size
                    image_data.append((path, width, height))
                except Exception as e:
                    logger.error(f"Skipping corrupted image {path}: {str(e)}")
                    continue
            if image_data:
                cursor.executemany('''
                    INSERT OR IGNORE INTO Images (absolute_path, width, height)
                    VALUES (?, ?, ?)
                ''', image_data)
                conn.commit()
                logger.info(f"Added {len(image_data)} images to database for project {self.name}: {[path for path, _, _ in image_data]}")
            else:
                logger.warning(f"No valid images to add for project {self.name}")

    def save_annotations(self, image_path, annotations, user_id=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT image_id FROM Images WHERE absolute_path = ?', (image_path,))
            image_id = cursor.fetchone()
            if not image_id:
                logger.error(f"Image {image_path} not found in database for project {self.name}")
                return
            image_id = image_id[0]

            # Delete existing annotations for this image
            cursor.execute('DELETE FROM Annotations WHERE image_id = ?', (image_id,))
            logger.info(f"Deleted existing annotations for {image_path} in project {self.name}")

            # Deduplicate annotations
            unique_annotations = []
            seen = set()
            for anno in annotations:
                anno_type = anno.get('type', 'rect')
                if self.setup_type == "Segmentation" and anno.get('segmentation'):
                    anno_type = 'polygon'
                elif self.setup_type == "Oriented Bounding Box":
                    anno_type = 'obbox'

                key = (anno_type, anno.get('category_name') or anno.get('label'))
                if anno.get('bbox'):
                    bbox = tuple(round(float(coord), 4) for coord in anno['bbox'])
                    rotation = round(float(anno.get('rotation', 0)), 4)
                    key += bbox + (rotation,)
                elif anno.get('segmentation'):
                    seg = anno['segmentation']
                    if isinstance(seg, list) and seg:
                        seg = seg[0] if isinstance(seg[0], list) else seg
                        sorted_seg = tuple(sorted(tuple(round(float(coord), 4) for coord in seg)))
                        key += sorted_seg

                if key not in seen:
                    seen.add(key)
                    unique_annotations.append(anno)

            # Save unique annotations
            for anno in unique_annotations:
                anno_type = anno.get('type', 'rect')
                if self.setup_type == "Segmentation" and anno.get('segmentation'):
                    anno_type = 'polygon'
                elif self.setup_type == "Oriented Bounding Box":
                    anno_type = 'obbox'

                x = y = width = height = rotation = segmentation = None
                if self.setup_type in ("Bounding Box", "Oriented Bounding Box"):
                    if anno.get('bbox'):
                        try:
                            x, y, width, height = map(float, anno['bbox'])
                            if width <= 0 or height <= 0:
                                logger.warning(f"Invalid bbox dimensions for {anno.get('category_name')} in {image_path}: width={width}, height={height}")
                                continue
                            if self.setup_type == "Oriented Bounding Box":
                                rotation = float(anno.get('rotation', 0))
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid bbox format for {anno.get('category_name')} in {image_path}: {anno.get('bbox')}, error: {e}")
                            continue
                    else:
                        logger.warning(f"No bbox provided for {anno.get('category_name')} in {image_path}: {anno}")
                        continue
                elif self.setup_type == "Segmentation" and anno.get('segmentation'):
                    seg = anno['segmentation']
                    if isinstance(seg, list) and seg:
                        seg = seg[0] if isinstance(seg[0], list) else seg
                        segmentation = json.dumps(seg)
                    else:
                        logger.warning(f"Skipping invalid segmentation for {anno.get('category_name')} in {image_path}")
                        continue

                if (self.setup_type in ("Bounding Box", "Oriented Bounding Box") and (x is None or y is None or width is None or height is None)) or \
                (self.setup_type == "Segmentation" and segmentation is None):
                    logger.warning(f"Skipping invalid annotation for {anno.get('category_name')} in {image_path}: {anno}")
                    continue

                cursor.execute('''
                    INSERT INTO Annotations (image_id, user_id, type, class_name, x, y, width, height, rotation, segmentation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    image_id,
                    user_id,
                    anno_type,
                    anno.get('category_name') or anno.get('label'),
                    x,
                    y,
                    width,
                    height,
                    rotation,
                    segmentation
                ))
                logger.info(f"Saved annotation for {image_path}: type={anno_type}, class={anno.get('category_name')}, bbox=[{x}, {y}, {width}, {height}], rotation={rotation}, user_id={user_id}")

            # Clear preannotations after transfer
            cursor.execute('DELETE FROM Preannotations WHERE image_id = ?', (image_id,))
            logger.info(f"Cleared preannotations for {image_path} after transfer to annotations")
            
            conn.commit()

    def get_annotations(self, image_path):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT image_id FROM Images WHERE absolute_path = ?', (image_path,))
            image_id = cursor.fetchone()
            if not image_id:
                logger.warning(f"No image_id found for path: {image_path} in project {self.name}")
                return []
            image_id = image_id[0]
            cursor.execute('''
                SELECT annotation_id, image_id, type, class_name, x, y, width, height, rotation, segmentation
                FROM Annotations WHERE image_id = ?
            ''', (image_id,))
            annotations = []
            for row in cursor.fetchall():
                anno = {
                    'annotation_id': row[0],
                    'image_id': row[1],
                    'type': 'obbox' if self.setup_type == "Oriented Bounding Box" else row[2],
                    'label': row[3]
                }
                if row[4] is not None and row[5] is not None and row[6] is not None and row[7] is not None:
                    anno['x'] = row[4]
                    anno['y'] = row[5]
                    anno['width'] = row[6]
                    anno['height'] = row[7]
                    anno['bbox'] = [row[4], row[5], row[6], row[7]]
                else:
                    logger.warning(f"Annotation {row[0]} for {image_path} missing bbox coordinates: x={row[4]}, y={row[5]}, width={row[6]}, height={row[7]}")
                if row[8] is not None:
                    anno['rotation'] = row[8]
                else:
                    anno['rotation'] = 0
                if row[9]:
                    try:
                        segmentation = json.loads(row[9])
                        if isinstance(segmentation, list):
                            anno['segmentation'] = [segmentation]
                            anno['points'] = [{'x': segmentation[i], 'y': segmentation[i+1]} for i in range(0, len(segmentation), 2)]
                            anno['closed'] = True
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Error parsing segmentation for annotation_id {row[0]}: {e}")
                        anno['segmentation'] = []
                        anno['points'] = []
                annotations.append(anno)
            logger.info(f"Retrieved {len(annotations)} annotations for {image_path} in project {self.name}")
            return annotations
    
    def parse_and_add_annotations(self, temp_upload_dir, image_paths):
        name_matcher = NameMatcher(self.get_classes())
        image_basenames = [os.path.basename(path) for path in image_paths]
        annotation_files = [f for f in os.listdir(temp_upload_dir) if f.endswith(('.json', '.yaml', '.txt'))]

        logger.info(f"Found {len(annotation_files)} annotation files in {temp_upload_dir}: {annotation_files}")
        logger.info(f"Processing {len(image_paths)} images: {image_basenames}")

        for anno_file in [f for f in annotation_files if f.endswith('.json')]:
            anno_path = os.path.join(temp_upload_dir, anno_file)
            try:
                parser = CocoAnnotationParser(anno_path)
                for image_file in image_basenames:
                    annotations = parser.get_annotations_for_image(image_file)
                    if annotations:
                        absolute_image_path = next(
                            (path for path in image_paths if os.path.basename(path).lower() == image_file.lower()), None
                        )
                        if absolute_image_path:
                            normalized_annotations = []
                            for anno in annotations:
                                matched_class = name_matcher.match(anno['category_name'])
                                if matched_class:
                                    normalized_anno = {'category_name': matched_class, 'rotation': 0}
                                    if self.setup_type in ("Bounding Box", "Oriented Bounding Box"):
                                        if anno.get('bbox') and len(anno['bbox']) == 4:
                                            normalized_anno['bbox'] = anno['bbox']
                                        else:
                                            continue
                                    elif self.setup_type == "Segmentation":
                                        if anno.get('segmentation'):
                                            normalized_anno['segmentation'] = anno['segmentation']
                                        else:
                                            continue
                                    normalized_annotations.append(normalized_anno)
                            if normalized_annotations:
                                self.save_annotations(absolute_image_path, normalized_annotations)
            except Exception as e:
                logger.error(f"Error parsing COCO file {anno_file}: {e}")

        yaml_files = [f for f in annotation_files if f.endswith('.yaml')]
        txt_files = set([f for f in annotation_files if f.endswith('.txt')])
        
        if yaml_files:
            yaml_path = os.path.join(temp_upload_dir, yaml_files[0])
            try:
                parser = YoloAnnotationParser(yaml_path, temp_upload_dir)
                for image_file in image_basenames:
                    annotations = parser.get_annotations_for_image(image_file)
                    if annotations:
                        absolute_image_path = next(
                            (path for path in image_paths if os.path.basename(path) == image_file), None
                        )
                        if absolute_image_path:
                            with sqlite3.connect(self.db_path) as conn:
                                cursor = conn.cursor()
                                cursor.execute('SELECT width, height FROM Images WHERE absolute_path = ?', (absolute_image_path,))
                                result = cursor.fetchone()
                                if result:
                                    img_width, img_height = result
                                    normalized_annotations = []
                                    for anno in annotations:
                                        matched_class = name_matcher.match(anno['category_name'])
                                        if matched_class:
                                            normalized_anno = {'category_name': matched_class, 'rotation': 0}
                                            if self.setup_type == "Bounding Box":
                                                if anno.get('bbox_norm') and len(anno['bbox_norm']) == 4:
                                                    x_center, y_center, w, h = anno['bbox_norm']
                                                    normalized_anno['bbox'] = [
                                                        (x_center - w / 2) * img_width,
                                                        (y_center - h / 2) * img_height,
                                                        w * img_width,
                                                        h * img_height
                                                    ]
                                            elif self.setup_type == "Oriented Bounding Box":
                                                if anno.get('obbox') and len(anno['obbox']) == 8:
                                                    x1, y1, x2, y2, x3, y3, x4, y4 = anno['obbox']
                                                    min_x = min(x1, x2, x3, x4) * img_width
                                                    max_x = max(x1, x2, x3, x4) * img_width
                                                    min_y = min(y1, y2, y3, y4) * img_height
                                                    max_y = max(y1, y2, y3, y4) * img_height
                                                    width = max_x - min_x
                                                    height = max_y - min_y
                                                    dx = (x2 - x1) * img_width
                                                    dy = (y2 - y1) * img_height
                                                    rotation = math.degrees(math.atan2(dy, dx))
                                                    normalized_anno['bbox'] = [min_x, min_y, width, height]
                                                    normalized_anno['rotation'] = rotation
                                            elif self.setup_type == "Segmentation":
                                                if anno.get('segmentation'):
                                                    points = anno['segmentation']
                                                    denormalized_points = []
                                                    for i in range(0, len(points), 2):
                                                        x = points[i] * img_width
                                                        y = points[i + 1] * img_height
                                                        denormalized_points.extend([x, y])
                                                    normalized_anno['segmentation'] = denormalized_points
                                            if 'bbox' in normalized_anno or 'segmentation' in normalized_anno:
                                                normalized_annotations.append(normalized_anno)
                                    if normalized_annotations:
                                        self.save_annotations(absolute_image_path, normalized_annotations, None)
                                else:
                                    logger.error(f"No image dimensions found for {absolute_image_path}")
            except Exception as e:
                logger.error(f"Error initializing YOLO parser with {yaml_files[0]}: {e}")
        else:
            for txt_file in txt_files:
                try:
                    image_file = os.path.splitext(txt_file)[0] + '.jpg'
                    absolute_image_path = next(
                        (path for path in image_paths if os.path.basename(path).lower() == image_file.lower()), None
                    )
                    if absolute_image_path:
                        with open(os.path.join(temp_upload_dir, txt_file), 'r') as f:
                            lines = f.readlines()
                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute('SELECT width, height FROM Images WHERE absolute_path = ?', (absolute_image_path,))
                            result = cursor.fetchone()
                            if result:
                                img_width, img_height = result
                                project_classes = self.get_classes()
                                normalized_annotations = []
                                for line in lines:
                                    parts = line.strip().split()
                                    if len(parts) >= 5:
                                        class_id = int(parts[0])
                                        if 0 <= class_id < len(project_classes):
                                            class_name = project_classes[class_id]
                                            if len(parts) == 5:
                                                x_center, y_center, w, h = map(float, parts[1:5])
                                                bbox = [
                                                    (x_center - w / 2) * img_width,
                                                    (y_center - h / 2) * img_height,
                                                    w * img_width,
                                                    h * img_height
                                                ]
                                                normalized_annotations.append({
                                                    'category_name': class_name,
                                                    'bbox': bbox,
                                                    'rotation': 0
                                                })
                                            elif len(parts) == 9 and self.setup_type == "Oriented Bounding Box":
                                                points = list(map(float, parts[1:9]))
                                                min_x = min(points[0::2]) * img_width
                                                max_x = max(points[0::2]) * img_width
                                                min_y = min(points[1::2]) * img_height
                                                max_y = max(points[1::2]) * img_height
                                                width = max_x - min_x
                                                height = max_y - min_y
                                                dx = (points[2] - points[0]) * img_width
                                                dy = (points[3] - points[1]) * img_height
                                                rotation = math.degrees(math.atan2(dy, dx))
                                                normalized_annotations.append({
                                                    'category_name': class_name,
                                                    'bbox': [min_x, min_y, width, height],
                                                    'rotation': rotation
                                                })
                                            elif len(parts) > 5 and (len(parts) - 1) % 2 == 0 and self.setup_type == "Segmentation":
                                                points = list(map(float, parts[1:]))
                                                denormalized_points = []
                                                for i in range(0, len(points), 2):
                                                    denormalized_points.extend([points[i] * img_width, points[i + 1] * img_height])
                                                normalized_annotations.append({
                                                    'category_name': class_name,
                                                    'segmentation': denormalized_points
                                                })
                                if normalized_annotations:
                                    self.save_annotations(absolute_image_path, normalized_annotations)
                except Exception as e:
                    logger.error(f"Error parsing standalone TXT file {txt_file}: {e}")
                    
    def get_image_count(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM Images')
            count = cursor.fetchone()[0]
            logger.info(f"Image count for project {self.name}: {count}")
            return count

    def get_annotated_image_count(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(DISTINCT image_id) FROM Annotations')
            count = cursor.fetchone()[0]
            logger.info(f"Annotated image count for project {self.name}: {count}")
            return count

    def get_class_distribution(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT class_name, COUNT(*) FROM Annotations GROUP BY class_name')
            distribution = dict(cursor.fetchall())
            logger.info(f"Class distribution for project {self.name}: {distribution}")
            return distribution

    def get_annotations_per_image(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(a.annotation_id)
                FROM Images i
                LEFT JOIN Annotations a ON i.image_id = a.image_id
                GROUP BY i.image_id
            ''')
            counts = [row[0] for row in cursor.fetchall()]
            #logger.info(f"Annotations per image for project {self.name}: {counts}")
            return counts