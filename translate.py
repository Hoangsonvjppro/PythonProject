

# from flask import Flask, request, jsonify, Blueprint
# from googletrans import Translator

# translate_bp = Blueprint('translate', __name__)
# translator = Translator()

# @translate_bp.route('/translate', methods=['GET', 'POST'])
# def translate_text():
#     if request.method == 'POST' or 'GET':
#         return jsonify({'message': 'Use POST to translate text'})

#     text = request.json.get('text', '')
#     target_lang = request.json.get('target_lang', 'en')

#     if not text:
#         return jsonify({'success': False, 'error': 'No text provided'}), 400

#     try:
#         translated = translator.translate(text, dest=target_lang)
#         return jsonify({'success': True, 'translated_text': translated.text})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# from flask import Flask, request, jsonify, Blueprint
# from googletrans import Translator

# translate_bp = Blueprint('translate', __name__)
# translator = Translator()

# @translate_bp.route('/translate', methods=['GET', 'POST'])
# def translate_text():
#     if not request.is_json:
#         return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

#     data = request.get_json()
#     text = data.get('text', '')
#     target_lang = data.get('target_lang', 'en')

#     if not text:
#         return jsonify({'success': False, 'error': 'No text provided'}), 400

#     try:
#         translated = translator.translate(text, dest=target_lang)
#         return jsonify({'success': True, 'translated_text': translated.text})
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)}), 500

# from flask import Flask, request, jsonify, Blueprint
from googletrans import Translator
from flask import Flask, Blueprint, render_template, request, jsonify

translate_bp = Blueprint('translate', __name__)
translator = Translator()

@translate_bp.route('/translate', methods=['GET', 'POST'])
def translate_text():
    if request.method == 'GET':
        return render_template("translate_text.html")
        return jsonify({'message': 'Use POST to translate text'})

    # Kiểm tra request có chứa JSON không
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

    data = request.get_json(silent=True)  # Tránh lỗi nếu JSON bị sai format

    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400

    text = data.get('text', '')
    target_lang = data.get('target_lang', 'en')

    if not text:
        return jsonify({'success': False, 'error': 'No text provided'}), 400

    try:
        translated = translator.translate(text, dest=target_lang)
        return jsonify({'success': True, 'translated_text': translated.text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
