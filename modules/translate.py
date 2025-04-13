from flask import Flask, Blueprint, render_template, request, jsonify, session
from deep_translator import GoogleTranslator
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Tạo Blueprint cho module dịch
translate_bp = Blueprint('translate', __name__)

# Khởi tạo translator
translator = GoogleTranslator()

# Lấy danh sách ngôn ngữ hỗ trợ từ GoogleTranslator
LANGUAGES = translator.get_supported_languages(as_dict=True)

@translate_bp.route('/translate', methods=['GET', 'POST'])
def translate_text():
    if request.method == 'GET':
        history = session.get('translate_history', [])
        return render_template("translate_text.html", history=history, languages=LANGUAGES)

    if not request.is_json:
        return jsonify({'success': False, 'error': 'Yêu cầu phải là JSON'}), 400

    data = request.get_json(silent=True)
    if not data or 'text' not in data or 'target_lang' not in data or 'source_lang' not in data:
        return jsonify({'success': False, 'error': 'Định dạng JSON không hợp lệ'}), 400

    text = data['text'].strip()
    target_lang = data['target_lang'].strip()
    source_lang = data['source_lang'].strip()

    if not text:
        return jsonify({'success': False, 'error': 'Không có văn bản để dịch'}), 400

    if source_lang == 'auto':
        return jsonify({'success': False, 'error': 'Tự động phát hiện ngôn ngữ không được hỗ trợ. Vui lòng chọn ngôn ngữ nguồn.'}), 400

    try:
        # Dịch văn bản
        translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(text)

        # Lưu vào lịch sử dịch
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
        history = history[:10]
        session['translate_history'] = history

        return jsonify({
            'success': True,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'detected_lang': source_lang
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@translate_bp.route('/translate/file', methods=['POST'])
def translate_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file được cung cấp'}), 400

    file = request.files['file']
    target_lang = request.form.get('target_lang', 'en')
    source_lang = request.form.get('source_lang', 'auto')

    if file.filename == '':
        return jsonify({'success': False, 'error': 'Chưa chọn file'}), 400

    if source_lang == 'auto':
        return jsonify({'success': False, 'error': 'Tự động phát hiện ngôn ngữ không được hỗ trợ. Vui lòng chọn ngôn ngữ nguồn.'}), 400

    try:
        content = file.read().decode('utf-8')

        translated_text = GoogleTranslator(source=source_lang, target=target_lang).translate(content)

        return jsonify({
            'success': True,
            'translated_text': translated_text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

app.register_blueprint(translate_bp)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5001)