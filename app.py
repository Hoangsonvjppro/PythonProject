import eventlet
eventlet.monkey_patch()

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
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app)

# Cấu hình Socket.IO với eventlet
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
migrate = Migrate(app, db)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def home():
    return render_template('home.html', current_user=current_user)

@app.route('/settings')
def settings():
    return render_template('settings.html', current_user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
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
        flash("Đăng ký thành công! Bạn có thể đăng nhập.", "success")
        return redirect(url_for('settings'))
    return redirect(url_for('settings'))

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
    return redirect(url_for('settings'))

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
    return redirect(url_for('settings'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('home'))

@app.errorhandler(500)
def handle_internal_error(error):
    return jsonify({'success': False, 'error': 'Lỗi máy chủ nội bộ'}), 500

app.register_blueprint(speech_bp)
app.register_blueprint(translate_bp)
app.register_blueprint(chatting)
register_socketio_events(socketio)
app.register_blueprint(tutorials_bp, url_prefix='/tutorials')

def init_sample_data():
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

    if not Lesson.query.first():
        a1 = Level.query.filter_by(level_name='A1').first()
        a2 = Level.query.filter_by(level_name='A2').first()
        b1 = Level.query.filter_by(level_name='B1').first()
        b2 = Level.query.filter_by(level_name='B2').first()
        c1 = Level.query.filter_by(level_name='C1').first()

        lessons = [
            Lesson(level_id=a1.level_id, title="Giới thiệu bản thân", description="Học cách giới thiệu tên, tuổi, và quốc tịch.", content="Trong bài học này, bạn sẽ học cách giới thiệu bản thân bằng tiếng Anh. Ví dụ: 'Hello, my name is John. I am 25 years old. I am from Vietnam.'"),
            Lesson(level_id=a1.level_id, title="Từ vựng cơ bản", description="Học các từ vựng cơ bản như màu sắc, số đếm, và ngày trong tuần.", content="Bài học này giới thiệu các từ vựng cơ bản: red (đỏ), blue (xanh), one (một), two (hai), Monday (Thứ Hai), Tuesday (Thứ Ba)."),
            Lesson(level_id=a1.level_id, title="Câu chào hỏi hàng ngày", description="Học các câu chào hỏi cơ bản.", content="Học cách chào hỏi: 'Good morning!' (Chào buổi sáng!), 'How are you?' (Bạn khỏe không?), 'I'm fine, thank you.' (Tôi khỏe, cảm ơn bạn)."),
            Lesson(level_id=a2.level_id, title="Mô tả người và vật", description="Học cách mô tả ngoại hình và tính cách của người, vật.", content="Học cách mô tả: 'He is tall and handsome.' (Anh ấy cao và đẹp trai.) 'The cat is small and cute.' (Con mèo nhỏ và dễ thương.)"),
            Lesson(level_id=a2.level_id, title="Thì quá khứ đơn", description="Học cách sử dụng thì quá khứ đơn để kể về các sự kiện trong quá khứ.", content="Học thì quá khứ đơn: 'I went to the park yesterday.' (Hôm qua tôi đã đi công viên.) 'She watched a movie last night.' (Tối qua cô ấy đã xem một bộ phim.)"),
            Lesson(level_id=a2.level_id, title="Hỏi đường", description="Học cách hỏi và chỉ đường.", content="Học cách hỏi đường: 'Where is the nearest bus stop?' (Bến xe buýt gần nhất ở đâu?) 'Turn left at the next street.' (Rẽ trái ở con đường tiếp theo.)"),
            Lesson(level_id=b1.level_id, title="Thảo luận về sở thích", description="Học cách nói về sở thích và hoạt động giải trí.", content="Học cách nói về sở thích: 'I enjoy playing football.' (Tôi thích chơi bóng đá.) 'She likes reading books.' (Cô ấy thích đọc sách.)"),
            Lesson(level_id=b1.level_id, title="Viết email đơn giản", description="Học cách viết email cơ bản để gửi cho bạn bè hoặc đồng nghiệp.", content="Học cách viết email: 'Dear Anna, How are you? I hope you are well. Best regards, John.' (Gửi Anna, Bạn khỏe không? Tôi hy vọng bạn khỏe. Trân trọng, John.)"),
            Lesson(level_id=b1.level_id, title="Thì hiện tại hoàn thành", description="Học cách sử dụng thì hiện tại hoàn thành.", content="Học thì hiện tại hoàn thành: 'I have just finished my homework.' (Tôi vừa làm xong bài tập.) 'She has visited Paris.' (Cô ấy đã đến Paris.)"),
            Lesson(level_id=b2.level_id, title="Tranh luận cơ bản", description="Học cách đưa ra ý kiến và tranh luận.", content="Học cách tranh luận: 'In my opinion, technology is beneficial.' (Theo ý kiến của tôi, công nghệ có lợi.) 'I disagree because it can be addictive.' (Tôi không đồng ý vì nó có thể gây nghiện.)"),
            Lesson(level_id=b2.level_id, title="Viết đoạn văn mô tả", description="Học cách viết đoạn văn mô tả chi tiết.", content="Học cách viết đoạn văn: 'My hometown is a small village surrounded by mountains. The air is fresh, and the people are friendly.' (Quê tôi là một ngôi làng nhỏ được bao quanh bởi núi. Không khí trong lành và người dân thân thiện.)"),
            Lesson(level_id=b2.level_id, title="Thì tương lai", description="Học cách sử dụng các thì tương lai.", content="Học thì tương lai: 'I will visit my grandparents tomorrow.' (Ngày mai tôi sẽ thăm ông bà.) 'She is going to study abroad next year.' (Cô ấy sẽ đi du học vào năm tới.)"),
            Lesson(level_id=c1.level_id, title="Phân tích bài báo", description="Học cách đọc và phân tích bài báo tiếng Anh.", content="Học cách phân tích bài báo: Đọc một bài báo về biến đổi khí hậu và trả lời các câu hỏi như: 'What is the main argument of the article?' (Luận điểm chính của bài báo là gì?)"),
            Lesson(level_id=c1.level_id, title="Viết luận nâng cao", description="Học cách viết bài luận chuyên sâu.", content="Học cách viết luận: 'To what extent does social media impact mental health? Provide arguments for both sides.' (Mạng xã hội ảnh hưởng đến sức khỏe tinh thần đến mức nào? Đưa ra lập luận cho cả hai phía.)"),
            Lesson(level_id=c1.level_id, title="Thảo luận chủ đề phức tạp", description="Học cách thảo luận các chủ đề phức tạp.", content="Học cách thảo luận: 'What are the ethical implications of artificial intelligence?' (Những hệ quả đạo đức của trí tuệ nhân tạo là gì?)")
        ]
        db.session.add_all(lessons)
        db.session.commit()

    if not Vocabulary.query.first():
        vocab = [
            Vocabulary(word="hello", definition="Xin chào", example_sentence="Hello, how are you?", level_id=a1.level_id),
            Vocabulary(word="book", definition="Sách", example_sentence="I read a book.", level_id=a1.level_id),
            Vocabulary(word="red", definition="Màu đỏ", example_sentence="The apple is red.", level_id=a1.level_id),
            Vocabulary(word="travel", definition="Du lịch", example_sentence="I love to travel.", level_id=a2.level_id),
            Vocabulary(word="restaurant", definition="Nhà hàng", example_sentence="We went to a restaurant.", level_id=a2.level_id),
            Vocabulary(word="beautiful", definition="Đẹp", example_sentence="The sunset is beautiful.", level_id=a2.level_id),
            Vocabulary(word="hobby", definition="Sở thích", example_sentence="My hobby is reading.", level_id=b1.level_id),
            Vocabulary(word="email", definition="Thư điện tử", example_sentence="I sent an email.", level_id=b1.level_id),
            Vocabulary(word="opinion", definition="Ý kiến", example_sentence="In my opinion, this is a good idea.", level_id=b1.level_id),
            Vocabulary(word="argument", definition="Lập luận", example_sentence="He presented a strong argument.", level_id=b2.level_id),
            Vocabulary(word="environment", definition="Môi trường", example_sentence="We need to protect the environment.", level_id=b2.level_id),
            Vocabulary(word="decision", definition="Quyết định", example_sentence="She made a wise decision.", level_id=b2.level_id),
            Vocabulary(word="ethical", definition="Thuộc về đạo đức", example_sentence="There are ethical concerns about this issue.", level_id=c1.level_id),
            Vocabulary(word="impact", definition="Tác động", example_sentence="Social media has a big impact on our lives.", level_id=c1.level_id),
            Vocabulary(word="analyze", definition="Phân tích", example_sentence="We need to analyze the data carefully.", level_id=c1.level_id)
        ]
        db.session.add_all(vocab)
        db.session.commit()

    if not Test.query.first():
        levels = Level.query.all()
        for level in levels:
            speech_test = Test(
                test_type='speech',
                level_id=level.level_id,
                description=f'Speech Test for {level.level_name}'
            )
            db.session.add(speech_test)
            db.session.commit()

            sample_sentences = []
            if level.level_name == 'A1':
                sample_sentences = [
                    ("Hello, my name is John.", "correct_audios/a1_sentence1.wav"),
                    ("I am from Vietnam.", "correct_audios/a1_sentence2.wav"),
                    ("Good morning!", "correct_audios/a1_sentence3.wav")
                ]
            elif level.level_name == 'A2':
                sample_sentences = [
                    ("The cat is small and cute.", "correct_audios/a2_sentence1.wav"),
                    ("He is tall and handsome.", "correct_audios/a2_sentence2.wav"),
                    ("Where is the nearest bus stop?", "correct_audios/a2_sentence3.wav")
                ]
            elif level.level_name == 'B1':
                sample_sentences = [
                    ("I enjoy playing football.", "correct_audios/b1_sentence1.wav"),
                    ("She has visited Paris.", "correct_audios/b1_sentence2.wav"),
                    ("In my opinion, this is a good idea.", "correct_audios/b1_sentence3.wav")
                ]
            elif level.level_name == 'B2':
                sample_sentences = [
                    ("Technology is beneficial.", "correct_audios/b2_sentence1.wav"),
                    ("She is going to study abroad.", "correct_audios/b2_sentence2.wav"),
                    ("My hometown is surrounded by mountains.", "correct_audios/b2_sentence3.wav")
                ]
            elif level.level_name == 'C1':
                sample_sentences = [
                    ("Social media impacts mental health.", "correct_audios/c1_sentence1.wav"),
                    ("What are the ethical implications?", "correct_audios/c1_sentence2.wav"),
                    ("We need to analyze the data carefully.", "correct_audios/c1_sentence3.wav")
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
    with app.app_context():
        db.create_all()
        init_sample_data()

    # Chạy với eventlet
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)