from flask import Blueprint, render_template
from flask_socketio import emit
from flask_login import current_user
import logging
from flask import Blueprint, render_template
from flask_socketio import emit
from flask_login import current_user
import google.generativeai as genai
import logging
# Tạo Blueprint
chatting = Blueprint('chatting', __name__)

@chatting.route('/chat')
def chat_page():
    return render_template('chatting.html')

# Cấu hình log
logging.basicConfig(level=logging.DEBUG)

# Cấu hình API Key OpenAI
genai.configure(api_key="AIzaSyD_KgoexvUqVcEuEp9m5ZfKbE_eS4YWxPU")  
model = genai.GenerativeModel("gemini-1.5-pro") 

def get_ai_response(user_message):
    try:
        response = model.generate_content(user_message)
        return response.text  # Lấy nội dung phản hồi từ Gemini
    except Exception as e:
        return f"❌ Lỗi API Gemini: {str(e)}"

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
