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
from modules.tutorials import tutorials_bp
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
app.config['ASYNC_MODE'] = True

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
    return db.session.get(User, int(user_id))  # Thay vì User.query.get(int(user_id))

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
app.register_blueprint(tutorials_bp, url_prefix='/tutorials')

# Khởi tạo dữ liệu mẫu ban đầu
def init_sample_data():
    # Thêm cấp độ (A1-C1)
    if not Level.query.first():
        levels = [
            Level(level_name='A1'),
            Level(level_name='A2'),
            Level(level_name='B1'),
            Level(level_name='B2'),
            Level(level_name='C1')
        ]
        db.session.add_all(levels)
        db.session.commit()

    # Thêm bài học mẫu cho mỗi cấp độ
    if not Lesson.query.first():
        # Lấy các cấp độ
        a1 = Level.query.filter_by(level_name='A1').first()
        a2 = Level.query.filter_by(level_name='A2').first()
        b1 = Level.query.filter_by(level_name='B1').first()
        b2 = Level.query.filter_by(level_name='B2').first()
        c1 = Level.query.filter_by(level_name='C1').first()

        lessons = [
            # Cấp độ A1
            Lesson(level_id=a1.level_id, title="Giới thiệu bản thân", description="Học cách giới thiệu tên, tuổi, và quốc tịch.", content="Trong bài học này, bạn sẽ học cách giới thiệu bản thân bằng tiếng Anh. Ví dụ: 'Hello, my name is John. I am 25 years old. I am from Vietnam.'"),
            Lesson(level_id=a1.level_id, title="Từ vựng cơ bản", description="Học các từ vựng cơ bản như màu sắc, số đếm, và ngày trong tuần.", content="Bài học này giới thiệu các từ vựng cơ bản: red (đỏ), blue (xanh), one (một), two (hai), Monday (Thứ Hai), Tuesday (Thứ Ba)."),
            Lesson(level_id=a1.level_id, title="Câu chào hỏi hàng ngày", description="Học các câu chào hỏi cơ bản.", content="Học cách chào hỏi: 'Good morning!' (Chào buổi sáng!), 'How are you?' (Bạn khỏe không?), 'I’m fine, thank you.' (Tôi khỏe, cảm ơn bạn)."),

            # Cấp độ A2
            Lesson(level_id=a2.level_id, title="Mô tả người và vật", description="Học cách mô tả ngoại hình và tính cách của người, vật.", content="Học cách mô tả: 'He is tall and handsome.' (Anh ấy cao và đẹp trai.) 'The cat is small and cute.' (Con mèo nhỏ và dễ thương.)"),
            Lesson(level_id=a2.level_id, title="Thì quá khứ đơn", description="Học cách sử dụng thì quá khứ đơn để kể về các sự kiện trong quá khứ.", content="Học thì quá khứ đơn: 'I went to the park yesterday.' (Hôm qua tôi đã đi công viên.) 'She watched a movie last night.' (Tối qua cô ấy đã xem một bộ phim.)"),
            Lesson(level_id=a2.level_id, title="Hỏi đường", description="Học cách hỏi và chỉ đường.", content="Học cách hỏi đường: 'Where is the nearest bus stop?' (Bến xe buýt gần nhất ở đâu?) 'Turn left at the next street.' (Rẽ trái ở con đường tiếp theo.)"),

            # Cấp độ B1
            Lesson(level_id=b1.level_id, title="Thảo luận về sở thích", description="Học cách nói về sở thích và hoạt động giải trí.", content="Học cách nói về sở thích: 'I enjoy playing football.' (Tôi thích chơi bóng đá.) 'She likes reading books.' (Cô ấy thích đọc sách.)"),
            Lesson(level_id=b1.level_id, title="Viết email đơn giản", description="Học cách viết email cơ bản để gửi cho bạn bè hoặc đồng nghiệp.", content="Học cách viết email: 'Dear Anna, How are you? I hope you are well. Best regards, John.' (Gửi Anna, Bạn khỏe không? Tôi hy vọng bạn khỏe. Trân trọng, John.)"),
            Lesson(level_id=b1.level_id, title="Thì hiện tại hoàn thành", description="Học cách sử dụng thì hiện tại hoàn thành.", content="Học thì hiện tại hoàn thành: 'I have just finished my homework.' (Tôi vừa làm xong bài tập.) 'She has visited Paris.' (Cô ấy đã đến Paris.)"),

            # Cấp độ B2
            Lesson(level_id=b2.level_id, title="Tranh luận cơ bản", description="Học cách đưa ra ý kiến và tranh luận.", content="Học cách tranh luận: 'In my opinion, technology is beneficial.' (Theo ý kiến của tôi, công nghệ có lợi.) 'I disagree because it can be addictive.' (Tôi không đồng ý vì nó có thể gây nghiện.)"),
            Lesson(level_id=b2.level_id, title="Viết đoạn văn mô tả", description="Học cách viết đoạn văn mô tả chi tiết.", content="Học cách viết đoạn văn: 'My hometown is a small village surrounded by mountains. The air is fresh, and the people are friendly.' (Quê tôi là một ngôi làng nhỏ được bao quanh bởi núi. Không khí trong lành và người dân thân thiện.)"),
            Lesson(level_id=b2.level_id, title="Thì tương lai", description="Học cách sử dụng các thì tương lai.", content="Học thì tương lai: 'I will visit my grandparents tomorrow.' (Ngày mai tôi sẽ thăm ông bà.) 'She is going to study abroad next year.' (Cô ấy sẽ đi du học vào năm tới.)"),

            # Cấp độ C1
            Lesson(level_id=c1.level_id, title="Phân tích bài báo", description="Học cách đọc và phân tích bài báo tiếng Anh.", content="Học cách phân tích bài báo: Đọc một bài báo về biến đổi khí hậu và trả lời các câu hỏi như: 'What is the main argument of the article?' (Luận điểm chính của bài báo là gì?)"),
            Lesson(level_id=c1.level_id, title="Viết luận nâng cao", description="Học cách viết bài luận chuyên sâu.", content="Học cách viết luận: 'To what extent does social media impact mental health? Provide arguments for both sides.' (Mạng xã hội ảnh hưởng đến sức khỏe tinh thần đến mức nào? Đưa ra lập luận cho cả hai phía.)"),
            Lesson(level_id=c1.level_id, title="Thảo luận chủ đề phức tạp", description="Học cách thảo luận các chủ đề phức tạp.", content="Học cách thảo luận: 'What are the ethical implications of artificial intelligence?' (Những hệ quả đạo đức của trí tuệ nhân tạo là gì?)")
        ]
        db.session.add_all(lessons)
        db.session.commit()

    # Thêm từ vựng mẫu
    if not Vocabulary.query.first():
        vocab = [
            # Cấp độ A1
            Vocabulary(word="hello", definition="Xin chào", example_sentence="Hello, how are you?", level_id=a1.level_id),
            Vocabulary(word="book", definition="Sách", example_sentence="I read a book.", level_id=a1.level_id),
            Vocabulary(word="red", definition="Màu đỏ", example_sentence="The apple is red.", level_id=a1.level_id),

            # Cấp độ A2
            Vocabulary(word="travel", definition="Du lịch", example_sentence="I love to travel.", level_id=a2.level_id),
            Vocabulary(word="restaurant", definition="Nhà hàng", example_sentence="We went to a restaurant.", level_id=a2.level_id),
            Vocabulary(word="beautiful", definition="Đẹp", example_sentence="The sunset is beautiful.", level_id=a2.level_id),

            # Cấp độ B1
            Vocabulary(word="hobby", definition="Sở thích", example_sentence="My hobby is reading.", level_id=b1.level_id),
            Vocabulary(word="email", definition="Thư điện tử", example_sentence="I sent an email.", level_id=b1.level_id),
            Vocabulary(word="opinion", definition="Ý kiến", example_sentence="In my opinion, this is a good idea.", level_id=b1.level_id),

            # Cấp độ B2
            Vocabulary(word="argument", definition="Lập luận", example_sentence="He presented a strong argument.", level_id=b2.level_id),
            Vocabulary(word="environment", definition="Môi trường", example_sentence="We need to protect the environment.", level_id=b2.level_id),
            Vocabulary(word="decision", definition="Quyết định", example_sentence="She made a wise decision.", level_id=b2.level_id),

            # Cấp độ C1
            Vocabulary(word="ethical", definition="Thuộc về đạo đức", example_sentence="There are ethical concerns about this issue.", level_id=c1.level_id),
            Vocabulary(word="impact", definition="Tác động", example_sentence="Social media has a big impact on our lives.", level_id=c1.level_id),
            Vocabulary(word="analyze", definition="Phân tích", example_sentence="We need to analyze the data carefully.", level_id=c1.level_id)
        ]
        db.session.add_all(vocab)
        db.session.commit()

    # Thêm bài kiểm tra speech test mặc định
    if not Test.query.first():
        speech_test = Test(
            test_type='speech',
            level_id=a1.level_id,
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

if __name__ == '__main__':
    app.debug = True
    with app.app_context():
        # db.drop_all()  # Xóa database cũ (cẩn thận, sẽ xóa dữ liệu cũ)
        db.create_all()  # Tạo database mới
        init_sample_data()  # Khởi tạo dữ liệu mẫu
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, port=5001)