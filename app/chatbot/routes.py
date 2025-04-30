from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
from flask_login import current_user
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer, util
from datetime import datetime
import os
from app.chatbot import bp
from app.extensions import socketio, socketio_available

@bp.route('/chatbot')
def chatbot():
    """Hiển thị trang chatbot"""
    return render_template('chatbot/chatbot.html', socketio_available=socketio_available)

user_modes = {}
current_question = {}

# Try to connect to the database in the instance folder
try:
    db_path = os.path.join("instance", "chatbot_data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT question, answer, embedding FROM chatbot_data")
    rows = cursor.fetchall()

    questions = []
    answers = []
    embeddings = []

    for row in rows:
        questions.append(row[0])
        answers.append(row[1])
        embeddings.append(np.frombuffer(row[2], dtype=np.float32))

    conn.close()
    print(f"[{datetime.now()}] Successfully loaded chatbot data from the database.")
except Exception as e:
    print(f"[{datetime.now()}] Error loading chatbot data: {str(e)}")
    questions = []
    answers = []
    embeddings = []

# Load model
try:
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    print(f"[{datetime.now()}] SentenceTransformer model loaded successfully.")
except Exception as e:
    print(f"[{datetime.now()}] Error loading SentenceTransformer: {str(e)}")
    model = None


def get_bot_response(user_input, threshold=0.6):
    """Generate bot response."""
    if model is None:
        return "Lỗi: Không thể tải mô hình AI. Vui lòng liên hệ quản trị viên."
    
    if not embeddings:
        return "Cơ sở dữ liệu chatbot chưa được khởi tạo. Vui lòng chạy script khởi tạo dữ liệu."
    
    try:
        user_embedding = model.encode(user_input, convert_to_tensor=True).numpy()
        emb_array = np.array(embeddings)

        cosine_scores = np.dot(emb_array, user_embedding) / (
            np.linalg.norm(emb_array, axis=1) * np.linalg.norm(user_embedding)
        )
        best_score = np.max(cosine_scores)
        best_idx = np.argmax(cosine_scores)

        if best_score >= threshold:
            return answers[best_idx]
        else:
            return "Xin lỗi, tôi chưa hiểu rõ. Nếu muốn dạy cho chat bot hãy gõ theo cú pháp 'Training: câu hỏi => câu trả lời'"
    except Exception as e:
        print(f"[{datetime.now()}] Error in get_bot_response: {str(e)}")
        return f"Đã xảy ra lỗi: {str(e)}"

def register_chatbot_events():
    if not socketio_available:
        print("WARNING: SocketIO not available, chatbot events not registered")
        return
    
    @socketio.on('message')
    def handle_message(data):
        # Xử lý tin nhắn
        pass
    
    @socketio.on('connect')
    def test_connect():
        # Xử lý kết nối
        pass
    
    # Các sự kiện khác

# API cho chatbot khi không có SocketIO
@bp.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    """API endpoint để tương tác với chatbot qua HTTP khi không có SocketIO"""
    if not request.is_json:
        return jsonify({"success": False, "error": "Yêu cầu phải ở định dạng JSON"}), 400
    
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({"success": False, "error": "Tin nhắn không được để trống"}), 400
    
    # Sử dụng cùng logic xử lý tin nhắn như trong SocketIO
    try:
        if message.lower().startswith("training:"):
            return jsonify({
                "success": True,
                "response": "Chế độ HTTP không hỗ trợ chức năng training. Vui lòng sử dụng SocketIO."
            })
        
        # Xử lý tin nhắn bình thường
        response = get_bot_response(message)
        return jsonify({
            "success": True,
            "response": response
        })
    except Exception as e:
        print(f"[{datetime.now()}] Error in API chatbot: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Đã xảy ra lỗi: {str(e)}"
        })

# Các route khác 