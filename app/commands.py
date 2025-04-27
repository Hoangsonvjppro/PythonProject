import click
from flask.cli import with_appcontext
from flask import current_app
from datetime import datetime

from app.extensions import db
from app.models.user import User
from app.models.learning import Level, Lesson, PronunciationExercise

@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin_command(username, email, password):
    """Create a new admin user.
    
    Example:
        flask create-admin admin admin@example.com password123
    """
    try:
        if User.query.filter_by(username=username).first():
            click.echo(f"Lỗi: Tên người dùng {username} đã tồn tại.")
            return
        if User.query.filter_by(email=email).first():
            click.echo(f"Lỗi: Email {email} đã tồn tại.")
            return
        
        user = User(username=username, email=email, role='admin')
        user.set_password(password)
        user.created_at = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        click.echo(f"Đã tạo tài khoản admin {username} thành công.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Lỗi khi tạo tài khoản admin: {str(e)}")

@click.command('list-users')
@with_appcontext
def list_users_command():
    """List all users in the system."""
    try:
        users = User.query.all()
        if not users:
            click.echo("Không tìm thấy người dùng nào.")
            return
            
        click.echo("\nDanh sách người dùng:")
        click.echo("=" * 80)
        click.echo(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Created'}")
        click.echo("-" * 80)
        
        for user in users:
            created = user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else "N/A"
            click.echo(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} {created}")
            
    except Exception as e:
        click.echo(f"Lỗi khi liệt kê người dùng: {str(e)}")

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database with required tables."""
    try:
        db.create_all()
        click.echo("Đã tạo cấu trúc cơ sở dữ liệu thành công.")
    except Exception as e:
        click.echo(f"Lỗi khi tạo cơ sở dữ liệu: {str(e)}")

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Initialize sample data for the application."""
    try:
        # Tạo người dùng admin mẫu nếu chưa tồn tại
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            admin.created_at = datetime.utcnow()
            db.session.add(admin)
            db.session.commit()
            click.echo("Đã tạo tài khoản admin mẫu.")
        
        # Tạo cấp độ học tập mẫu
        if Level.query.count() == 0:
            levels = [
                {'name': 'A1', 'description': 'Sơ cấp - Beginner', 'order': 1, 'icon': 'star'},
                {'name': 'A2', 'description': 'Tiền trung cấp - Elementary', 'order': 2, 'icon': 'star-half-alt'},
                {'name': 'B1', 'description': 'Trung cấp - Intermediate', 'order': 3, 'icon': 'star'}
            ]
            
            for level_data in levels:
                level = Level(
                    name=level_data['name'],
                    description=level_data['description'],
                    order=level_data['order'],
                    icon=level_data['icon'],
                    created_by=admin.id
                )
                db.session.add(level)
            
            db.session.commit()
            click.echo("Đã tạo cấp độ học tập mẫu.")
        
        # Tạo bài học mẫu
        if Lesson.query.count() == 0:
            level_a1 = Level.query.filter_by(name='A1').first()
            if level_a1:
                lessons = [
                    {
                        'title': 'Chào hỏi và giới thiệu bản thân',
                        'description': 'Học cách chào hỏi và giới thiệu bản thân bằng tiếng Anh',
                        'content': '<h2>Chào hỏi</h2><p>Hello - Xin chào</p><p>Hi - Chào</p><p>Good morning - Chào buổi sáng</p><p>Good afternoon - Chào buổi chiều</p><p>Good evening - Chào buổi tối</p><h2>Giới thiệu bản thân</h2><p>My name is... - Tên tôi là...</p><p>I am... - Tôi là...</p><p>Nice to meet you - Rất vui được gặp bạn</p>',
                        'order': 1
                    },
                    {
                        'title': 'Số đếm từ 1-100',
                        'description': 'Học đếm số từ 1 đến 100 bằng tiếng Anh',
                        'content': '<h2>Số từ 1-10</h2><p>One - Một</p><p>Two - Hai</p><p>Three - Ba</p><p>Four - Bốn</p><p>Five - Năm</p><p>Six - Sáu</p><p>Seven - Bảy</p><p>Eight - Tám</p><p>Nine - Chín</p><p>Ten - Mười</p><h2>Số từ 11-20</h2><p>Eleven - Mười một</p><p>Twelve - Mười hai</p><p>Thirteen - Mười ba</p>...',
                        'order': 2
                    }
                ]
                
                for lesson_data in lessons:
                    lesson = Lesson(
                        title=lesson_data['title'],
                        description=lesson_data['description'],
                        content=lesson_data['content'],
                        level_id=level_a1.id,
                        order=lesson_data['order'],
                        created_by=admin.id
                    )
                    db.session.add(lesson)
                
                db.session.commit()
                click.echo("Đã tạo bài học mẫu.")
        
        # Tạo bài tập phát âm mẫu
        if PronunciationExercise.query.count() == 0:
            lesson = Lesson.query.filter_by(title='Chào hỏi và giới thiệu bản thân').first()
            if lesson:
                exercises = [
                    "Hello, my name is John.",
                    "Nice to meet you.",
                    "How are you today?",
                    "I am from Vietnam."
                ]
                
                for i, text in enumerate(exercises):
                    exercise = PronunciationExercise(
                        lesson_id=lesson.id,
                        text=text,
                        is_required=True,
                        created_by=admin.id
                    )
                    db.session.add(exercise)
                
                db.session.commit()
                click.echo("Đã tạo bài tập phát âm mẫu.")
        
        click.echo("\nĐã tạo dữ liệu mẫu thành công!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Lỗi khi tạo dữ liệu mẫu: {str(e)}")

def register_commands(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command) 