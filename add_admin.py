import sys
import os

# Thêm đường dẫn hiện tại vào sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.models.user import User
from app.extensions import db

def create_admin_user(username, email, password):
    """Tạo một tài khoản admin mới"""
    app = create_app()
    
    with app.app_context():
        # Kiểm tra xem user đã tồn tại chưa
        if User.query.filter_by(username=username).first():
            print(f"Error: Username {username} đã tồn tại.")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"Error: Email {email} đã tồn tại.")
            return
        
        # Tạo admin user
        try:
            user = User.create_admin(username, email, password)
            db.session.add(user)
            db.session.commit()
            print(f"Admin user {username} đã được tạo thành công!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python add_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(username, email, password) 