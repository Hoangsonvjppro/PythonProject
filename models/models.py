# models/models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

# Khởi tạo db (sẽ được khởi tạo từ app.py)
db = SQLAlchemy()

# Model Users
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), nullable=True, default="default.jpg")
    role = db.Column(db.String(50), nullable=False, default="user")

    # Relationships
    progress = db.relationship('UserProgress', backref='user', lazy=True)
    speech_tests = db.relationship('SpeechTest', backref='user', lazy=True)
    owned_rooms = db.relationship('ChatRoom', backref='owner', lazy=True, foreign_keys='ChatRoom.owner_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Model Levels
class Level(db.Model):
    __tablename__ = 'levels'
    level_id = db.Column(db.Integer, primary_key=True)
    level_name = db.Column(db.String(10), unique=True, nullable=False)

    # Relationships
    lessons = db.relationship('Lesson', backref='level', lazy=True)
    vocabulary = db.relationship('Vocabulary', backref='level', lazy=True)
    tests = db.relationship('Test', backref='level', lazy=True)

# Model Lessons
class Lesson(db.Model):
    __tablename__ = 'lessons'
    lesson_id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.level_id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)

    # Relationships
    progress = db.relationship('UserProgress', backref='lesson', lazy=True)

# Model User_Progress
class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    progress_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'), nullable=False)
    completion_status = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)
    completed_at = db.Column(db.DateTime)

# Model Vocabulary
class Vocabulary(db.Model):
    __tablename__ = 'vocabulary'
    word_id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text)
    example_sentence = db.Column(db.Text)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.level_id'), nullable=False)

# Model Tests
class Test(db.Model):
    __tablename__ = 'tests'
    test_id = db.Column(db.Integer, primary_key=True)
    test_type = db.Column(db.String(50), nullable=False)  # speech/vocab/grammar
    level_id = db.Column(db.Integer, db.ForeignKey('levels.level_id'), nullable=False)
    description = db.Column(db.Text)

    # Relationships
    sentences = db.relationship('SampleSentence', backref='test', lazy=True)
    speech_tests = db.relationship('SpeechTest', backref='test', lazy=True)

# Model Sample_Sentences
class SampleSentence(db.Model):
    __tablename__ = 'sample_sentences'
    sentence_id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.test_id'), nullable=False)
    sentence_text = db.Column(db.Text, nullable=False)
    correctAudio_file = db.Column(db.String(200))

    # Relationships
    speech_tests = db.relationship('SpeechTest', backref='sentence', lazy=True)

# Model SpeechTests
class SpeechTest(db.Model):
    __tablename__ = 'speech_tests'
    speechtest_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.test_id'), nullable=False)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sample_sentences.sentence_id'), nullable=False)
    userAudio_file = db.Column(db.String(200))
    similarity_score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.now())

# Chat models
class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'
    room_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    messages = db.relationship('Message', backref='room', lazy=True, cascade='all, delete-orphan')
    participants = db.relationship('RoomParticipant', backref='room', lazy=True, cascade='all, delete-orphan')

    def is_owner(self, user_id):
        return self.owner_id == user_id

class RoomParticipant(db.Model):
    __tablename__ = 'room_participants'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.room_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('room_id', 'user_id', name='_room_user_uc'),)
    
    user = db.relationship('User')

class Message(db.Model):
    __tablename__ = 'messages'
    message_id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), db.ForeignKey('chat_rooms.room_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='messages')

class StatusPost(db.Model):
    __tablename__ = 'status_posts'
    post_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    comments = db.relationship('PostComment', backref='post', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='posts')

class PostComment(db.Model):
    __tablename__ = 'post_comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('status_posts.post_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='comments')