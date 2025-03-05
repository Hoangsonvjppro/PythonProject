import speech_recognition as sr
from flask import Blueprint, render_template, request, jsonify

# Tạo Blueprint cho module này
speech_bp = Blueprint('speech', __name__)

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Đang lắng nghe...")
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio, language="vi-VN")
            return {"success": True, "text": text}
        except sr.UnknownValueError:
            return {"success": False, "error": "Không thể nhận dạng giọng nói."}
        except sr.RequestError as e:
            return {"success": False, "error": f"Lỗi kết nối: {e}"}

# Route cho trang Speech to Text
@speech_bp.route('/speech_to_text', methods=['GET', 'POST'])
def speech_to_text():
    if request.method == 'POST':
        result = recognize_speech()
        return jsonify(result)
    return render_template('speech_to_text.html')