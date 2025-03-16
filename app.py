from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from flask_cors import CORS
from flask_socketio import SocketIO
from modules.speech import speech_bp
from modules.translate import translate_bp
from modules.chat import chatting, register_socketio_events
from datetime import datetime
import os

# Khởi tạo Flask
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

# Cấu hình database
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Lấy đường dẫn thư mục hiện tại
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'users.db')}"
app.config['SQLALCHEMY_BINDS'] = {
    'chats': f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'chats.db')}"
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Khởi tạo SQLAlchemy
db = SQLAlchemy(app)

# Cấu hình Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Model User
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default="default.jpg")
    role = db.Column(db.String(50), nullable=False, default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Model Chat
class ChatMessage(db.Model):
    __bind_key__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default="default.jpg")
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ChatMessage {self.username}: {self.message}>"

# Decorator yêu cầu quyền admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Load user cho Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route trang chủ
@app.route('/')
def home():
    return render_template('home.html', current_user=current_user)

# Route Settings
@app.route('/settings')
def settings():
    return render_template('settings.html', current_user=current_user)

# Route đăng ký
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    role = request.form.get('role', 'user')

    if User.query.filter_by(username=username).first():
        flash("Tên người dùng đã tồn tại!", "danger")
        return redirect(url_for('settings'))
    if User.query.filter_by(email=email).first():
        flash("Email đã được đăng ký!", "danger")
        return redirect(url_for('settings'))

    new_user = User(username=username, email=email, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash("Đăng ký thành công!", "success")
    return redirect(url_for('settings'))

# Route đăng nhập
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user)
        flash("Đăng nhập thành công!", "success")
        return redirect(url_for('home'))
    else:
        flash("Tên người dùng hoặc mật khẩu không đúng!", "danger")
        return redirect(url_for('settings'))

# Route cập nhật hồ sơ
@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    new_username = request.form.get('username')
    new_password = request.form.get('password')
    avatar = request.files.get('avatar')

    if new_username:
        current_user.username = new_username
    if new_password:
        current_user.set_password(new_password)
    if avatar:
        filename = secure_filename(avatar.filename)
        avatar_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        avatar.save(avatar_path)
        current_user.avatar = filename

    db.session.commit()
    flash('Cập nhật hồ sơ thành công!', 'success')
    return redirect(url_for('settings'))

# Route bảng điều khiển admin
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin.html', users=users)

# Route đăng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('home'))

# Xử lý lỗi 500
@app.errorhandler(500)
def handle_internal_error(error):
    print(f"❌ Lỗi máy chủ: {error}")  # Debug lỗi
    return jsonify({'success': False, 'error': 'Lỗi máy chủ nội bộ'}), 500

# Đăng ký blueprints
app.register_blueprint(speech_bp)
app.register_blueprint(translate_bp)
app.register_blueprint(chatting)

# Đăng ký sự kiện SocketIO
register_socketio_events(socketio)

# Chạy ứng dụng
if __name__ == '__main__':
    app.debug = True
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
