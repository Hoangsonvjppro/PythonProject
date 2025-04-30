from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from cachelib import SimpleCache
import os

# Cờ để kiểm tra xem SocketIO có sẵn sàng không
socketio_available = False

# Khởi tạo các extension
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

# Cache cho dịch thuật
translate_cache = SimpleCache(default_timeout=86400)  # 24 giờ

# Đảm bảo thư mục uploads tồn tại
def ensure_uploads_dir():
    upload_dir = os.path.join('app', 'static', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    
    # Tạo file default.jpg nếu chưa có
    default_jpg = os.path.join(upload_dir, 'default.jpg')
    if not os.path.exists(default_jpg):
        with open(default_jpg, 'w') as f:
            f.write('')

# Thử import và khởi tạo SocketIO nếu có thể
try:
    from flask_socketio import SocketIO
    socketio = SocketIO()
    socketio_available = True
    print("SocketIO available and initialized.")
except (ImportError, ValueError) as e:
    print(f"SocketIO not available or failed to initialize: {e}")
    # Tạo một class giả để tránh lỗi import
    class DummySocketIO:
        def init_app(self, app, **kwargs):
            pass
        def run(self, app, **kwargs):
            app.run(**kwargs)
    socketio = DummySocketIO() 