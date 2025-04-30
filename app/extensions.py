from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from cachelib import SimpleCache

# Khởi tạo các extension
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
socketio = SocketIO()
csrf = CSRFProtect()

# Cache cho dịch thuật
translate_cache = SimpleCache(default_timeout=86400)  # 24 giờ 