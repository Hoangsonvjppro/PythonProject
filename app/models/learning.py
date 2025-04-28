from datetime import datetime
from app.extensions import db


class Level(db.Model):
    """Cấp độ học tập"""
    __tablename__ = 'levels'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    level_name = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='graduation-cap')
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    lessons = db.relationship('Lesson', backref='level', lazy=True,
                              order_by='Lesson.order', cascade='all, delete-orphan')
    vocabulary = db.relationship('Vocabulary', backref='level', lazy=True,
                                 cascade='all, delete-orphan')
    tests = db.relationship('Test', backref='level', lazy=True,
                            cascade='all, delete-orphan')

    def get_progress_for_user(self, user_id):
        """Tính toán tiến độ của người dùng cho cấp độ này"""
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return 0
        return user.get_completion_percentage(self.id)

    def __repr__(self):
        return f'<Level {self.level_name}>'


class Lesson(db.Model):
    """Bài học"""
    __tablename__ = 'lessons'
    __table_args__ = {'extend_existing': True}

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

    # Relationships
    progress = db.relationship('UserProgress', backref='lesson', lazy=True, cascade='all, delete-orphan')
    pronunciation_exercises = db.relationship('PronunciationExercise', backref='lesson', lazy=True,
                                              cascade='all, delete-orphan')

    def is_completed(self, user_id):
        """Kiểm tra xem bài học đã hoàn thành chưa đối với người dùng cụ thể"""
        progress = UserProgress.query.filter_by(
            user_id=user_id, lesson_id=self.id, completion_status=True).first()
        return progress is not None

    def get_next_lesson(self):
        """Lấy bài học tiếp theo trong cùng cấp độ"""
        return Lesson.query.filter(
            Lesson.level_id == self.level_id,
            Lesson.order > self.order,
            Lesson.active == True
        ).order_by(Lesson.order).first()

    def __repr__(self):
        return f'<Lesson {self.title}>'


class UserProgress(db.Model):
    """Tiến độ học tập của người dùng"""
    __tablename__ = 'user_progress'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'lesson_id', name='uq_user_lesson'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    completion_status = db.Column(db.Boolean, default=False)
    score = db.Column(db.Float)
    completed_at = db.Column(db.DateTime)
    attempts = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.DateTime)

    def __repr__(self):
        return f'<UserProgress user_id={self.user_id} lesson_id={self.lesson_id}>'


class Vocabulary(db.Model):
    """Từ vựng"""
    __tablename__ = 'vocabulary'
    __table_args__ = {'extend_existing': True}  # Thêm dòng này

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    definition = db.Column(db.Text)
    example = db.Column(db.Text)
    pronunciation = db.Column(db.String(100))
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<Vocabulary {self.word}>'


class Test(db.Model):
    """Mô hình kiểm tra"""
    __tablename__ = 'tests'
    __table_args__ = {'extend_existing': True}  # Thêm dòng này

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
    __table_args__ = {'extend_existing': True}  # Thêm dòng này

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    sentence_text = db.Column(db.Text, nullable=False)
    audio_file = db.Column(db.String(200))

    # Mối quan hệ
    speech_tests = db.relationship('SpeechTest', backref='sentence', lazy=True)

    def __repr__(self):
        return f'<SampleSentence {self.id}>'


class PronunciationExercise(db.Model):
    """Bài tập phát âm"""
    __tablename__ = 'pronunciation_exercises'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    audio_reference = db.Column(db.String(200))
    is_required = db.Column(db.Boolean, default=True)
    min_accuracy = db.Column(db.Float, default=70.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Relationships
    attempts = db.relationship('PronunciationAttempt', backref='exercise', lazy=True,
                               cascade='all, delete-orphan')

    def get_best_score(self, user_id):
        """Lấy điểm cao nhất của người dùng cho bài tập này"""
        best_attempt = PronunciationAttempt.query.filter_by(
            exercise_id=self.id, user_id=user_id).order_by(PronunciationAttempt.accuracy.desc()).first()
        return best_attempt.accuracy if best_attempt else 0

    def __repr__(self):
        return f'<PronunciationExercise {self.id}>'


class PronunciationAttempt(db.Model):
    """Lần thử phát âm của người dùng"""
    __tablename__ = 'pronunciation_attempts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('pronunciation_exercises.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_audio = db.Column(db.String(200))
    accuracy = db.Column(db.Float)
    feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PronunciationAttempt {self.id}>'


class SpeechTest(db.Model):
    """Mô hình lưu lại kết quả kiểm tra phát âm"""
    __tablename__ = 'speech_tests'
    __table_args__ = {'extend_existing': True}  # Thêm dòng này

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