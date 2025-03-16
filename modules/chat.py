from flask import Blueprint, render_template
from flask_socketio import emit
from flask_login import current_user
import openai
import logging
import os

# Tạo Blueprint
chatting = Blueprint('chatting', __name__)

@chatting.route('/chat')
def chat_page():
    return render_template('chatting.html')

# Cấu hình log
logging.basicConfig(level=logging.DEBUG)

# Cấu hình API Key (thay bằng API key thật của bạn)
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_ai_response(user_message):
    try:
        logging.debug(f"Đang gửi tin nhắn đến AI: {user_message}")

        client = openai.OpenAI()  # Tạo client mới

        response = client.chat.completions.create(  # Cách gọi API mới
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )

        ai_message = response.choices[0].message.content  # Lấy nội dung phản hồi
        logging.debug(f"🤖 AI phản hồi: {ai_message}")

        return ai_message
    except Exception as e:
        logging.error(f"🚨 Lỗi khi gọi OpenAI API: {e}")
        return "Xin lỗi, tôi không thể phản hồi ngay bây giờ."

# Đăng ký sự kiện SocketIO
def register_socketio_events(socketio):

    @socketio.on('connect')
    def handle_connect():
        print("✅ Người dùng đã kết nối!")

    @socketio.on('disconnect')
    def handle_disconnect():
        print("❌ Người dùng đã rời khỏi!")

    @socketio.on('send_message')
    def handle_send_message(data):
        username = current_user.username if current_user.is_authenticated else 'Guest'
        avatar = current_user.avatar if current_user.is_authenticated else 'default.jpg'
        message = data.get('message', '')

        print(f"📩 Tin nhắn mới từ {username}: {message}")  # Debug

        # Phát tin nhắn đến tất cả client
        emit('new_message', {'username': username, 'message': message, 'avatar': avatar}, broadcast=True)

    @socketio.on('send_message_ai')
    def handle_send_message_ai(data):
        user_message = data.get('message', '')
        ai_response = get_ai_response(user_message)  # Gọi AI xử lý

        print(f"🤖 AI phản hồi: {ai_response}")  # Debug

        emit('new_message_ai', {'message': ai_response})
