from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
import os
import sqlite3
from visiofirm.config import PROJECTS_FOLDER
from visiofirm.models.project import Project
from visiofirm.models.user import get_user_by_id
from io import BytesIO
import zipfile
from visiofirm.utils.export_utils import split_images, generate_coco_export, generate_yolo_export, generate_pascal_voc_export, generate_csv_export
import logging
from werkzeug.utils import secure_filename
from visiofirm.utils.VFPreAnnotator import PreAnnotator
import json
import threading

bp = Blueprint('annotation', __name__, url_prefix='/annotation')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for pre-annotation and blind trust status
preannotation_status = {}
preannotation_progress = {}
blind_trust_status = {}
blind_trust_progress = {}

@bp.route('/ai_preannotator_config', methods=['POST'])
@login_required
def ai_preannotator_config():
    """
    Handle AI pre-annotation configuration and execution in a background thread.
    """
    try:
        project_name = request.form.get('project_name')
        mode = request.form.get('mode')
        device = request.form.get('processing_unit', 'cpu')
        box_threshold = float(request.form.get('box_threshold', 0.2))

        if not project_name or not mode:
            return jsonify({'success': False, 'error': 'Project name and mode required'}), 400

        if preannotation_status.get(project_name) == 'running':
            return jsonify({'success': False, 'error': 'Pre-annotation is already running'}), 400

        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        config_db_path = os.path.join(project_path, 'config.db')

        if not os.path.exists(config_db_path):
            return jsonify({'success': False, 'error': 'Project not found'}), 404

        # Set initial status and progress
        preannotation_status[project_name] = 'running'
        preannotation_progress[project_name] = 0

        # Define the background task with all parameters
        def run_preannotation(project_name, mode, device, box_threshold, dino_model, model_path, config_db_path):
            try:
                # Instantiate PreAnnotator inside the thread
                if mode == 'zero-shot':
                    model_type = f"grounding_dino_{dino_model}"
                    proc = PreAnnotator(
                        model_type=model_type,
                        config_db_path=config_db_path,
                        device=device,
                        box_threshold=box_threshold
                    )
                elif mode == 'custom-model':
                    proc = PreAnnotator(
                        model_type="yolo",
                        yolo_model_path=model_path,
                        config_db_path=config_db_path,
                        device=device,
                        box_threshold=box_threshold
                    )
                else:
                    raise ValueError("Invalid mode")

                # pre-annotation process
                proc.run_inferences()
                preannotation_status[project_name] = 'completed'
                preannotation_progress[project_name] = 100
            except Exception as e:
                logger.error(f"Pre-annotation failed for {project_name}: {e}")
                preannotation_status[project_name] = 'failed'
                preannotation_progress[project_name] = 0

        # start the background thread with parameters
        if mode == 'zero-shot':
            dino_model = request.form.get('dino_model', 'tiny')
            thread = threading.Thread(
                target=run_preannotation,
                args=(project_name, mode, device, box_threshold, dino_model, None, config_db_path)
            )
        elif mode == 'custom-model':
            model_path = request.form.get('model_path', 'yolov10x.pt')
            thread = threading.Thread(
                target=run_preannotation,
                args=(project_name, mode, device, box_threshold, None, model_path, config_db_path)
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid mode'}), 400

        thread.start()
        return jsonify({'success': True, 'message': 'Pre-annotation started'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/check_preannotation_status', methods=['GET'])
@login_required
def check_preannotation_status():
    """
    Check the status and progress of the pre-annotation process for a project.
    """
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify({'success': False, 'error': 'Project name required'}), 400
    status = preannotation_status.get(project_name, 'not_started')
    progress = preannotation_progress.get(project_name, 0)
    return jsonify({'success': True, 'status': status, 'progress': progress})

@bp.route('/blind_trust', methods=['POST'])
@login_required
def blind_trust():
    """
    Convert pre-annotations above a confidence threshold to official annotations.
    """
    try:
        project_name = request.form.get('project_name')
        confidence_threshold = float(request.form.get('confidence_threshold', 0.5))

        if not project_name:
            return jsonify({'success': False, 'error': 'Project name required'}), 400

        if blind_trust_status.get(project_name) == 'running':
            return jsonify({'success': False, 'error': 'Blind Trust is already running'}), 400

        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        config_db_path = os.path.join(project_path, 'config.db')

        if not os.path.exists(config_db_path):
            return jsonify({'success': False, 'error': 'Project not found'}), 404

        # capture user_id from the current user
        user_id = current_user.id

        # set initial status and progress
        blind_trust_status[project_name] = 'running'
        blind_trust_progress[project_name] = 0

        # background task
        def run_blind_trust(project_name, confidence_threshold, config_db_path, user_id):
            try:
                with sqlite3.connect(config_db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT DISTINCT i.image_id, i.absolute_path
                        FROM Images i
                        JOIN Preannotations p ON i.image_id = p.image_id
                        WHERE p.confidence >= ?
                    ''', (confidence_threshold,))
                    images = cursor.fetchall()

                    total_images = len(images)
                    processed_images = 0

                    for image_id, absolute_path in images:
                        cursor.execute('''
                            SELECT preannotation_id, type, class_name, x, y, width, height, rotation, segmentation, confidence
                            FROM Preannotations
                            WHERE image_id = ? AND confidence >= ?
                        ''', (image_id, confidence_threshold))
                        preannotations = cursor.fetchall()

                        cursor.execute('DELETE FROM Annotations WHERE image_id = ?', (image_id,))

                        for preanno in preannotations:
                            cursor.execute('''
                                INSERT INTO Annotations (image_id, user_id, type, class_name, x, y, width, height, rotation, segmentation)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (image_id, user_id, preanno[1], preanno[2], preanno[3], preanno[4], preanno[5], preanno[6], preanno[7], preanno[8]))
                        
                        cursor.execute('DELETE FROM Preannotations WHERE image_id = ?', (image_id,))

                        cursor.execute('''
                            INSERT OR REPLACE INTO ReviewedImages (image_id, user_id) VALUES (?, ?)
                        ''', (image_id, user_id))

                        processed_images += 1
                        blind_trust_progress[project_name] = (processed_images / total_images) * 100 if total_images > 0 else 100

                        conn.commit()

                    blind_trust_status[project_name] = 'completed'
            except Exception as e:
                logger.error(f"Blind Trust failed for {project_name}: {e}")
                blind_trust_status[project_name] = 'failed'
                blind_trust_progress[project_name] = 0

        thread = threading.Thread(
            target=run_blind_trust,
            args=(project_name, confidence_threshold, config_db_path, user_id)
        )
        thread.start()
        return jsonify({'success': True, 'message': 'Blind Trust started'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/check_blind_trust_status', methods=['GET'])
def check_blind_trust_status():
    """
    Check the status and progress of the blind trust process for a project.
    """
    project_name = request.args.get('project_name')
    if not project_name:
        return jsonify({'success': False, 'error': 'Project name required'}), 400
    status = blind_trust_status.get(project_name, 'not_started')
    progress = blind_trust_progress.get(project_name, 0)
    return jsonify({'success': True, 'status': status, 'progress': progress})

@bp.route('/<project_name>')
@login_required
def annotation(project_name):
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_path):
            return "Project not found", 404
        
        project = Project(project_name, "", "", project_path)
        images = project.get_images()
        class_list = project.get_classes()
        setup_type = project.get_setup_type()
        
        image_urls = [
            os.path.join('/projects', project_name, 'images', os.path.basename(img[1]))
            for img in images
        ]
        
        image_annotators = {}
        with sqlite3.connect(project.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ReviewedImages (
                    image_id INTEGER PRIMARY KEY,
                    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER
                )
            ''')
            
            cursor.execute('''
                SELECT i.absolute_path
                FROM Images i
                LEFT JOIN Annotations a ON i.image_id = a.image_id
                LEFT JOIN ReviewedImages r ON i.image_id = r.image_id
                WHERE a.annotation_id IS NOT NULL OR r.image_id IS NOT NULL
                GROUP BY i.image_id
            ''')
            annotated_images = {
                os.path.join('/projects', project_name, 'images', os.path.basename(row[0]))
                for row in cursor.fetchall()
            }
            
            # Fetch preannotated_images: images with preannotations but not annotated or reviewed
            cursor.execute('''
                SELECT i.absolute_path
                FROM Images i
                JOIN Preannotations p ON i.image_id = p.image_id
                LEFT JOIN Annotations a ON i.image_id = a.image_id
                LEFT JOIN ReviewedImages r ON i.image_id = r.image_id
                WHERE a.annotation_id IS NULL AND r.image_id IS NULL
                GROUP BY i.image_id
            ''')
            preannotated_images = {
                os.path.join('/projects', project_name, 'images', os.path.basename(row[0]))
                for row in cursor.fetchall()
            }
            
            # Fetch annotator information for all images
            cursor.execute('''
                SELECT i.absolute_path, r.user_id
                FROM Images i
                LEFT JOIN ReviewedImages r ON i.image_id = r.image_id
            ''')
            for absolute_path, user_id in cursor.fetchall():
                image_url = os.path.join('/projects', project_name, 'images', os.path.basename(absolute_path))
                if user_id:
                    user = get_user_by_id(user_id)
                    image_annotators[image_url] = f"{user[3][0]}.{user[4][0]}" if user else None
                else:
                    image_annotators[image_url] = None
        
        return render_template('annotation.html',
                            project_name=project_name,
                            images=image_urls,
                            classes=class_list,
                            setup_type=setup_type,
                            annotated_images=annotated_images,
                            preannotated_images=preannotated_images,
                            image_annotators=image_annotators,
                            current_user_avatar=f"{current_user.first_name[0]}.{current_user.last_name[0]}" if current_user.first_name and current_user.last_name else "")
    
    except Exception as e:
        logger.error(f"Error in annotation route for {project_name}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/get_annotations/<project_name>/<path:image_path>', methods=['GET'])
@login_required
def get_annotations(project_name, image_path):
    try:
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if not os.path.exists(project_path):
            return jsonify({'success': False, 'error': 'Project not found'}), 404
        
        project = Project(project_name, "", "", project_path)
        image_path = os.path.normpath(image_path)
        absolute_image_path = os.path.abspath(os.path.join(PROJECTS_FOLDER, project_name, 'images', image_path))
        logger.info(f"Looking up image with absolute path: {absolute_image_path}")
        
        with sqlite3.connect(project.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT image_id FROM Images WHERE absolute_path = ?', (absolute_image_path,))
            image_id = cursor.fetchone()
            
            if not image_id:
                cursor.execute('SELECT image_id, absolute_path FROM Images')
                all_images = cursor.fetchall()
                for row in all_images:
                    stored_path = row[1]
                    if os.path.normpath(stored_path).lower() == os.path.normpath(absolute_image_path).lower():
                        logger.info(f"Found matching image with path: {stored_path}")
                        image_id = (row[0],)
                        absolute_image_path = stored_path
                        break
            
            if not image_id:
                filename = os.path.basename(image_path)
                cursor.execute('SELECT image_id, absolute_path FROM Images WHERE absolute_path LIKE ?', (f'%{filename}',))
                image_id = cursor.fetchone()
                if image_id:
                    logger.info(f"Found image by filename match: {filename} -> {image_id[1]}")
                    absolute_image_path = image_id[1]
                    image_id = (image_id[0],)
                else:
                    available_paths = [row[1] for row in all_images]
                    logger.warning(f"No image_id found for path: {absolute_image_path} or filename: {filename} in project {project_name}. Available paths: {available_paths}")
                    return jsonify({'success': False, 'error': 'Image not found', 'available_paths': available_paths}), 404
            
            image_id = image_id[0]
            
            annotations = project.get_annotations(absolute_image_path)
            
            cursor.execute('''
                SELECT preannotation_id, image_id, type, class_name, x, y, width, height, rotation, segmentation, confidence
                FROM Preannotations WHERE image_id = ?
            ''', (image_id,))
            preannotations = []
            for row in cursor.fetchall():
                preanno = {
                    'preannotation_id': row[0],
                    'image_id': row[1],
                    'type': 'obbox' if project.get_setup_type() == "Oriented Bounding Box" else row[2],
                    'label': row[3],
                    'confidence': float(row[10]) if row[10] is not None else 0.0
                }
                if row[4] is not None and row[5] is not None and row[6] is not None and row[7] is not None:
                    preanno['x'] = float(row[4])
                    preanno['y'] = float(row[5])
                    preanno['width'] = float(row[6])
                    preanno['height'] = float(row[7])
                    preanno['bbox'] = [float(row[4]), float(row[5]), float(row[6]), float(row[7])]
                if row[8] is not None:
                    preanno['rotation'] = float(row[8])
                else:
                    preanno['rotation'] = 0.0
                if row[9]:
                    try:
                        segmentation = json.loads(row[9])
                        if isinstance(segmentation, list):
                            preanno['segmentation'] = [segmentation]
                            preanno['points'] = [{'x': float(segmentation[i]), 'y': float(segmentation[i+1])} for i in range(0, len(segmentation), 2)]
                            preanno['closed'] = True
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.error(f"Error parsing segmentation for preannotation_id {row[0]}: {e}")
                        preanno['segmentation'] = []
                        preanno['points'] = []
                preannotations.append(preanno)
            
            # Check if the image is reviewed
            cursor.execute('SELECT 1 FROM ReviewedImages WHERE image_id = ?', (image_id,))
            reviewed = cursor.fetchone() is not None
        
        logger.info(f"Retrieved {len(annotations)} annotations and {len(preannotations)} preannotations for {absolute_image_path}, reviewed: {reviewed}")
        return jsonify({
            'success': True,
            'annotations': annotations,
            'preannotations': preannotations,
            'reviewed': reviewed
        })
    except Exception as e:
        logger.error(f"Error fetching annotations and preannotations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/save_annotations', methods=['POST'])
def save_annotations():
    try:
        data = request.json
        if not data or 'project' not in data or 'image' not in data or 'annotations' not in data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400

        project_name = data['project']
        image_filename = data['image']  # expects just the filename, e.g., "image.jpg"
        raw_annotations = data['annotations']

        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        project = Project(project_name, "", "", project_path)
        absolute_image_path = os.path.abspath(os.path.join(PROJECTS_FOLDER, project_name, 'images', secure_filename(image_filename)))
        logger.info(f"Looking up image with absolute path: {absolute_image_path}")

        with sqlite3.connect(project.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT image_id FROM Images WHERE absolute_path = ?', (absolute_image_path,))
            image_id = cursor.fetchone()

            # Fallback 1: Case-insensitive normalized path match
            if not image_id:
                cursor.execute('SELECT image_id, absolute_path FROM Images')
                all_images = cursor.fetchall()
                for row in all_images:
                    stored_path = row[1]
                    if os.path.normpath(stored_path).lower() == os.path.normpath(absolute_image_path).lower():
                        logger.info(f"Found matching image with path: {stored_path}")
                        image_id = (row[0],)
                        absolute_image_path = stored_path
                        break

            # Fallback 2: Filename match (last resort)
            if not image_id:
                filename = os.path.basename(image_filename)
                cursor.execute('SELECT image_id, absolute_path FROM Images WHERE absolute_path LIKE ?', (f'%{filename}',))
                result = cursor.fetchone()
                if result:
                    logger.info(f"Found image by filename match: {filename} -> {result[1]}")
                    absolute_image_path = result[1]
                    image_id = (result[0],)

            # If still not found, try to add if file exists (original behavior)
            if not image_id:
                if os.path.exists(absolute_image_path):
                    project.add_image(absolute_image_path)
                    cursor.execute('SELECT image_id FROM Images WHERE absolute_path = ?', (absolute_image_path,))
                    image_id = cursor.fetchone()
                else:
                    logger.error(f"Image file {absolute_image_path} not found on disk")
                    return jsonify({'success': False, 'error': f'Image file {absolute_image_path} not found on disk'}), 404

            if not image_id:
                logger.error(f"No image entry found or created for {absolute_image_path}")
                return jsonify({'success': False, 'error': 'Image not found or could not be added'}), 404

            image_id = image_id[0]

            # Proceed with saving (rest of the function unchanged)
            cursor.execute('DELETE FROM Annotations WHERE image_id = ?', (image_id,))
            cursor.execute('DELETE FROM Preannotations WHERE image_id = ?', (image_id,))

            for anno in raw_annotations:
                anno_type = anno.get('type', 'rect')
                if project.get_setup_type() == "Segmentation" and anno.get('segmentation'):
                    anno_type = 'polygon'
                elif project.get_setup_type() == "Oriented Bounding Box":
                    anno_type = 'obbox'

                x = y = width = height = rotation = segmentation = None
                if project.get_setup_type() in ("Bounding Box", "Oriented Bounding Box"):
                    if anno.get('bbox'):
                        try:
                            x, y, width, height = map(float, anno['bbox'])
                            if width <= 0 or height <= 0:
                                logger.warning(f"Invalid bbox dimensions for {anno.get('category_name')} in {absolute_image_path}: width={width}, height={height}")
                                continue
                            if project.get_setup_type() == "Oriented Bounding Box":
                                rotation = float(anno.get('rotation', 0))
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid bbox format for {anno.get('category_name')} in {absolute_image_path}: {anno.get('bbox')}, error: {e}")
                            continue
                    else:
                        logger.warning(f"No bbox provided for {anno.get('category_name')} in {absolute_image_path}: {anno}")
                        continue
                elif project.get_setup_type() == "Segmentation" and anno.get('segmentation'):
                    seg = anno['segmentation']
                    if isinstance(seg, list) and seg:
                        seg = seg[0] if isinstance(seg[0], list) else seg
                        segmentation = json.dumps(seg)
                    else:
                        logger.warning(f"Skipping invalid segmentation for {anno.get('category_name')} in {absolute_image_path}")
                        continue

                if (project.get_setup_type() in ("Bounding Box", "Oriented Bounding Box") and (x is None or y is None or width is None or height is None)) or \
                   (project.get_setup_type() == "Segmentation" and segmentation is None):
                    logger.warning(f"Skipping invalid annotation for {anno.get('category_name')} in {absolute_image_path}: {anno}")
                    continue

                cursor.execute('''
                    INSERT INTO Annotations (image_id, type, class_name, x, y, width, height, rotation, segmentation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    image_id,
                    anno_type,
                    anno.get('category_name') or anno.get('label'),
                    x,
                    y,
                    width,
                    height,
                    rotation,
                    segmentation
                ))

            # Mark the image as reviewed
            cursor.execute('''
                INSERT OR REPLACE INTO ReviewedImages (image_id) VALUES (?)
            ''', (image_id,))

            conn.commit()
            logger.info(f"Saved {len(raw_annotations)} annotations for {absolute_image_path} and marked as reviewed")

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error saving annotations: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/delete_images', methods=['POST'])
@login_required
def delete_images():
    data = request.json
    project_name = data.get('project')
    image_urls = data.get('images', [])

    if not project_name or not image_urls:
        return jsonify({'success': False, 'error': 'Project name and image list are required'}), 400

    project_path = os.path.join(PROJECTS_FOLDER, project_name)
    db_path = os.path.join(project_path, 'config.db')

    if not os.path.exists(db_path):
        return jsonify({'success': False, 'error': 'Project database not found'}), 404

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            deleted_count = 0

            for image_url in image_urls:
                image_filename = os.path.basename(image_url)
                absolute_image_path = os.path.join(PROJECTS_FOLDER, project_name, 'images', secure_filename(image_filename))

                if os.path.exists(absolute_image_path):
                    os.remove(absolute_image_path)
                else:
                    logger.warning(f"Image file not found on disk: {absolute_image_path}")

                cursor.execute('''
                    DELETE FROM Annotations
                    WHERE image_id IN (
                        SELECT image_id FROM Images WHERE absolute_path = ?
                    )
                ''', (absolute_image_path,))

                cursor.execute('DELETE FROM Images WHERE absolute_path = ?', (absolute_image_path,))
                deleted_count += cursor.rowcount

            conn.commit()

        return jsonify({'success': True, 'deleted': deleted_count})

    except Exception as e:
        logger.error(f"Error deleting images: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/download_images', methods=['POST'])
@login_required
def download_images():
    data = request.get_json()
    project_name = data.get('project')
    filenames = data.get('images', [])
    save_path = data.get('save_path')

    if not project_name or not filenames:
        return jsonify({'success': False, 'error': 'Project name and image list are required'}), 400

    project_path = os.path.join(PROJECTS_FOLDER, project_name)
    images_path = os.path.join(project_path, 'images')

    if not os.path.exists(images_path):
        return jsonify({'success': False, 'error': 'Images directory not found'}), 404

    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        for filename in filenames:
            safe_filename = os.path.basename(filename)
            file_path = os.path.join(images_path, safe_filename)
            if os.path.exists(file_path):
                zf.write(file_path, arcname=safe_filename)
            else:
                logger.warning(f"File not found: {file_path}")

    if save_path:
        os.makedirs(save_path, exist_ok=True)
        zip_filename = f'{project_name}_images.zip'
        zip_path = os.path.join(save_path, zip_filename)
        with open(zip_path, 'wb') as f:
            f.write(mem_zip.getvalue())
        mem_zip.close()
        return jsonify({'success': True, 'saved_file': zip_path})

    mem_zip.seek(0)
    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{project_name}_images.zip'
    )

@bp.route('/export/<project_name>', methods=['POST'])
@login_required
def export_annotations(project_name):
    if request.is_json:
        data = request.get_json()
    else:
        data_str = request.form.get('export_data')
        if data_str:
            data = json.loads(data_str)
        else:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

    format_type = data.get('format')
    selected_images = data.get('images', [])
    split_choices = data.get('split_choices', ['train'])
    split_ratios = data.get('split_ratios', {'train': 100, 'test': 0, 'val': 0})
    save_path = data.get('save_path')


    # Log incoming parameters
    logger.info(f'Export request for project: {project_name}')
    logger.info(f'Format type: {format_type}')
    logger.info(f'Selected images: {selected_images}')
    logger.info(f'Split choices: {split_choices}')
    logger.info(f'Split ratios: {split_ratios}')

    if not format_type:
        return jsonify({'success': False, 'error': 'Format not specified'}), 400
    project_path = os.path.join(PROJECTS_FOLDER, project_name)
    if not os.path.exists(project_path):
        return jsonify({'success': False, 'error': 'Project not found'}), 404
    project = Project(project_name, "", "", project_path)
    setup_type = project.get_setup_type()
    if setup_type == "Oriented Bounding Box" and format_type not in ['CSV', 'YOLO']:
        return jsonify({'success': False, 'error': 'Oriented Bounding Box can only be exported as CSV or YOLO'}), 400
    elif setup_type == "Segmentation" and format_type not in ['COCO', 'YOLO']:
        return jsonify({'success': False, 'error': 'Segmentation can only be exported as COCO or YOLO'}), 400

    with sqlite3.connect(project.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT i.absolute_path
            FROM Images i
            JOIN Annotations a ON i.image_id = a.image_id
        ''')
        annotated_images = [row[0] for row in cursor.fetchall()]
        cursor.execute('SELECT description FROM Project_Configuration WHERE project_name = ?', (project_name,))
        project_description = cursor.fetchone()[0] or ""

    if not selected_images:
        annotated_selected_images = annotated_images
    else:
        selected_basenames = [os.path.basename(img_path) for img_path in selected_images]
        annotated_selected_images = [img for img in annotated_images if os.path.basename(img) in selected_basenames]

    if not annotated_selected_images:
        return jsonify({'success': False, 'error': 'No annotated images available'}), 400

    # Filter out missing files
    existing_images = [img for img in annotated_selected_images if os.path.exists(img)]
    missing_count = len(annotated_selected_images) - len(existing_images)
    if missing_count > 0:
        logger.warning(f"{missing_count} images not found on disk and skipped during export for project {project_name}")

    if not existing_images:
        return jsonify({'success': False, 'error': 'No existing annotated images found on disk'}), 400

    try:
        splits = split_images(existing_images, split_choices, split_ratios)
        logger.info(f'Split images: {splits}')
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    try:
        if format_type == 'COCO':
            export_data = generate_coco_export(
                project,
                splits,
                setup_type,
                project_name,
                project_description
            )
        elif format_type == 'YOLO':
            export_data = generate_yolo_export(
                project,
                splits,
                setup_type,
                project_name,
                project_description
            )
        elif format_type == 'PASCAL_VOC':
            export_data = generate_pascal_voc_export(
                project,
                splits,
                setup_type
            )
        elif format_type == 'CSV':
            export_data = generate_csv_export(
                project,
                splits,
                setup_type
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid format specified'}), 400

        if save_path:
            os.makedirs(save_path, exist_ok=True)
            zip_filename = f'{project_name}_{format_type}.zip'
            zip_path = os.path.join(save_path, zip_filename)
            with open(zip_path, 'wb') as f:
                f.write(export_data.getvalue())
            return jsonify({'success': True, 'saved_file': zip_path})

        return send_file(
            export_data,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{project_name}_{format_type}.zip'
        )
    except Exception as e:
        logger.error(f'Error during export generation: {e}')
        return jsonify({'success': False, 'error': f'Export failed: {str(e)}'}), 500

    
@bp.route('/check_gpu', methods=['GET'])
def check_gpu():
    try:
        import torch
        has_gpu = torch.cuda.is_available()
        logger.info(f"GPU check: {'Available' if has_gpu else 'Not available'}")
        return jsonify({'success': True, 'has_gpu': has_gpu})
    except ImportError as e:
        logger.error(f"Failed to import torch: {e}")
        return jsonify({'success': False, 'has_gpu': False, 'error': 'PyTorch not installed'}), 500
    except Exception as e:
        logger.error(f"Error checking GPU: {e}")
        return jsonify({'success': False, 'has_gpu': False, 'error': str(e)}), 500