import os
import platform

def get_cache_folder():
    system = platform.system()
    if system == 'Windows':
        cache_dir = os.path.join(os.environ['LOCALAPPDATA'], 'visiofirm_cache')
    elif system == 'Darwin':  # MacOS
        cache_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Caches', 'visiofirm_cache')
    elif system == 'Linux':
        cache_dir = os.path.join(os.path.expanduser('~'), '.cache', 'visiofirm_cache')
    else:
        raise RuntimeError("Unsupported operating system")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def get_db_path():
    return os.path.join(get_cache_folder(), 'users.db')

PROJECTS_FOLDER = get_cache_folder()
VALID_IMAGE_EXTENSIONS = {'.webp', '.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.avif'}
WEIGHTS_FOLDER = os.path.join(get_cache_folder(), 'weights')