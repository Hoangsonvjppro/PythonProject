import uuid
from datetime import datetime
from app.extensions import db

class ChatRoom(db.Model):
    """Mô hình phòng trò chuyện"""
    __tablename__ = 'chat_rooms'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Mối quan hệ
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('RoomParticipant', backref='room', lazy=True, cascade='all, delete-orphan')
    
    def is_owner(self, user_id):
        """Kiểm tra người dùng có phải chủ phòng không"""
        return self.owner_id == user_id
    
    def __repr__(self):
        return f'<ChatRoom {self.name}>'

class RoomParticipant(db.Model):
    """Mô hình người tham gia phòng trò chuyện"""
    __tablename__ = 'room_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='_room_user_uc'),)
    
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<RoomParticipant Room={self.room_id} User={self.user_id}>'

class Message(db.Model):
    """Mô hình tin nhắn"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.id}>'

class StatusPost(db.Model):
    """Mô hình bài đăng trạng thái"""
    __tablename__ = 'status_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Mối quan hệ
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<StatusPost {self.id}>'

class PostComment(db.Model):
    """Mô hình bình luận bài đăng"""
    __tablename__ = 'post_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('status_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PostComment {self.id}>' 