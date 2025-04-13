from flask import Blueprint, render_template
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from models.models import db

chatting = Blueprint('chatting', __name__)

@chatting.route('/chat')
def chat_page():
    return render_template('chatting.html')

def register_socketio_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        print(f'Người dùng đã kết nối: {current_user.username if current_user.is_authenticated else "Guest"}')

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'Người dùng đã rời khỏi: {current_user.username if current_user.is_authenticated else "Guest"}')

    @socketio.on('send_message')
    def handle_send_message(data):
        print(f'Nhận tin nhắn từ {current_user.username if current_user.is_authenticated else "Guest"}: {data["message"]}')
        if current_user.is_authenticated:
            username = current_user.username
            avatar = current_user.avatar
        else:
            username = 'Guest'
            avatar = 'default.jpg'
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

    @socketio.on('update_username')
    def handle_update_username(data):
        new_username = data.get('username', '').strip()
        print(f'Yêu cầu đổi tên từ {current_user.username if current_user.is_authenticated else "Guest"} thành {new_username}')
        if not new_username:
            return
        if current_user.is_authenticated:
            old_username = current_user.username
            if new_username != old_username:
                current_user.username = new_username
                db.session.commit()
                emit('set_username', {'old_username': old_username, 'new_username': new_username}, broadcast=True)
        else:
            emit('error', {'message': 'Guests cannot change username'})