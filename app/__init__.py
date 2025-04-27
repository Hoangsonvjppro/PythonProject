from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate, socketio
from app.models import user, learning, chat

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
    
    # Thiết lập login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để truy cập trang này.'
    login_manager.login_message_category = 'warning'
    
    # Đăng ký các blueprint
    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.tutorials import bp as tutorials_bp
    app.register_blueprint(tutorials_bp, url_prefix='/tutorials')
    
    from app.speech import bp as speech_bp
    app.register_blueprint(speech_bp)
    
    from app.chat import bp as chat_bp
    app.register_blueprint(chat_bp)
    
    from app.translate import bp as translate_bp
    app.register_blueprint(translate_bp)
    
    # Đăng ký trang chủ
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Đăng ký các lệnh CLI
    from app.commands import register_commands
    register_commands(app)
    
    return app 