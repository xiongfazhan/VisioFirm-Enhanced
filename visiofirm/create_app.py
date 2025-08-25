from flask import Flask, send_from_directory
from flask_login import LoginManager
from visiofirm.config import PROJECTS_FOLDER
from visiofirm.models.user import init_db, get_user_by_id, User
import os

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.secret_key = 'VISIOFIRM'
    app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB limit

    os.makedirs(PROJECTS_FOLDER, exist_ok=True)
    with app.app_context():
        init_db()

    from visiofirm.routes.dashboard import bp as dashboard_bp
    from visiofirm.routes.annotation import bp as annotation_bp
    from visiofirm.routes.auth import bp as auth_bp
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(annotation_bp)
    app.register_blueprint(auth_bp)

    @app.route('/projects/<path:filename>')
    def serve_project_file(filename):
        return send_from_directory(PROJECTS_FOLDER, filename)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        user_data = get_user_by_id(user_id)
        if user_data:
            return User(user_data[0], user_data[1], user_data[3], user_data[4], user_data[5], user_data[6])
        return None

    return app