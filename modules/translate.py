import asyncio
from googletrans import Translator, LANGUAGES
from flask import Flask, Blueprint, render_template, request, jsonify, session
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Thêm secret key cho session

# Tạo Blueprint cho dịch thuật
translate_bp = Blueprint('translate', __name__)
translator = Translator()

@translate_bp.route('/translate', methods=['GET', 'POST'])
def translate_text():
    if request.method == 'GET':
        # Lấy lịch sử dịch từ session
        history = session.get('translate_history', [])
        return render_template("translate_text.html",
                             history=history,
                             languages=LANGUAGES)

    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

    data = request.get_json(silent=True)
    if not data or 'text' not in data or 'target_lang' not in data:
        return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400

    text = data['text'].strip()
    target_lang = data['target_lang'].strip()
    source_lang = data.get('source_lang', 'auto')  # Thêm source_lang, mặc định là 'auto'

    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400

    try:
        # Phát hiện ngôn ngữ nguồn nếu không được chỉ định
        if source_lang == 'auto':
            detected = translator.detect(text)
            source_lang = detected.lang
        
        # Dịch văn bản
        translated_text = asyncio.run(translate_text_async(text, target_lang, source_lang))
        
        # Lưu vào lịch sử
        history_entry = {
            'text': text,
            'translated': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Cập nhật session
        history = session.get('translate_history', [])
        history.insert(0, history_entry)
        history = history[:10]  # Giữ tối đa 10 mục
        session['translate_history'] = history
        
        return jsonify({
            'success': True, 
            'translated_text': translated_text,
            'source_lang': source_lang,
            'detected_lang': detected.lang if source_lang == 'auto' else source_lang
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@translate_bp.route('/translate/file', methods=['POST'])
def translate_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
        
    file = request.files['file']
    target_lang = request.form.get('target_lang', 'en')
    source_lang = request.form.get('source_lang', 'auto')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
        
    try:
        # Đọc nội dung file
        content = file.read().decode('utf-8')
        
        # Dịch nội dung
        translated_text = asyncio.run(translate_text_async(content, target_lang, source_lang))
        
        return jsonify({
            'success': True,
            'translated_text': translated_text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

async def translate_text_async(text, target_lang, source_lang='auto'):
    loop = asyncio.get_running_loop()
    translated = await loop.run_in_executor(None, lambda: translator.translate(text, dest=target_lang, src=source_lang))
    return translated.text

# Đăng ký Blueprint vào ứng dụng Flask
app.register_blueprint(translate_bp)

if __name__ == "__main__":
    app.run(debug=True)  
