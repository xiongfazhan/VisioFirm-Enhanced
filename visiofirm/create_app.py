from flask import Flask, send_from_directory
from visiofirm.config import PROJECTS_FOLDER
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = 'your_secret_key'
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB limit

    os.makedirs(PROJECTS_FOLDER, exist_ok=True)
    
    from visiofirm.routes.dashboard import bp as dashboard_bp
    from visiofirm.routes.annotation import bp as annotation_bp
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(annotation_bp)
    
    @app.route('/projects/<path:filename>')
    def serve_project_file(filename):
        return send_from_directory(PROJECTS_FOLDER, filename)
    
    return app