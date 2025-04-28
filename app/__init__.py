from flask import Flask, render_template
from app.config import Config
from app.extensions import db, login_manager, migrate, socketio, csrf


def create_app(config_class=Config):
    """
    Khởi tạo ứng dụng Flask sử dụng mô hình Factory Pattern
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Khởi tạo các extension
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")
    csrf.init_app(app)

    # Thiết lập login manager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Đăng ký trang chủ trước
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Đăng ký các blueprint khác
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.tutorials import bp as tutorials_bp
    app.register_blueprint(tutorials_bp, url_prefix='/tutorials')

    from app.speech import bp as speech_bp
    app.register_blueprint(speech_bp)

    from app.chat import bp as chat_bp
    app.register_blueprint(chat_bp)

    from app.translate import bp as translate_bp
    app.register_blueprint(translate_bp)

    # Đăng ký các lệnh CLI
    from app.commands import register_commands
    register_commands(app)

    # Xử lý lỗi
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Đăng ký các hàm xử lý lỗi cho ứng dụng"""

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500