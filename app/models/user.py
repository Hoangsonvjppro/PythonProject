from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    """Mô hình người dùng"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default="default.jpg")
    role = db.Column(db.String(50), default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    active = db.Column(db.Boolean, default=True)

    # Relationships
    progress = db.relationship('UserProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    speech_tests = db.relationship('SpeechTest', backref='user', lazy=True, cascade='all, delete-orphan')
    owned_rooms = db.relationship('ChatRoom', backref='owner', lazy=True,
                                  foreign_keys='ChatRoom.owner_id', cascade='all, delete-orphan')
    lessons_created = db.relationship('Lesson', backref='creator', lazy=True,
                                      foreign_keys='Lesson.created_by')
    levels_created = db.relationship('Level', backref='creator', lazy=True,
                                     foreign_keys='Level.created_by')

    def set_password(self, password):
        """Lưu mật khẩu được hash"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Kiểm tra mật khẩu"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Kiểm tra xem người dùng có phải là admin không"""
        return self.role == 'admin'

    def get_completed_lessons(self):
        """Lấy danh sách bài học đã hoàn thành"""
        return [p.lesson for p in self.progress if p.completion_status]

    def get_completion_percentage(self, level_id=None):
        """Tính phần trăm hoàn thành cho cấp độ hoặc toàn bộ"""
        from app.models.learning import Lesson

        if level_id:
            total_lessons = Lesson.query.filter_by(level_id=level_id, active=True).count()
            completed = [p for p in self.progress if p.lesson.level_id == level_id and p.completion_status]
        else:
            total_lessons = Lesson.query.filter_by(active=True).count()
            completed = [p for p in self.progress if p.completion_status]

        if total_lessons == 0:
            return 0

        return round((len(completed) / total_lessons) * 100)

    @classmethod
    def create_admin(cls, username, email, password):
        """Tạo người dùng admin"""
        user = cls(username=username, email=email, role='admin')
        user.set_password(password)
        return user

    def __repr__(self):
        return f'<User {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    """Hàm tải người dùng cho Flask-Login"""
    return User.query.get(int(user_id))