from flask import Blueprint, render_template, request, jsonify
from deep_translator import GoogleTranslator

translate_bp = Blueprint('translate', __name__)

@translate_bp.route('/translate', methods=['GET', 'POST'])
def translate_text():
    if request.method == 'GET':
        return render_template("translate_text.html")

    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

    data = request.get_json(silent=True)
    if not data or 'text' not in data or 'target_lang' not in data:
        return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400

    text = data['text']
    target_lang = data['target_lang']

    if not text.strip():
        return jsonify({'success': False, 'error': 'No text provided'}), 400

    try:
        # Sử dụng deep-translator để dịch
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return jsonify({'success': True, 'translated_text': translated_text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500