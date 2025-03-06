from flask import Blueprint, render_template
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user  # Thêm import này

# Tạo Blueprint cho chat
chatting = Blueprint('chatting', __name__)

@chatting.route('/chat')
def chat_page():
    return render_template('chatting.html')

# Đăng ký sự kiện SocketIO
def register_socketio_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        print('Người dùng đã kết nối')

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Người dùng đã rời khỏi')

    @socketio.on('send_message')
    def handle_send_message(data):
        if current_user.is_authenticated:
            username = current_user.username
            avatar = current_user.avatar
        else:
            username = 'Guest'
            avatar = 'static/img/male.svg'  # Đảm bảo có file default.jpg trong thư mục static/uploads
        message = data.get('message', '')
        emit('new_message', {'username': username, 'message': message, 'avatar': avatar}, broadcast=True)

    @socketio.on('join_room')
    def handle_join_room(data):
        room = data.get('room', 'default')
        username = data.get('username', 'Ẩn danh')
        join_room(room)
        emit('user_joined', {'username': username}, room=room)

    @socketio.on('leave_room')
    def handle_leave_room(data):
        room = data.get('room', 'default')
        username = data.get('username', 'Ẩn danh')
        leave_room(room)
        emit('user_left', {'username': username}, room=room)