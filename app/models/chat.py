import uuid
from datetime import datetime
from app.extensions import db

class ChatRoom(db.Model):
    """Phòng chat"""
    __tablename__ = 'chat_rooms'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='comments')
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('RoomParticipant', backref='room', lazy=True, cascade='all, delete-orphan')
    
    def is_owner(self, user_id):
        """Kiểm tra xem người dùng có phải là chủ phòng không"""
        return self.owner_id == user_id
    
    def add_participant(self, user_id):
        """Thêm người dùng vào phòng"""
        if not RoomParticipant.query.filter_by(room_id=self.id, user_id=user_id).first():
            participant = RoomParticipant(room_id=self.id, user_id=user_id)
            db.session.add(participant)
            return True
        return False
    
    def remove_participant(self, user_id):
        """Xóa người dùng khỏi phòng"""
        participant = RoomParticipant.query.filter_by(room_id=self.id, user_id=user_id).first()
        if participant:
            db.session.delete(participant)
            return True
        return False
    
    def get_participants(self):
        """Lấy danh sách người tham gia"""
        from app.models.user import User
        return User.query.join(RoomParticipant).filter(RoomParticipant.room_id == self.id).all()
    
    def get_last_message(self):
        """Lấy tin nhắn cuối cùng"""
        return Message.query.filter_by(room_id=self.id).order_by(Message.created_at.desc()).first()
    
    def __repr__(self):
        return f'<ChatRoom {self.name}>'


class RoomParticipant(db.Model):
    """Người tham gia phòng chat"""
    __tablename__ = 'room_participants'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    last_read = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='uq_room_user'),)
    
    # Relationships
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<RoomParticipant room={self.room_id} user={self.user_id}>'


class Message(db.Model):
    """Tin nhắn trong phòng chat"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_system = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<Message {self.id}>'


class StatusPost(db.Model):
    """Bài viết trạng thái"""
    __tablename__ = 'status_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    author = db.relationship('User', backref='posts')
    
    def __repr__(self):
        return f'<StatusPost {self.id}>'


class Comment(db.Model):
    """Bình luận cho bài viết"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('status_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='comments')
    
    def __repr__(self):
        return f'<Comment {self.id}>' 