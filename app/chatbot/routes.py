from flask import Blueprint, render_template, request
from flask_socketio import emit
from flask_login import current_user
import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer, util
from datetime import datetime
import os
from . import chatbot_bp


@chatbot_bp.route('/', methods=['GET', 'POST'])
def chatbot():
    return render_template('chatbot/chatbot.html')

user_modes = {}
current_question = {}

conn = sqlite3.connect(os.path.join(os.getcwd(), "instance", "chatbot_data.db"))
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

# Load model
try:
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    print(f"[{datetime.now()}] SentenceTransformer model loaded successfully.")
except Exception as e:
    print(f"[{datetime.now()}] Error loading SentenceTransformer: {str(e)}")
    model = None

def get_bot_response(user_input, threshold=0.6):
    if model is None:
        return "Lỗi: Không thể tải mô hình AI. Vui lòng liên hệ quản trị viên."
    try:
        user_embedding = model.encode(user_input, convert_to_tensor=True).numpy()
        emb_array = np.array(embeddings)

        cosine_scores = np.dot(emb_array, user_embedding) / (
            np.linalg.norm(emb_array, axis=1) * np.linalg.norm(user_embedding)
        )
        best_score = np.max(cosine_scores)
        best_idx = np.argmax(cosine_scores)
        print(f"[{datetime.now()}] Best score: {best_score}, Best index: {best_idx}")
        if best_score >= threshold:
            return answers[best_idx]
        elif best_score >= 0.4:
            return answers[best_idx] + " (Tôi không chắc chắn về câu trả lời này.)"
        else:
            return "Xin lỗi, tôi chưa hiểu rõ. Nếu muốn dạy cho chat bot hãy gõ theo cú pháp 'Training: câu hỏi => câu trả lời'"
    except Exception as e:
        print(f"[{datetime.now()}] Error in get_bot_response: {str(e)}")
        return f"Đã xảy ra lỗi: {str(e)}"

def register_socketio_events(socketio):
    @socketio.on('connect')
    def handle_connect():
        print(f"[{datetime.now()}] Người dùng đã kết nối!")
        if model is None:
            emit("new_message_chatbot", {"message": "Lỗi: Chatbot không khả dụng vì mô hình AI chưa sẵn sàng."})
        else:
            emit("new_message_chatbot", {"message": "Đã kết nối với chatbot!"})

    @socketio.on('disconnect')
    def handle_disconnect():
        user_id = request.sid
        user_modes.pop(user_id, None)
        current_question.pop(user_id, None)
        print(f"[{datetime.now()}] Người dùng đã ngắt kết nối.")

    @socketio.on("send_message_chatbot")
    def handle_ai_message(data):
        user_id = request.sid
        user_message = data.get("message", "").strip()
        print(f"[{datetime.now()}] Received message: {user_message}")

        if not user_message:
            return

        try:
            # Training mode
            if user_message.lower().startswith("training:"):
                training_text = user_message[9:].strip()

                if "=>" not in training_text:
                    emit("new_message_chatbot", {
                        "message": "Sai cú pháp. Dùng: Training: câu hỏi => câu trả lời"
                    }, room=user_id)
                    return

                parts = training_text.split("=>")
                if len(parts) != 2:
                    emit("new_message_chatbot", {
                        "message": "Sai cú pháp. Hãy dùng đúng 1 dấu =>. Ví dụ: Training: Bạn tên gì? => Tôi là chatbot."
                    }, room=user_id)
                    return

                new_question = parts[0].strip().lower()
                new_answer = parts[1].strip()

                if not new_question or not new_answer:
                    emit("new_message_chatbot", {
                        "message": "Câu hỏi và câu trả lời không được trống."
                    }, room=user_id)
                    return

                if new_question in [q.lower() for q in questions]:
                    emit("new_message_chatbot", {
                        "message": "Câu hỏi này đã tồn tại. Vui lòng nhập câu hỏi khác."
                    }, room=user_id)
                    return

                new_embedding = model.encode(new_question, convert_to_tensor=True).numpy()

                conn = sqlite3.connect(os.path.join(os.getcwd(), "instance", "chatbot_data.db"))
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chatbot_data (question, answer, embedding)
                    VALUES (?, ?, ?)
                """, (new_question, new_answer, new_embedding.tobytes()))
                conn.commit()
                conn.close()

                emit("new_message_chatbot", {
                    "message": "Huấn luyện câu hỏi mới thành công!"
                }, room=user_id)
                print(f"[{datetime.now()}] Trained new question: {new_question}")
                return

            # Regular chat
            response = get_bot_response(user_message)
            emit("new_message_chatbot", {"message": response}, room=user_id)
            print(f"[{datetime.now()}] Sent response: {response}")

        except Exception as e:
            print(f"[{datetime.now()}] Error handling message: {str(e)}")
            emit("new_message_chatbot", {
                "message": f"Đã xảy ra lỗi: {str(e)}"
            }, room=user_id)
