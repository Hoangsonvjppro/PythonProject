import speech_recognition as sr
from flask import Blueprint, render_template, request, jsonify
import difflib  # Để so sánh chuỗi

# Tạo Blueprint cho module này
speech_bp = Blueprint('speech', __name__)

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Đang lắng nghe...")
            audio = recognizer.listen(source, timeout=5)  # Timeout 5 giây
            text = recognizer.recognize_google(audio, language="en-US")  # Chuyển sang tiếng Anh
            return {"success": True, "text": text}
        except sr.UnknownValueError:
            return {"success": False, "error": "Không thể nhận dạng giọng nói."}
        except sr.RequestError as e:
            return {"success": False, "error": f"Lỗi kết nối: {e}"}
        except sr.WaitTimeoutError:
            return {"success": False, "error": "Hết thời gian chờ, hãy thử lại."}

# Danh sách câu mẫu (có thể lưu trong database sau này)
SAMPLE_SENTENCES = [
    "She sells seashells by the seashore",
    "This restaurant serves delicious Vietnamese food",
    "Technology is transforming the way we communicate",
    "She often participates in academic discussions"
]

def evaluate_pronunciation(user_text, sample_text):
    # So sánh chuỗi đơn giản bằng difflib
    similarity = difflib.SequenceMatcher(None, user_text.lower(), sample_text.lower()).ratio()
    accuracy = similarity * 100  # Tính phần trăm chính xác
    if accuracy >= 90:
        feedback = "Excellent pronunciation!"
    elif accuracy >= 70:
        feedback = "Good effort, but could be clearer."
    else:
        feedback = "Needs improvement, try again."
    return {"accuracy": round(accuracy, 2), "feedback": feedback}

# Route cho trang Speech to Text
@speech_bp.route('/speech_to_text', methods=['GET', 'POST'])
def speech_to_text():
    if request.method == 'POST':
        sample_sentence = request.json.get('sample_sentence')  # Nhận câu mẫu từ frontend
        if not sample_sentence:
            return jsonify({"success": False, "error": "No sample sentence provided."}), 400

        result = recognize_speech()
        if result["success"]:
            user_text = result["text"]
            evaluation = evaluate_pronunciation(user_text, sample_sentence)
            result.update(evaluation)  # Thêm kết quả đánh giá vào phản hồi
        return jsonify(result)
    return render_template('speech_to_text.html', sample_sentences=SAMPLE_SENTENCES)

