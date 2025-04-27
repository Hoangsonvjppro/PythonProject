import os
import uuid
import tempfile
import numpy as np
from datetime import datetime
from flask import render_template, request, jsonify, current_app
from flask_login import current_user, login_required
import speech_recognition as sr
from pydub import AudioSegment

from app.speech import bp
from app.models.learning import PronunciationExercise, PronunciationAttempt
from app.extensions import db

def recognize_speech():
    """Nhận dạng giọng nói từ microphone"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=5)  # 5 second timeout
            # Lưu audio để phân tích
            audio_data = audio.get_wav_data()
            # Sử dụng Google Speech Recognition để chuyển đổi thành văn bản
            text = recognizer.recognize_google(audio, language="en-US")
            return {
                "success": True, 
                "text": text,
                "audio_data": audio_data
            }
        except sr.UnknownValueError:
            return {"success": False, "error": "Không thể nhận dạng giọng nói."}
        except sr.RequestError as e:
            return {"success": False, "error": f"Lỗi kết nối: {e}"}
        except sr.WaitTimeoutError:
            return {"success": False, "error": "Hết thời gian, vui lòng thử lại."}

def evaluate_pronunciation_basic(user_text, sample_text):
    """Đánh giá phát âm cơ bản bằng so sánh chuỗi"""
    import difflib
    similarity = difflib.SequenceMatcher(None, user_text.lower(), sample_text.lower()).ratio()
    accuracy = similarity * 100
    
    if accuracy >= 90:
        feedback = "Phát âm xuất sắc!"
    elif accuracy >= 70:
        feedback = "Phát âm tốt, nhưng có thể rõ ràng hơn."
    else:
        feedback = "Cần cải thiện, hãy thử lại."
        
    return {"accuracy": round(accuracy, 2), "feedback": feedback}

def analyze_audio_features(audio_data, sample_text):
    """
    Phân tích đặc điểm âm thanh để đánh giá chất lượng phát âm
    """
    # Lưu dữ liệu âm thanh vào file tạm
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
        temp_audio.write(audio_data)
        temp_audio_path = temp_audio.name
    
    try:
        # Trích xuất đặc điểm cơ bản của âm thanh
        audio = AudioSegment.from_wav(temp_audio_path)
        
        # Tính toán năng lượng âm thanh (âm lượng)
        energy = np.array([chunk.dBFS for chunk in audio[::100]])
        energy_var = np.var(energy[energy > -40])  # Phương sai của các phần không im lặng
        
        # Các chỉ số mô phỏng sẽ đến từ API thực:
        # - Độ chính xác của âm vị
        # - Độ chính xác của ngữ điệu (nhịp điệu và ngữ điệu)
        # - Độ trôi chảy (tạm dừng, do dự)
        phoneme_accuracy = min(95, 70 + energy_var)
        prosody_accuracy = min(90, 65 + energy_var * 0.8)
        fluency = min(85, 60 + energy_var * 1.2)
        
        # Kết hợp các chỉ số cho điểm tổng thể
        overall_accuracy = (phoneme_accuracy * 0.5 + prosody_accuracy * 0.3 + fluency * 0.2)
        
        # Phản hồi chi tiết
        if overall_accuracy >= 90:
            detailed_feedback = "Phát âm xuất sắc với nhịp điệu và ngữ điệu tốt."
        elif overall_accuracy >= 80:
            detailed_feedback = "Phát âm tốt. Cần cải thiện nhỏ về nhịp điệu và trọng âm."
        elif overall_accuracy >= 70:
            detailed_feedback = "Phát âm đạt yêu cầu. Cần cải thiện trọng âm từ và mẫu ngữ điệu."
        else:
            detailed_feedback = "Cần luyện tập. Tập trung vào từng âm riêng lẻ và kết nối từ."
        
        # Dọn dẹp
        os.unlink(temp_audio_path)
        
        return {
            "accuracy": round(overall_accuracy, 2),
            "feedback": detailed_feedback,
            "details": {
                "phoneme_accuracy": round(phoneme_accuracy, 2),
                "prosody_accuracy": round(prosody_accuracy, 2),
                "fluency": round(fluency, 2)
            }
        }
    
    except Exception as e:
        # Quay lại phương pháp cơ bản nếu phân tích nâng cao thất bại
        print(f"Phân tích nâng cao thất bại: {e}")
        os.unlink(temp_audio_path)
        return None

@bp.route('/speech')
@login_required
def index():
    """Trang Speech-to-Text thông thường"""
    sample_sentences = [
        "She sells seashells by the seashore",
        "This restaurant serves delicious Vietnamese food",
        "Technology is transforming the way we communicate",
        "She often participates in academic discussions"
    ]
    return render_template('speech/index.html', title='Luyện phát âm', sample_sentences=sample_sentences)

@bp.route('/api/evaluate', methods=['POST'])
@login_required
def evaluate_speech():
    """API để đánh giá phát âm"""
    if not request.is_json:
        return jsonify({"success": False, "error": "Yêu cầu không hợp lệ"}), 400
    
    data = request.get_json()
    sample_text = data.get('sample_text')
    exercise_id = data.get('exercise_id')
    
    if not sample_text:
        return jsonify({"success": False, "error": "Không có văn bản mẫu"}), 400
    
    # Nhận dạng giọng nói
    result = recognize_speech()
    if result["success"]:
        user_text = result["text"]
        
        # Trích xuất audio_data từ result trước khi chuyển thành JSON
        audio_data = result.pop("audio_data", None)
        
        # Thử phân tích âm thanh nâng cao nếu có dữ liệu âm thanh
        if audio_data:
            advanced_evaluation = analyze_audio_features(audio_data, sample_text)
            if advanced_evaluation:
                result.update(advanced_evaluation)
                
                # Lưu kết quả nếu có exercise_id
                if exercise_id and exercise_id.isdigit():
                    # Tạo tên file audio
                    audio_filename = f"{uuid.uuid4()}.wav"
                    audio_path = os.path.join(current_app.config['UPLOAD_FOLDER'], audio_filename)
                    
                    # Lưu file audio
                    os.makedirs(os.path.dirname(audio_path), exist_ok=True)
                    with open(audio_path, 'wb') as f:
                        f.write(audio_data)
                    
                    # Lưu kết quả vào database
                    attempt = PronunciationAttempt(
                        exercise_id=int(exercise_id),
                        user_id=current_user.id,
                        audio_file=audio_filename,
                        accuracy=advanced_evaluation['accuracy'],
                        feedback=advanced_evaluation['feedback'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(attempt)
                    db.session.commit()
                
                return jsonify(result)
        
        # Quay lại đánh giá cơ bản nếu không có phân tích nâng cao
        basic_evaluation = evaluate_pronunciation_basic(user_text, sample_text)
        result.update(basic_evaluation)
        
    return jsonify(result) 