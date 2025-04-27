from datetime import datetime
from app.extensions import db

class Level(db.Model):
    """Mô hình cấp độ học tập"""
    __tablename__ = 'levels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default="graduation-cap")
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Mối quan hệ
    lessons = db.relationship('Lesson', backref='level', lazy=True, 
                             cascade='all, delete-orphan', order_by='Lesson.order')
    vocabulary = db.relationship('Vocabulary', backref='level', lazy=True, 
                                cascade='all, delete-orphan')
    tests = db.relationship('Test', backref='level', lazy=True, 
                           cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Level {self.name}>'

class Lesson(db.Model):
    """Mô hình bài học"""
    __tablename__ = 'lessons'
    
    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Mối quan hệ
    progress = db.relationship('UserProgress', backref='lesson', lazy=True, 
                              cascade='all, delete-orphan')
    pronunciation_exercises = db.relationship('PronunciationExercise', backref='lesson', lazy=True,
                                             cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lesson {self.title}>'

class UserProgress(db.Model):
    """Mô hình tiến độ học tập của người dùng"""
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    completion_status = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)
    completed_at = db.Column(db.DateTime)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson'),)
    
    def __repr__(self):
        return f'<Progress User={self.user_id} Lesson={self.lesson_id}>'

class Vocabulary(db.Model):
    """Mô hình từ vựng"""
    __tablename__ = 'vocabulary'
    
    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    word = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text)
    example_sentence = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Vocabulary {self.word}>'

class Test(db.Model):
    """Mô hình kiểm tra"""
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)  # speech/vocab/grammar
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Mối quan hệ
    sentences = db.relationship('SampleSentence', backref='test', lazy=True, 
                               cascade='all, delete-orphan')
    speech_tests = db.relationship('SpeechTest', backref='test', lazy=True)
    
    def __repr__(self):
        return f'<Test {self.title}>'

class SampleSentence(db.Model):
    """Mô hình câu mẫu cho bài kiểm tra"""
    __tablename__ = 'sample_sentences'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    sentence_text = db.Column(db.Text, nullable=False)
    audio_file = db.Column(db.String(200))
    
    # Mối quan hệ
    speech_tests = db.relationship('SpeechTest', backref='sentence', lazy=True)
    
    def __repr__(self):
        return f'<SampleSentence {self.id}>'

class PronunciationExercise(db.Model):
    """Mô hình bài tập phát âm cho bài học"""
    __tablename__ = 'pronunciation_exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    audio_file = db.Column(db.String(200))
    is_required = db.Column(db.Boolean, default=True)  # Bắt buộc hoàn thành để pass bài học
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Mối quan hệ
    attempts = db.relationship('PronunciationAttempt', backref='exercise', lazy=True,
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PronunciationExercise {self.id}>'

class PronunciationAttempt(db.Model):
    """Mô hình lưu lại nỗ lực phát âm của người dùng"""
    __tablename__ = 'pronunciation_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('pronunciation_exercises.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    audio_file = db.Column(db.String(200))
    accuracy = db.Column(db.Float)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PronunciationAttempt {self.id}>'

class SpeechTest(db.Model):
    """Mô hình lưu lại kết quả kiểm tra phát âm"""
    __tablename__ = 'speech_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sample_sentences.id'), nullable=False)
    audio_file = db.Column(db.String(200))
    accuracy = db.Column(db.Float)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SpeechTest {self.id}>' 