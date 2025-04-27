from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app.extensions import db, login_manager

class User(db.Model, UserMixin):
    """Mô hình người dùng"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default="default.jpg")
    role = db.Column(db.String(50), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Mối quan hệ
    progress = db.relationship('UserProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    speech_tests = db.relationship('SpeechTest', backref='user', lazy=True, cascade='all, delete-orphan')
    owned_rooms = db.relationship('ChatRoom', backref='owner', lazy=True, 
                                 foreign_keys='ChatRoom.owner_id', cascade='all, delete-orphan')
    posts = db.relationship('StatusPost', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('PostComment', backref='author', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='author', lazy=True, cascade='all, delete-orphan')
    
    # Mối quan hệ admin - nội dung
    created_levels = db.relationship('Level', backref='creator', lazy=True,
                                    foreign_keys='Level.created_by')
    created_lessons = db.relationship('Lesson', backref='creator', lazy=True,
                                     foreign_keys='Lesson.created_by')
    
    def set_password(self, password):
        """Mã hóa và thiết lập mật khẩu"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Kiểm tra mật khẩu"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Kiểm tra người dùng có phải admin không"""
        return self.role == 'admin'
    
    @classmethod
    def create_admin(cls, username, email, password):
        """Tạo tài khoản admin mới"""
        user = cls(username=username, email=email, role='admin')
        user.set_password(password)
        return user
    
    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Hàm bắt buộc cho Flask-Login để tải người dùng từ ID phiên"""
    return User.query.get(int(user_id)) 