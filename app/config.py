import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Lớp cấu hình cơ bản cho ứng dụng Flask"""
    
    # Cấu hình bảo mật
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-should-be-changed'
    
    # Cấu hình cơ sở dữ liệu
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cấu hình tải lên
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
    STATIC_FOLDER = os.path.join('app', 'static')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Cấu hình phiên
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Cấu hình Email (để thêm vào sau này)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Cấu hình dịch thuật
    TRANSLATE_CACHE_TIMEOUT = 86400  # 24 giờ
    TRANSLATE_MAX_LENGTH = 5000  # Độ dài tối đa của văn bản cần dịch
    TRANSLATE_DEFAULT_SOURCE = 'en'  # Ngôn ngữ nguồn mặc định
    TRANSLATE_DEFAULT_TARGET = 'vi'  # Ngôn ngữ đích mặc định
    
    # Các cấu hình khác
    ITEMS_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        """Khởi tạo các thư mục cần thiết"""
        uploads_dir = os.path.join(app.root_path, 'static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Các thư mục khác nếu cần
        correct_audios_dir = os.path.join(app.root_path, 'static', 'correct_audios')
        os.makedirs(correct_audios_dir, exist_ok=True)

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường phát triển"""
    DEBUG = True
    

class ProductionConfig(Config):
    """Cấu hình cho môi trường sản xuất"""
    DEBUG = False
    
    # Thay đổi SECRET_KEY trong môi trường sản xuất
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-key-must-be-set-in-env'
    
    # Sử dụng cơ sở dữ liệu PostgreSQL trong sản xuất
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/language_app' 