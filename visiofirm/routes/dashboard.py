import logging
from flask import (
    Blueprint, 
    render_template, 
    request,
    jsonify, 
    current_app)
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
import shutil
import zipfile
import tarfile
import rarfile
import sqlite3
from filelock import FileLock
import time
import psutil
import errno
from visiofirm.config import PROJECTS_FOLDER, VALID_IMAGE_EXTENSIONS, get_cache_folder
from visiofirm.models.project import Project
from visiofirm.utils import CocoAnnotationParser, YoloAnnotationParser, NameMatcher, is_valid_image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    projects = []
    for project_name in os.listdir(PROJECTS_FOLDER):
        if project_name in ['temp_chunks', 'weights']:
            continue
        project_path = os.path.join(PROJECTS_FOLDER, project_name)
        if os.path.isdir(project_path):
            db_path = os.path.join(project_path, 'config.db')
            creation_date = None
            if os.path.exists(db_path):
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('SELECT creation_date FROM Project_Configuration WHERE project_name = ?', (project_name,))
                        result = cursor.fetchone()
                        creation_date = result[0] if result else None
                except Exception as e:
                    logger.error(f"Error fetching creation date for {project_name}: {e}")
            
            images_path = os.path.join(project_path, 'images')
            image_files = [
                f for f in os.listdir(images_path)
                if os.path.isfile(os.path.join(images_path, f)) and os.path.splitext(f)[1].lower() in VALID_IMAGE_EXTENSIONS
            ] if os.path.exists(images_path) else []
            projects.append({
                'name': project_name,
                'images': [
                    os.path.join('/projects', project_name, 'images', img)
                    for img in image_files[:3]
                ],
                'creation_date': creation_date
            })
    
    projects.sort(key=lambda p: p['creation_date'] or '', reverse=True)
    return render_template('index.html', projects=projects)

