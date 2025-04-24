"""
Script để cập nhật cấu trúc bảng chat_rooms và các bảng liên quan
"""
import sqlite3
from app import app

# Kết nối tới database
def update_database():
    conn = sqlite3.connect('../instance/learning_app.db')
    cursor = conn.cursor()
    
    # Kiểm tra xem bảng chat_rooms đã tồn tại chưa
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_rooms'")
    chat_rooms_exists = cursor.fetchone() is not None
    
    try:
        # Nếu bảng chat_rooms đã tồn tại, thêm cột owner_id
        if chat_rooms_exists:
            # Kiểm tra xem cột owner_id đã tồn tại trong bảng chưa
            cursor.execute("PRAGMA table_info(chat_rooms)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            if 'owner_id' not in column_names:
                print("Thêm cột owner_id vào bảng chat_rooms...")
                # Với SQLite không thể trực tiếp ADD COLUMN với constraint FOREIGN KEY
                # Tạo bảng tạm, copy dữ liệu, xóa bảng cũ, đổi tên bảng tạm
                cursor.execute('''
                    CREATE TABLE chat_rooms_new (
                        room_id TEXT PRIMARY KEY, 
                        name TEXT NOT NULL, 
                        description TEXT, 
                        is_private BOOLEAN, 
                        created_at TIMESTAMP, 
                        created_by INTEGER,
                        owner_id INTEGER NOT NULL DEFAULT 1,
                        FOREIGN KEY (owner_id) REFERENCES users(id)
                    )
                ''')
                
                # Copy dữ liệu từ bảng cũ sang bảng mới, với owner_id mặc định = created_by
                cursor.execute('''
                    INSERT INTO chat_rooms_new(room_id, name, description, is_private, created_at, created_by, owner_id)
                    SELECT room_id, name, description, is_private, created_at, created_by, COALESCE(created_by, 1)
                    FROM chat_rooms
                ''')
                
                # Xóa bảng cũ
                cursor.execute('DROP TABLE chat_rooms')
                
                # Đổi tên bảng mới thành tên bảng cũ
                cursor.execute('ALTER TABLE chat_rooms_new RENAME TO chat_rooms')
                
                print("Cập nhật thành công cột owner_id trong bảng chat_rooms")
            else:
                print("Cột owner_id đã tồn tại trong bảng chat_rooms")
        
        # Kiểm tra và tạo các bảng khác nếu chưa tồn tại
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='room_participants'")
        if cursor.fetchone() is None:
            print("Tạo bảng room_participants...")
            cursor.execute('''
                CREATE TABLE room_participants (
                    id INTEGER PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    joined_at TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE (room_id, user_id)
                )
            ''')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if cursor.fetchone() is None:
            print("Tạo bảng messages...")
            cursor.execute('''
                CREATE TABLE messages (
                    message_id INTEGER PRIMARY KEY,
                    room_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP,
                    FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='status_posts'")
        if cursor.fetchone() is None:
            print("Tạo bảng status_posts...")
            cursor.execute('''
                CREATE TABLE status_posts (
                    post_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='post_comments'")
        if cursor.fetchone() is None:
            print("Tạo bảng post_comments...")
            cursor.execute('''
                CREATE TABLE post_comments (
                    comment_id INTEGER PRIMARY KEY,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES status_posts(post_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
        
        # Commit các thay đổi
        conn.commit()
        print("Cập nhật database thành công!")
        
    except Exception as e:
        print(f"Lỗi: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    with app.app_context():
        update_database() 