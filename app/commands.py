import click
from flask.cli import with_appcontext
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
    """Tạo tài khoản admin mới.
    
    Ví dụ:
        flask create-admin admin admin@example.com password123
    """
    try:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            click.echo(f"Lỗi: Tên người dùng {username} đã tồn tại.")
            return
        
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            click.echo(f"Lỗi: Email {email} đã tồn tại.")
            return
        
        user = User.create_admin(username, email, password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Đã tạo tài khoản admin {username} thành công.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Lỗi khi tạo tài khoản admin: {str(e)}")

@click.command('list-users')
@with_appcontext
def list_users_command():
    """Liệt kê tất cả người dùng trong hệ thống."""
    try:
        users = User.query.all()
        if not users:
            click.echo("Không tìm thấy người dùng nào.")
            return
            
        click.echo("\nDanh sách người dùng:")
        click.echo("=" * 80)
        click.echo(f"{'ID':<5} {'Tên đăng nhập':<20} {'Email':<30} {'Vai trò':<10} {'Đăng ký'}")
        click.echo("-" * 80)
        
        for user in users:
            created = user.created_at.strftime('%Y-%m-%d %H:%M') if user.created_at else "N/A"
            click.echo(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10} {created}")
            
    except Exception as e:
        click.echo(f"Lỗi liệt kê người dùng: {str(e)}")

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Khởi tạo cơ sở dữ liệu với các bảng cần thiết."""
    try:
        db.create_all()
        click.echo("Đã tạo bảng cơ sở dữ liệu thành công.")
    except Exception as e:
        click.echo(f"Lỗi tạo bảng cơ sở dữ liệu: {str(e)}")

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Tạo dữ liệu mẫu cho cơ sở dữ liệu."""
    try:
        # Tạo admin nếu chưa có
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            click.echo("Đã tạo tài khoản admin mặc định.")
        
        # Tạo cấp độ mẫu nếu chưa có
        if Level.query.count() == 0:
            levels = [
                {'name': 'A1', 'description': 'Beginner', 'icon': 'baby', 'order': 1},
                {'name': 'A2', 'description': 'Elementary', 'icon': 'child', 'order': 2},
                {'name': 'B1', 'description': 'Intermediate', 'icon': 'user', 'order': 3},
                {'name': 'B2', 'description': 'Upper Intermediate', 'icon': 'user-graduate', 'order': 4}
            ]
            
            for level_data in levels:
                level = Level(
                    name=level_data['name'],
                    description=level_data['description'],
                    icon=level_data['icon'],
                    order=level_data['order'],
                    active=True,
                    created_by=admin.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(level)
            
            db.session.commit()
            click.echo("Đã tạo các cấp độ mẫu.")
        
        # Tạo bài học mẫu nếu chưa có
        if Lesson.query.count() == 0:
            # Lấy cấp độ A1
            level_a1 = Level.query.filter_by(name='A1').first()
            
            if level_a1:
                lessons = [
                    {
                        'title': 'Greeting and Introduction',
                        'description': 'Learn how to greet people and introduce yourself',
                        'content': '''
                        <h2>Greeting and Introduction</h2>
                        <p>In this lesson, you will learn how to greet people and introduce yourself in English.</p>
                        
                        <h3>Common Greetings</h3>
                        <ul>
                            <li><strong>Hello</strong> - A universal greeting that works in any situation</li>
                            <li><strong>Hi</strong> - An informal greeting for friends and acquaintances</li>
                            <li><strong>Good morning</strong> - Used from sunrise until noon</li>
                            <li><strong>Good afternoon</strong> - Used from noon until around 5pm</li>
                            <li><strong>Good evening</strong> - Used from around 5pm until bedtime</li>
                        </ul>
                        
                        <h3>Introducing Yourself</h3>
                        <p>To introduce yourself, you can use these phrases:</p>
                        <ul>
                            <li><strong>My name is...</strong></li>
                            <li><strong>I'm...</strong></li>
                            <li><strong>Nice to meet you</strong> - Say this after someone introduces themselves to you</li>
                        </ul>
                        
                        <h3>Example Conversations</h3>
                        <p><strong>Conversation 1:</strong></p>
                        <p>
                        A: Hello!<br>
                        B: Hi there!<br>
                        A: My name is John.<br>
                        B: Nice to meet you, John. I'm Sarah.<br>
                        A: Nice to meet you too, Sarah.
                        </p>
                        
                        <p><strong>Conversation 2:</strong></p>
                        <p>
                        A: Good morning!<br>
                        B: Good morning! How are you?<br>
                        A: I'm fine, thank you. And you?<br>
                        B: I'm good, thanks. I'm David.<br>
                        A: I'm Emma. Nice to meet you, David.<br>
                        B: Nice to meet you too, Emma.
                        </p>
                        ''',
                        'order': 1
                    },
                    {
                        'title': 'Numbers and Counting',
                        'description': 'Learn how to count and use numbers in English',
                        'content': '''
                        <h2>Numbers and Counting</h2>
                        <p>In this lesson, you will learn about numbers and how to count in English.</p>
                        
                        <h3>Cardinal Numbers (1-20)</h3>
                        <ul>
                            <li>1 - one</li>
                            <li>2 - two</li>
                            <li>3 - three</li>
                            <li>4 - four</li>
                            <li>5 - five</li>
                            <li>6 - six</li>
                            <li>7 - seven</li>
                            <li>8 - eight</li>
                            <li>9 - nine</li>
                            <li>10 - ten</li>
                            <li>11 - eleven</li>
                            <li>12 - twelve</li>
                            <li>13 - thirteen</li>
                            <li>14 - fourteen</li>
                            <li>15 - fifteen</li>
                            <li>16 - sixteen</li>
                            <li>17 - seventeen</li>
                            <li>18 - eighteen</li>
                            <li>19 - nineteen</li>
                            <li>20 - twenty</li>
                        </ul>
                        
                        <h3>Tens (10-100)</h3>
                        <ul>
                            <li>10 - ten</li>
                            <li>20 - twenty</li>
                            <li>30 - thirty</li>
                            <li>40 - forty</li>
                            <li>50 - fifty</li>
                            <li>60 - sixty</li>
                            <li>70 - seventy</li>
                            <li>80 - eighty</li>
                            <li>90 - ninety</li>
                            <li>100 - one hundred</li>
                        </ul>
                        
                        <h3>Using Numbers in Conversation</h3>
                        <p>Here are some common ways to use numbers:</p>
                        <ul>
                            <li>Telling time: "It's nine o'clock." "It's half past ten."</li>
                            <li>Prices: "This book costs fifteen dollars."</li>
                            <li>Age: "I'm twenty-five years old."</li>
                            <li>Phone numbers: "My phone number is 555-123-4567."</li>
                        </ul>
                        ''',
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
                        active=True,
                        created_by=admin.id,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(lesson)
                
                db.session.commit()
                
                # Thêm bài tập phát âm cho bài học đầu tiên
                first_lesson = Lesson.query.filter_by(level_id=level_a1.id, order=1).first()
                if first_lesson:
                    exercises = [
                        {
                            'text': 'Hello, my name is John. Nice to meet you.',
                            'is_required': True
                        },
                        {
                            'text': 'Good morning! How are you today?',
                            'is_required': True
                        },
                        {
                            'text': 'I am from Vietnam. I am learning English.',
                            'is_required': False
                        }
                    ]
                    
                    for exercise_data in exercises:
                        exercise = PronunciationExercise(
                            lesson_id=first_lesson.id,
                            text=exercise_data['text'],
                            is_required=exercise_data['is_required'],
                            created_by=admin.id,
                            created_at=datetime.utcnow()
                        )
                        db.session.add(exercise)
                    
                    db.session.commit()
                
                click.echo("Đã tạo các bài học và bài tập phát âm mẫu.")
            
        click.echo("Đã tạo dữ liệu mẫu thành công.")
        
    except Exception as e:
        db.session.rollback()
        click.echo(f"Lỗi tạo dữ liệu mẫu: {str(e)}")

def register_commands(app):
    """Đăng ký các lệnh CLI với ứng dụng Flask."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command) 