def extract_archive(file_path, extract_path):
    """Extract archive files (zip, tar, rar) to the specified path and validate images."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        elif ext in {'.tar', '.tar.gz'}:
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
        elif ext == '.rar':
            with rarfile.RarFile(file_path) as rar_ref:
                rar_ref.extractall(extract_path)
        # Validate extracted images
        for root, _, filenames in os.walk(extract_path):
            for fname in filenames:
                if os.path.splitext(fname)[1].lower() in VALID_IMAGE_EXTENSIONS:
                    full_path = os.path.join(root, fname)
                    if not is_valid_image(full_path):
                        os.remove(full_path)
                        logger.warning(f"Removed corrupted extracted image: {full_path}")
    except Exception as e:
        logger.error(f"Error extracting archive {file_path}: {e}")
        raise

@bp.route('/create_project', methods=['POST'])
@login_required
def create_project():
    try:
        project_name = request.form.get('project_name', '').strip()
        description = request.form.get('description', '')
        setup_type = request.form.get('setup_type', '').strip()
        class_names = request.form.get('class_names', '')
        upload_id = request.form.get('upload_id')

        if not setup_type or not upload_id:
            return jsonify({'error': 'Setup type and upload ID are required'}), 400
        if setup_type not in {"Bounding Box", "Oriented Bounding Box", "Segmentation"}:
            return jsonify({'error': 'Invalid setup type'}), 400

        class_list = [cls.strip() for cls in class_names.replace(';', ',').replace('.', ',').split(',') if cls.strip()]

        if not project_name:
            project_name = generate_unique_project_name()
        else:
            project_name = ensure_unique_project_name(project_name)

        project_path = os.path.join(PROJECTS_FOLDER, secure_filename(project_name))
        images_path = os.path.join(project_path, 'images')
        os.makedirs(images_path, exist_ok=True)

        project = Project(project_name, description, setup_type, project_path)
        project.add_classes(class_list)

        cache_dir = get_cache_folder()
        temp_base = os.path.join(cache_dir, 'temp_chunks')
        os.makedirs(temp_base, exist_ok=True)
        temp_upload_dir = os.path.join(temp_base, upload_id)
        if not os.path.exists(temp_upload_dir):
            return jsonify({'error': 'No files found for upload ID'}), 400

        image_paths = []
        annotation_extensions = {'.json', '.yaml', '.txt'}
        files_to_process = []

        for filename in os.listdir(temp_upload_dir):
            file_path = os.path.join(temp_upload_dir, filename)
            ext = os.path.splitext(filename)[1].lower()
            if ext in VALID_IMAGE_EXTENSIONS or ext in annotation_extensions:
                files_to_process.append((filename, file_path, ext))
            elif ext in {'.zip', '.tar', '.tar.gz', '.rar'}:
                extract_path = os.path.join(temp_upload_dir, f'extracted_{filename}')
                os.makedirs(extract_path, exist_ok=True)
                extract_archive(file_path, extract_path)
                extracted_files = []
                for root, _, filenames in os.walk(extract_path):
                    for fname in filenames:
                        file_ext = os.path.splitext(fname)[1].lower()
                        src_path = os.path.join(root, fname)
                        extracted_files.append((fname, src_path, file_ext))
                project.parse_and_add_annotations(extract_path, [f[1] for f in extracted_files if f[2] in VALID_IMAGE_EXTENSIONS])
                for fname, src_path, file_ext in extracted_files:
                    if file_ext in VALID_IMAGE_EXTENSIONS:
                        if is_valid_image(src_path):
                            final_path = os.path.join(images_path, secure_filename(fname))
                            if not os.path.exists(final_path):
                                lock_path = final_path + '.lock'
                                with FileLock(lock_path):
                                    shutil.move(src_path, final_path)
                                image_paths.append(os.path.abspath(final_path))
                                logger.info(f"Moved image {fname} from archive to {final_path}")
                            else:
                                logger.info(f"Image {fname} already exists, skipping")
                        else:
                            logger.warning(f"Skipping corrupted image from archive: {fname}")
                    elif file_ext in annotation_extensions:
                        dest_path = os.path.join(temp_upload_dir, secure_filename(fname))
                        lock_path = dest_path + '.lock'
                        with FileLock(lock_path):
                            shutil.move(src_path, dest_path)
                        logger.info(f"Moved annotation {fname} to {dest_path}")
                shutil.rmtree(extract_path, ignore_errors=True)
                os.remove(file_path)

        for filename, file_path, ext in files_to_process:
            if ext in VALID_IMAGE_EXTENSIONS:
                if is_valid_image(file_path):
                    final_path = os.path.join(images_path, secure_filename(filename))
                    if not os.path.exists(final_path):
                        lock_path = final_path + '.lock'
                        with FileLock(lock_path):
                            shutil.move(file_path, final_path)
                        image_paths.append(os.path.abspath(final_path))
                        logger.info(f"Moved image {filename} to {final_path}")
                    else:
                        logger.info(f"Image {filename} already exists, skipping")
                else:
                    logger.warning(f"Skipping corrupted image: {filename}")
            elif ext in annotation_extensions:
                logger.info(f"Keeping annotation {filename} in {temp_upload_dir}")

        if not image_paths:
            shutil.rmtree(project_path, ignore_errors=True)
            return jsonify({'error': 'No valid images found to create the project'}), 400

        project.add_images(image_paths)
        project.parse_and_add_annotations(temp_upload_dir, image_paths)
        shutil.rmtree(temp_upload_dir, ignore_errors=True)

        return jsonify({'success': True, 'project_name': project_name})
    except Exception as e:
        logger.error(f"Error in create_project: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

def generate_unique_project_name():
    base_name = "#VisioFirm"
    counter = 0
    while True:
        project_name = base_name if counter == 0 else f"{base_name}_{counter}"
        if not os.path.exists(os.path.join(PROJECTS_FOLDER, project_name)):
            return project_name
        counter += 1

def ensure_unique_project_name(project_name):
    original_name = secure_filename(project_name)
    if original_name == "#VisioFirm":
        return generate_unique_project_name()
    counter = 1
    new_name = original_name
    while os.path.exists(os.path.join(PROJECTS_FOLDER, new_name)):
        new_name = f"{original_name}_{counter}"
        counter += 1
    return new_name

@bp.route('/get_unique_project_name', methods=['GET'])
@login_required
def get_unique_project_name():
    try:
        project_name = generate_unique_project_name()
        return jsonify({'success': True, 'project_name': project_name})
    except Exception as e:
        logger.error(f"Error in get_unique_project_name: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@bp.route('/import_images', methods=['POST'])
@login_required
def import_images():
    try:
        project_name = request.form.get('project_name')
        upload_id = request.form.get('upload_id')

        if not project_name or not upload_id:
            return jsonify({'error': 'Project name and upload ID are required'}), 400

        project_path = os.path.join(PROJECTS_FOLDER, secure_filename(project_name))
        if not os.path.exists(project_path):
            return jsonify({'error': 'Project does not exist'}), 404

        images_path = os.path.join(project_path, 'images')
        os.makedirs(images_path, exist_ok=True)

        project = Project(project_name, '', '', project_path)

        cache_dir = get_cache_folder()
        temp_base = os.path.join(cache_dir, 'temp_chunks')
        os.makedirs(temp_base, exist_ok=True)
        temp_upload_dir = os.path.join(temp_base, upload_id)
        if not os.path.exists(temp_upload_dir):
            return jsonify({'error': 'No files found for upload ID'}), 400

        image_paths = []
        annotation_extensions = {'.json', '.yaml', '.txt'}
        for filename in os.listdir(temp_upload_dir):
            file_path = os.path.join(temp_upload_dir, filename)
            ext = os.path.splitext(filename)[1].lower()
            try:
                if ext in VALID_IMAGE_EXTENSIONS:
                    if is_valid_image(file_path):
                        final_path = os.path.join(images_path, secure_filename(filename))
                        if not os.path.exists(final_path):
                            lock_path = final_path + '.lock'
                            with FileLock(lock_path):
                                shutil.move(file_path, final_path)
                            image_paths.append(os.path.abspath(final_path))
                            logger.info(f"Moved image {filename} to {final_path}")
                        else:
                            logger.info(f"Image {filename} already exists, skipping")
                    else:
                        logger.warning(f"Skipping corrupted image: {filename}")
                elif ext in {'.zip', '.tar', '.tar.gz', '.rar'}:
                    extract_path = os.path.join(temp_upload_dir, f'extracted_{filename}')
                    os.makedirs(extract_path, exist_ok=True)
                    extract_archive(file_path, extract_path)
                    for root, _, filenames in os.walk(extract_path):
                        for fname in filenames:
                            file_ext = os.path.splitext(fname)[1].lower()
                            src_path = os.path.join(root, fname)
                            if file_ext in VALID_IMAGE_EXTENSIONS:
                                if is_valid_image(src_path):
                                    final_path = os.path.join(images_path, secure_filename(fname))
                                    if not os.path.exists(final_path):
                                        lock_path = final_path + '.lock'
                                        with FileLock(lock_path):
                                            shutil.move(src_path, final_path)
                                        image_paths.append(os.path.abspath(final_path))
                                        logger.info(f"Moved image {fname} from archive to {final_path}")
                                    else:
                                        logger.info(f"Image {fname} already exists, skipping")
                                else:
                                    logger.warning(f"Skipping corrupted image from archive: {fname}")
                            elif file_ext in annotation_extensions:
                                dest_path = os.path.join(temp_upload_dir, secure_filename(fname))
                                lock_path = dest_path + '.lock'
                                with FileLock(lock_path):
                                    shutil.move(src_path, dest_path)
                                logger.info(f"Moved annotation {fname} to {dest_path}")
                    shutil.rmtree(extract_path, ignore_errors=True)
                    os.remove(file_path)
            except Exception as e:
                logger.error(f"Error processing file {filename}: {e}")
                continue

        if not image_paths:
            return jsonify({'error': 'No new valid images found to import'}), 400

        project.add_images(image_paths)
        project.parse_and_add_annotations(temp_upload_dir, image_paths)
        shutil.rmtree(temp_upload_dir, ignore_errors=True)

        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error in import_images: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@bp.route('/parse_annotations', methods=['POST'])
@login_required
def parse_annotations():
    upload_id = request.form.get('upload_id')
    class_names = request.form.get('class_names', '')
    project_classes = [cls.strip() for cls in class_names.replace(';', ',').replace('.', ',').split(',') if cls.strip()]

    cache_dir = get_cache_folder()
    temp_base = os.path.join(cache_dir, 'temp_chunks')
    temp_upload_dir = os.path.join(temp_base, upload_id)
    if not os.path.exists(temp_upload_dir):
        return jsonify({'error': 'Upload ID not found'}), 404

    annotation_files = [f for f in os.listdir(temp_upload_dir) if f.endswith('.json') or f.endswith('.yaml')]

    summary = {
        'coco_files': [],
        'yolo_files': [],
        'class_mapping': {},
        'annotated_images': 0
    }

    name_matcher = NameMatcher(project_classes)

    for anno_file in annotation_files:
        anno_path = os.path.join(temp_upload_dir, anno_file)
        if anno_file.endswith('.json'):
            try:
                parser = CocoAnnotationParser(anno_path)
                summary['coco_files'].append(anno_file)
                for img_id, annotations in parser.annotations_by_image.items():
                    image_file = parser.images_dict.get(img_id)
                    if image_file:
                        summary['annotated_images'] += 1
                        for anno in annotations:
                            cat_name = parser.categories.get(anno['category_id'], 'unknown')
                            matched_class = name_matcher.match(cat_name)
                            summary['class_mapping'][cat_name] = matched_class
            except Exception as e:
                logger.error(f"Error parsing COCO file {anno_file} for summary: {e}")
        elif anno_file.endswith('.yaml'):
            try:
                parser = YoloAnnotationParser(anno_path, temp_upload_dir)
                summary['yolo_files'].append(anno_file)
                for image_file in os.listdir(temp_upload_dir):
                    if image_file.lower().endswith(tuple(VALID_IMAGE_EXTENSIONS)):
                        annotations = parser.get_annotations_for_image(image_file)
                        if annotations:
                            summary['annotated_images'] += 1
                            for anno in annotations:
                                cat_name = anno['category_name']
                                matched_class = name_matcher.match(cat_name)
                                summary['class_mapping'][cat_name] = matched_class
            except Exception as e:
                logger.error(f"Error parsing YOLO file {anno_file} for summary: {e}")

    return jsonify({'success': True, 'summary': summary})

@bp.route('/upload_chunk', methods=['POST'])
@login_required
def upload_chunk():
    if 'chunk' not in request.files:
        return jsonify({'error': 'No chunk provided'}), 400
    
    chunk = request.files['chunk']
    upload_id = request.form.get('upload_id')
    file_id = request.form.get('file_id')
    chunk_index = int(request.form.get('chunk_index'))
    filename = secure_filename(request.form.get('filename'))

    if not all([upload_id, file_id, filename]):
        return jsonify({'error': 'Missing upload parameters'}), 400

    # Change to user cache-based temp dir
    cache_dir = get_cache_folder()
    temp_base = os.path.join(cache_dir, 'temp_chunks')  # New subdir for chunks
    os.makedirs(temp_base, exist_ok=True)
    
    temp_dir = os.path.join(temp_base, upload_id, file_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Clean up stale temporary files (older than 1 hour)
    try:
        current_time = time.time()
        for temp_upload_id in os.listdir(temp_base):
            temp_upload_path = os.path.join(temp_base, temp_upload_id)
            if os.path.isdir(temp_upload_path):
                mtime = os.path.getmtime(temp_upload_path)
                if current_time - mtime > 3600:  # 1 hour
                    shutil.rmtree(temp_upload_path, ignore_errors=True)
                    logger.info(f"Cleaned up stale temp directory: {temp_upload_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up stale temp files: {e}")

    # Validate temporary directory
    try:
        temp_stat = os.stat(temp_base)
        if not os.access(temp_base, os.W_OK):
            logger.error(f"Temporary directory {temp_base} is not writable")
            return jsonify({'error': 'Server error: Temporary directory not writable'}), 500
        # Check available disk space (in bytes)
        total, used, free = shutil.disk_usage(temp_base)
        chunk_size = chunk.seek(0, os.SEEK_END)
        chunk.seek(0)  # Reset to start
        if free < chunk_size:
            logger.error(f"Insufficient disk space in {temp_base}: {free} bytes available, {chunk_size} bytes needed")
            return jsonify({'error': 'Server error: Insufficient disk space'}), 500
        # Log disk and memory usage
        memory = psutil.virtual_memory()
        logger.info(f"System resources: Disk {free / (1024**3):.2f} GB available, Memory {memory.available / (1024**3):.2f} GB available")
    except Exception as e:
        logger.error(f"Error validating temporary directory: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

    chunk_path = os.path.join(temp_dir, f'chunk_{chunk_index}')
    try:
        start_time = time.time()
        logger.info(f"Received chunk {chunk_index} for {filename}, size: {chunk_size} bytes")
        chunk.save(chunk_path)
        elapsed_time = time.time() - start_time
        logger.info(f"Saved chunk {chunk_index} for {filename} at {chunk_path}, size: {os.path.getsize(chunk_path)} bytes, took {elapsed_time:.2f} seconds")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error saving chunk {chunk_index} for {filename}: {e}")
        return jsonify({'error': f'Chunk save failed: {str(e)}'}), 500

@bp.route('/assemble_file', methods=['POST'])
@login_required
def assemble_file():
    import hashlib
    from shutil import copyfileobj  # For streaming copy

    # Parse form data (compatible with uploads)
    upload_id = request.form.get('upload_id')
    file_id = request.form.get('file_id')
    total_chunks = int(request.form.get('total_chunks', 0))
    filename = secure_filename(request.form.get('filename'))
    expected_hash = request.form.get('file_hash', '')

    if not all([upload_id, file_id, filename, total_chunks]):
        return jsonify({'error': 'Missing assembly parameters'}), 400

    cache_dir = get_cache_folder()
    temp_base = os.path.join(cache_dir, 'temp_chunks')
    temp_dir = os.path.join(temp_base, upload_id, file_id)
    final_dir = os.path.join(temp_base, upload_id)
    os.makedirs(final_dir, exist_ok=True)
    final_path = os.path.join(final_dir, filename)
    lock_path = final_path + '.lock'

    try:
        with FileLock(lock_path):
            start_time = time.time()
            logger.info(f"Starting assembly for {filename} (ID: {file_id}) with {total_chunks} chunks")

            # Disk space check
            total, used, free = shutil.disk_usage(os.path.dirname(final_path))
            estimated_size = sum(os.path.getsize(os.path.join(temp_dir, f'chunk_{i}'))
                                 for i in range(total_chunks) if os.path.exists(os.path.join(temp_dir, f'chunk_{i}')))
            if free < estimated_size * 1.1:  # Add 10% buffer for safety
                logger.error(f"Insufficient disk space for {filename}: {free / (1024**3):.2f} GB available, "
                             f"{estimated_size / (1024**3):.2f} GB needed")
                return jsonify({'error': 'Insufficient disk space for file assembly'}), 507  # 507 Insufficient Storage

            # Log system resources
            memory = psutil.virtual_memory()
            logger.info(f"System resources: Disk {free / (1024**3):.2f} GB available, "
                        f"Memory {memory.available / (1024**3):.2f} GB available")

            with open(final_path, 'wb') as f:
                for i in range(total_chunks):
                    chunk_path = os.path.join(temp_dir, f'chunk_{i}')
                    if not os.path.exists(chunk_path):
                        logger.error(f"Missing chunk {i} for {filename}")
                        raise FileNotFoundError(f'Missing chunk {i}')

                    chunk_size = os.path.getsize(chunk_path)
                    logger.info(f"Assembling chunk {i}/{total_chunks} for {filename}, size: {chunk_size} bytes")

                    with open(chunk_path, 'rb') as chunk_file:
                        copyfileobj(chunk_file, f)  # Stream copy to reduce memory usage

                    os.remove(chunk_path)  # Clean up chunk immediately to free space

            # Hash verification
            if expected_hash:
                with open(final_path, 'rb') as f:
                    hasher = hashlib.md5()
                    while chunk := f.read(4096):  # Stream hash computation
                        hasher.update(chunk)
                    assembled_hash = hasher.hexdigest()

                if assembled_hash != expected_hash:
                    os.remove(final_path)
                    logger.error(f"Hash mismatch for {filename}: expected {expected_hash}, got {assembled_hash}")
                    return jsonify({'error': 'File corrupted during assembly (hash mismatch)'}), 400

            elapsed_time = time.time() - start_time
            final_size = os.path.getsize(final_path)
            logger.info(f"File {filename} assembled at {final_path}, size: {final_size} bytes, took {elapsed_time:.2f} seconds")

            # Final cleanup (remove empty temp_dir)
            try:
                os.rmdir(temp_dir)
            except OSError as e:
                if e.errno != errno.ENOTEMPTY:  # Ignore if not empty (shouldn't happen)
                    logger.warning(f"Cleanup warning for {temp_dir}: {str(e)}")

            return jsonify({'success': True, 'file_path': final_path})

    except FileNotFoundError as e:
        logger.error(f"Assembly failed for {filename}: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except OSError as e:
        logger.error(f"OS error during assembly of {filename}: {str(e)}")
        return jsonify({'error': 'Server storage error'}), 500
    except Exception as e:
        logger.error(f"Unexpected error assembling {filename}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Assembly failed due to server error'}), 500
        
@bp.route('/check_upload_status', methods=['POST'])
@login_required
def check_upload_status():
    upload_id = request.form.get('upload_id')
    file_id = request.form.get('file_id')
    
    cache_dir = get_cache_folder()
    temp_base = os.path.join(cache_dir, 'temp_chunks')
    
    temp_dir = os.path.join(temp_base, upload_id, file_id)
    if not os.path.exists(temp_dir):
        return jsonify({'uploaded_chunks': 0})
    
    uploaded_chunks = len([f for f in os.listdir(temp_dir) if f.startswith('chunk_')])
    logger.info(f"Checked upload status for upload_id={upload_id}, file_id={file_id}: {uploaded_chunks} chunks uploaded")
    return jsonify({'uploaded_chunks': uploaded_chunks})

@bp.route('/delete_project/<project_name>', methods=['POST'])
@login_required
def delete_project(project_name):
    project_path = os.path.join(PROJECTS_FOLDER, secure_filename(project_name))
    if os.path.exists(project_path):
        try:
            shutil.rmtree(project_path)
            logger.info(f"Deleted project {project_name}")
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error deleting project {project_name}: {e}")
            return jsonify({'error': f'Deletion failed: {str(e)}'}), 500
    return jsonify({'error': 'Project not found'}), 404

@bp.route('/cleanup_chunks', methods=['POST'])
@login_required
def cleanup_chunks():
    cache_dir = get_cache_folder()
    temp_base = os.path.join(cache_dir, 'temp_chunks')
    try:
        if os.path.exists(temp_base):
            shutil.rmtree(temp_base, ignore_errors=True)
        os.makedirs(temp_base, exist_ok=True)
        logger.info("Cleaned up temporary chunk directory")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error cleaning up chunks: {e}")
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@bp.route('/cleanup_temp', methods=['POST'])
@login_required
def cleanup_temp():
    """Manually clean up all temporary files older than 1 hour."""
    cache_dir = get_cache_folder()
    temp_base = os.path.join(cache_dir, 'temp_chunks')
    try:
        current_time = time.time()
        cleaned = 0
        if os.path.exists(temp_base):
            for temp_upload_id in os.listdir(temp_base):
                temp_upload_path = os.path.join(temp_base, temp_upload_id)
                if os.path.isdir(temp_upload_path):
                    mtime = os.path.getmtime(temp_upload_path)
                    if current_time - mtime > 3600:  # 1 hour
                        shutil.rmtree(temp_upload_path, ignore_errors=True)
                        logger.info(f"Cleaned up stale temp directory: {temp_upload_path}")
                        cleaned += 1
        logger.info(f"Manual temp cleanup completed, removed {cleaned} stale directories")
        return jsonify({'success': True, 'cleaned': cleaned})
    except Exception as e:
        logger.error(f"Error during manual temp cleanup: {e}")
        return jsonify({'error': f'Cleanup failed: {str(e)}'}), 500

@bp.route('/get_project_overview/<project_name>', methods=['GET'])
@login_required
def get_project_overview(project_name):
    project_path = os.path.join(PROJECTS_FOLDER, secure_filename(project_name))
    if not os.path.exists(project_path):
        return jsonify({'error': 'Project not found'}), 404

    try:
        project = Project(project_name, '', '', project_path)
        total_images = project.get_image_count()
        annotated_images = project.get_annotated_image_count()
        class_distribution = project.get_class_distribution()
        annotations_per_image = project.get_annotations_per_image()
        non_annotated_images = total_images - annotated_images

        data = {
            'total_images': total_images,
            'annotated_images': annotated_images,
            'non_annotated_images': non_annotated_images,
            'class_distribution': class_distribution,
            'annotations_per_image': annotations_per_image
        }
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error fetching overview for {project_name}: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500