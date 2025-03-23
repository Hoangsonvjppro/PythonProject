from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps
from flask_cors import CORS
from flask_socketio import SocketIO, send
from models.models import db, User, Level, Lesson, UserProgress, Vocabulary, Test, SampleSentence, SpeechTest
from modules.speech import speech_bp
from modules.translate import translate_bp
from modules.chat import chatting, register_socketio_events
import os

# Khởi tạo Flask
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, async_mode='eventlet')

# Cấu hình
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_app.db'  # Đổi tên DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Khởi tạo cơ sở dữ liệu
db.init_app(app)

# Cấu hình Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "login"

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
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')  # Mặc định là user

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
        flash("Đăng ký thành công! Bạn có thể đăng nhập.", "success")
        return redirect(url_for('settings'))
    return redirect(url_for('settings'))  # Nếu GET, quay về Settings

# Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
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
    return redirect(url_for('settings'))  # Nếu GET, quay về Settings

# Route cập nhật hồ sơ
@app.route('/update-profile', methods=['GET', 'POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        avatar = request.files['avatar']

        if new_username:
            current_user.username = new_username
        if new_password:
            current_user.set_password(new_password)
        if avatar:
            filename = secure_filename(avatar.filename)
            avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            current_user.avatar = filename

        db.session.commit()
        flash('Cập nhật hồ sơ thành công!', 'success')
        return redirect(url_for('settings'))
    return redirect(url_for('settings'))  # Nếu GET, quay về Settings

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
    return jsonify({'success': False, 'error': 'Lỗi máy chủ nội bộ'}), 500

# Đăng ký blueprints
app.register_blueprint(speech_bp)
app.register_blueprint(translate_bp)
app.register_blueprint(chatting)
register_socketio_events(socketio)

# Khởi tạo dữ liệu mẫu ban đầu
def init_sample_data():
    # Thêm cấp độ (A1-C1)
    if not Level.query.first():
        levels = ['A1', 'A2', 'B1', 'B2', 'C1']
        for level_name in levels:
            level = Level(level_name=level_name)
            db.session.add(level)
        db.session.commit()

    # Thêm bài kiểm tra speech test mặc định
    if not Test.query.first():
        level_a1 = Level.query.filter_by(level_name='A1').first()
        speech_test = Test(
            test_type='speech',
            level_id=level_a1.level_id,
            description='Speech Test for Pronunciation Evaluation'
        )
        db.session.add(speech_test)
        db.session.commit()

        # Thêm 4 câu mẫu cho speech test
        sample_sentences = [
            ("The quick brown fox jumps over the lazy dog.", "correct_audios/sentence1.wav"),
            ("She sells seashells by the seashore.", "correct_audios/sentence2.wav"),
            ("How much wood would a woodchuck chuck?", "correct_audios/sentence3.wav"),
            ("Peter Piper picked a peck of pickled peppers.", "correct_audios/sentence4.wav")
        ]
        for sentence_text, audio_file in sample_sentences:
            sentence = SampleSentence(
                test_id=speech_test.test_id,
                sentence_text=sentence_text,
                correctAudio_file=audio_file
            )
            db.session.add(sentence)
        db.session.commit()

    # Thêm bài học mẫu
    if not Lesson.query.first():
        levels = Level.query.all()
        for level in levels:
            lesson = Lesson(
                level_id=level.level_id,
                title=f"Basic Pronunciation for {level.level_name}",
                description=f"Learn basic pronunciation skills for {level.level_name} level.",
                content=f"This is a sample lesson for {level.level_name}."
            )
            db.session.add(lesson)
        db.session.commit()

    # Thêm từ vựng mẫu
    if not Vocabulary.query.first():
        levels = Level.query.all()
        sample_vocab = [
            ("hello", "Xin chào", "Hello, how are you?", "A1"),
            ("book", "Sách", "I read a book.", "A1"),
            ("negotiation", "Đàm phán", "The negotiation was successful.", "C1"),
            ("strategy", "Chiến lược", "We need a new strategy.", "B2")
        ]
        for word, definition, example, level_name in sample_vocab:
            level = Level.query.filter_by(level_name=level_name).first()
            vocab = Vocabulary(
                word=word,
                definition=definition,
                example_sentence=example,
                level_id=level.level_id
            )
            db.session.add(vocab)
        db.session.commit()

if __name__ == '__main__':
    app.debug = True
    with app.app_context():
        # db.drop_all()  # Xóa database cũ (cẩn thận, sẽ xóa dữ liệu cũ)
        db.create_all()  # Tạo database mới
        init_sample_data()  # Khởi tạo dữ liệu mẫu
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)