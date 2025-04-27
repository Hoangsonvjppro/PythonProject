import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, redirect, url_for, request, flash, abort, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps
from flask_cors import CORS
from flask_socketio import SocketIO, send
from models.models import db, User, Level, Lesson, UserProgress, Vocabulary, Test, SampleSentence, SpeechTest, Content
from modules.speech import speech_bp
from modules.translate import translate_bp
from modules.chat import chatting, register_socketio_events
from modules.tutorials import tutorials_bp
import os
import json
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
            if not user.is_active:
                flash("Tài khoản của bạn đã bị khóa. Vui lòng liên hệ quản trị viên.", "danger")
                return redirect(url_for('settings'))
                
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

# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    total_users = len(users)
    lessons = Lesson.query.count()
    return render_template('admin.html', users=users, total_users=total_users, 
                           lessons=lessons, current_user=current_user)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users, current_user=current_user)

@app.route('/admin/users/toggle-status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent admins from deactivating their own account
    if user.user_id == current_user.user_id:
        flash("Không thể khóa tài khoản của chính bạn!", "danger")
        return redirect(url_for('admin_users'))
    
    # Prevent deactivating other admins
    if user.role == 'admin' and user.user_id != current_user.user_id:
        flash("Không thể khóa tài khoản admin khác!", "danger")
        return redirect(url_for('admin_users'))
    
    # Toggle the status
    new_status = user.toggle_active_status()
    db.session.commit()
    
    status_text = "kích hoạt" if new_status else "khóa"
    flash(f"Tài khoản của {user.username} đã được {status_text}!", "success")
    return redirect(url_for('admin_users'))

@app.route('/admin/content')
@login_required
@admin_required
def admin_content():
    levels = Level.query.order_by(Level.order).all()
    return render_template('admin_content.html', levels=levels, current_user=current_user)

@app.route('/admin/content/add/<content_type>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_content(content_type):
    if request.method == 'POST':
        if content_type == 'lesson':
            # Create a new lesson
            title = request.form.get('title')
            description = request.form.get('description')
            content_html = request.form.get('content')
            level_id = request.form.get('level_id')
            order = request.form.get('order', 0)
            
            # Validate required fields
            if not all([title, description, content_html, level_id]):
                flash("Tất cả các trường bắt buộc phải được điền đầy đủ.", "danger")
                levels = Level.query.all()
                return render_template('add_content.html', content_type=content_type, 
                                      levels=levels, current_user=current_user)
            
            # Create the lesson
            lesson = Lesson(
                title=title,
                description=description,
                content=content_html,
                level_id=level_id,
                order=order
            )
            db.session.add(lesson)
            db.session.commit()
            
            # Create corresponding Content entry
            level = Level.query.get(level_id)
            content_record = Content(
                title=title,
                content_type="lesson",
                html_content=content_html,
                related_id=lesson.lesson_id,
                content_metadata=json.dumps({"level": level.level_name})
            )
            db.session.add(content_record)
            db.session.commit()
            
            flash(f"Bài học '{title}' đã được tạo thành công!", "success")
            return redirect(url_for('admin_content'))
            
        elif content_type == 'level':
            # Create a new level
            level_name = request.form.get('level_name')
            description = request.form.get('description')
            icon = request.form.get('icon')
            order = request.form.get('order', 0)
            
            # Validate required fields
            if not all([level_name, description]):
                flash("Tất cả các trường bắt buộc phải được điền đầy đủ.", "danger")
                return render_template('add_content.html', content_type=content_type, current_user=current_user)
            
            # Check if level already exists
            if Level.query.filter_by(level_name=level_name).first():
                flash(f"Cấp độ '{level_name}' đã tồn tại!", "danger")
                return render_template('add_content.html', content_type=content_type, current_user=current_user)
            
            # Create the level
            level = Level(
                level_name=level_name,
                description=description,
                icon=icon or "graduation-cap",
                order=order
            )
            db.session.add(level)
            db.session.commit()
            
            flash(f"Cấp độ '{level_name}' đã được tạo thành công!", "success")
            return redirect(url_for('admin_content'))
        
    # GET request - show the form
    levels = Level.query.all()
    return render_template('add_content.html', content_type=content_type,
                          levels=levels, current_user=current_user)

@app.route('/admin/content/edit/<content_type>/<int:content_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_content(content_type, content_id):
    if content_type == 'lesson':
        content = Lesson.query.get_or_404(content_id)
    elif content_type == 'level':
        content = Level.query.get_or_404(content_id)
    else:
        abort(404)
        
    if request.method == 'POST':
        if content_type == 'lesson':
            content.title = request.form.get('title')
            content.description = request.form.get('description')
            content.content = request.form.get('content')
            content.order = request.form.get('order', 0)
            
            # Update the corresponding Content entry if it exists
            content_record = Content.query.filter_by(
                content_type="lesson", 
                related_id=content.lesson_id
            ).first()
            
            if content_record:
                content_record.title = content.title
                content_record.html_content = content.content
                
        elif content_type == 'level':
            content.level_name = request.form.get('level_name')
            content.description = request.form.get('description')
            content.icon = request.form.get('icon')
            content.order = request.form.get('order', 0)
            
        db.session.commit()
        flash(f"{content_type.capitalize()} đã được cập nhật thành công!", "success")
        return redirect(url_for('admin_content'))
        
    return render_template('edit_content.html', content=content, 
                           content_type=content_type, current_user=current_user)

@app.route('/admin/content/delete/<content_type>/<int:content_id>', methods=['POST'])
@login_required
@admin_required
def delete_content(content_type, content_id):
    if content_type == 'lesson':
        content = Lesson.query.get_or_404(content_id)
        
        # Delete related Content entry if it exists
        content_record = Content.query.filter_by(
            content_type="lesson", 
            related_id=content.lesson_id
        ).first()
        
        if content_record:
            db.session.delete(content_record)
            
        # Delete any UserProgress related to this lesson
        UserProgress.query.filter_by(lesson_id=content_id).delete()
        
        db.session.delete(content)
        flash("Bài học đã được xóa thành công!", "success")
        
    elif content_type == 'level':
        level = Level.query.get_or_404(content_id)
        
        # Check if the level has any lessons
        if level.lessons:
            flash("Không thể xóa cấp độ này vì nó có các bài học. Hãy xóa tất cả các bài học trước.", "danger")
            return redirect(url_for('admin_content'))
            
        # Delete vocabularies associated with this level
        Vocabulary.query.filter_by(level_id=content_id).delete()
        
        # Delete tests associated with this level
        tests = Test.query.filter_by(level_id=content_id).all()
        for test in tests:
            # Delete sample sentences associated with each test
            SampleSentence.query.filter_by(test_id=test.test_id).delete()
            db.session.delete(test)
            
        db.session.delete(level)
        flash("Cấp độ đã được xóa thành công!", "success")
    
    else:
        abort(404)
        
    db.session.commit()
    return redirect(url_for('admin_content'))

@app.route('/admin/stats')
@login_required
@admin_required
def admin_stats():
    # Get user statistics
    total_users = User.query.count()
    active_users = UserProgress.query.distinct(UserProgress.user_id).count()
    
    # Get lesson completion statistics
    lessons = Lesson.query.all()
    lesson_stats = []
    
    for lesson in lessons:
        completions = UserProgress.query.filter_by(
            lesson_id=lesson.lesson_id,
            completion_status=True
        ).count()
        
        lesson_stats.append({
            'lesson': lesson,
            'completions': completions,
            'completion_rate': round(completions / total_users * 100, 2) if total_users > 0 else 0
        })
        
    return render_template('admin_stats.html', 
                           total_users=total_users, 
                           active_users=active_users,
                           lesson_stats=lesson_stats,
                           current_user=current_user)

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
    """Initialize sample data for development purposes.
    
    This function creates initial data for the application including:
    - Standard CEFR levels (A1-C1)
    - Sample lessons for each level
    - Sample vocabulary
    - Speech test samples
    
    This function should only run during initial setup or in development.
    In production, content should be managed through the admin interface.
    """
    # Check if we have content in the database already
    if Content.query.first():
        return
        
    # Create levels if needed
    if not Level.query.first():
        print("Initializing CEFR Levels...")
        levels = [
            Level(level_name='A1', description="Beginner - Basic phrases and expressions", icon="graduation-cap", order=1),
            Level(level_name='A2', description="Elementary - Simple communication on familiar topics", icon="book-open", order=2),
            Level(level_name='B1', description="Intermediate - Understanding main points", icon="comments", order=3),
            Level(level_name='B2', description="Upper Intermediate - Effective communication", icon="pen", order=4),
            Level(level_name='C1', description="Advanced - Fluent expression in complex contexts", icon="certificate", order=5)
        ]
        db.session.add_all(levels)
        db.session.commit()

    # Initialize lessons from Content table
    if not Lesson.query.first():
        print("Initializing sample lessons...")
        
        # Get level references
        a1 = Level.query.filter_by(level_name='A1').first()
        a2 = Level.query.filter_by(level_name='A2').first()
        b1 = Level.query.filter_by(level_name='B1').first()
        b2 = Level.query.filter_by(level_name='B2').first()
        c1 = Level.query.filter_by(level_name='C1').first()
        
        # Sample lesson content - this can be moved to JSON files or database seeds
        lesson_data = [
            {
                "level": a1,
                "title": "Giới thiệu bản thân",
                "description": "Học cách giới thiệu tên, tuổi, và quốc tịch.",
                "content": "<h3>Introducing Yourself</h3><p>In this lesson, you'll learn to introduce yourself in English.</p><div class='example'><p>Hello, my name is John. I am 25 years old. I am from Vietnam.</p></div>",
                "order": 1
            },
            {
                "level": a1,
                "title": "Từ vựng cơ bản", 
                "description": "Học các từ vựng cơ bản như màu sắc, số đếm, và ngày trong tuần.",
                "content": "<h3>Basic Vocabulary</h3><p>Learn essential vocabulary for everyday conversation.</p><div class='vocab-list'><ul><li><strong>red</strong> (đỏ)</li><li><strong>blue</strong> (xanh)</li><li><strong>one</strong> (một)</li><li><strong>two</strong> (hai)</li></ul></div>",
                "order": 2
            }
        ]
        
        # Create lessons and associated content
        for data in lesson_data:
            # Create the lesson
            lesson = Lesson(
                level_id=data["level"].level_id,
                title=data["title"],
                description=data["description"],
                content=data["content"],
                order=data["order"]
            )
            db.session.add(lesson)
            db.session.commit()
            
            # Create associated content record
            content = Content(
                title=data["title"],
                content_type="lesson",
                html_content=data["content"],
                related_id=lesson.lesson_id,
                content_metadata=json.dumps({"level": data["level"].level_name})
            )
            db.session.add(content)
            
        db.session.commit()
        print("Sample lessons initialized successfully")

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

import sys
import click
from flask.cli import with_appcontext

@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin_command(username, email, password):
    """Create a new admin user."""
    if User.query.filter_by(username=username).first():
        click.echo(f"Error: Username {username} already exists.")
        return
    if User.query.filter_by(email=email).first():
        click.echo(f"Error: Email {email} already exists.")
        return
    
    user = User.create_admin(username, email, password)
    db.session.add(user)
    db.session.commit()
    click.echo(f"Admin user {username} created successfully.")

app.cli.add_command(create_admin_command)

from commands import register_commands

# Register CLI commands
register_commands(app)

if __name__ == '__main__':
    with app.app_context():
        # Check if database needs to be recreated
        recreate_db = False
        
        if len(sys.argv) > 1 and sys.argv[1] == 'recreate-db':
            recreate_db = True
            print("Recreating database...")
        
        # Try to access the database to check if it has the correct schema
        try:
            # Test if we can access the Level model with all columns
            if not recreate_db:
                test_level = Level.query.first()
                if test_level:
                    # Try to access the new columns to see if they exist
                    test_desc = test_level.description
                    test_icon = test_level.icon
                    test_order = test_level.order
                    print("Database schema is valid.")
        except Exception as e:
            print(f"Database schema issue detected: {e}")
            recreate_db = True
            
        # Recreate database if needed
        if recreate_db:
            # Drop all tables and recreate
            db.drop_all()
            db.create_all()
            print("Database has been recreated with the correct schema.")
            # Initialize with sample data after recreation
            init_sample_data()
        elif len(sys.argv) > 1 and sys.argv[1] == 'create-admin':
            if len(sys.argv) != 5:
                print("Usage: python app.py create-admin <username> <email> <password>")
                sys.exit(1)
            username = sys.argv[2]
            email = sys.argv[3]
            password = sys.argv[4]
            user = User.create_admin(username, email, password)
            db.session.add(user)
            db.session.commit()
            print(f"Admin user {username} created successfully.")
            sys.exit(0)
        else:
            # Only initialize sample data if no command was specified and it's a fresh database
            if not Level.query.first():
                init_sample_data()

    # Chạy với eventlet
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)