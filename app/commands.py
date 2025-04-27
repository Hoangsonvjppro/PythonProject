import click
from flask.cli import with_appcontext
from flask import current_app
from datetime import datetime

from app.extensions import db
from app.models.models import User, Level, Lesson, UserProgress, Vocabulary, Test, SampleSentence, SpeechTest

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
        click.echo(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10}")
        click.echo("-" * 80)
        
        for user in users:
            click.echo(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10}")
            
    except Exception as e:
        click.echo(f"Lỗi khi liệt kê người dùng: {str(e)}")

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database with sample data."""
    try:
        # Tạo người dùng admin mẫu nếu chưa tồn tại
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            click.echo("Đã tạo tài khoản admin mẫu.")
            
        # Tạo dữ liệu mẫu
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
            click.echo("Đã tạo cấp độ mẫu.")

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
            click.echo("Đã tạo bài học mẫu.")

        if not Vocabulary.query.first():
            a1 = Level.query.filter_by(level_name='A1').first()
            a2 = Level.query.filter_by(level_name='A2').first()
            b1 = Level.query.filter_by(level_name='B1').first()
            b2 = Level.query.filter_by(level_name='B2').first()
            c1 = Level.query.filter_by(level_name='C1').first()
            
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
            click.echo("Đã tạo từ vựng mẫu.")

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
            click.echo("Đã tạo bài kiểm tra mẫu.")
        
        click.echo("Đã khởi tạo cơ sở dữ liệu với dữ liệu mẫu thành công!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Lỗi khi khởi tạo cơ sở dữ liệu: {str(e)}")

def register_commands(app):
    """Register CLI commands with the Flask application."""
    app.cli.add_command(create_admin_command)
    app.cli.add_command(list_users_command)
    app.cli.add_command(init_db_command) 