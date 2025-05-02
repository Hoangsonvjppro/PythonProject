from app import create_app
from app.models.user import User
from app.extensions import db

app = create_app()

with app.app_context():
    username = 'admin'
    email = 'admin@example.com'
    password = '123'
    
    # Kiểm tra nếu user đã tồn tại
    if User.query.filter_by(username=username).first():
        print(f"User {username} đã tồn tại")
    elif User.query.filter_by(email=email).first():
        print(f"Email {email} đã tồn tại")
    else:
        # Tạo tài khoản admin
        user = User.create_admin(username, email, password)
        db.session.add(user)
        db.session.commit()
        print(f"Tài khoản admin {username} đã được tạo thành công!") 