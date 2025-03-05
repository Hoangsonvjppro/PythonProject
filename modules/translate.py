

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
import asyncio
from googletrans import Translator
from flask import Blueprint, render_template, request, jsonify

translate_bp = Blueprint('translate', __name__)
translator = Translator()

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
        # Gọi async function bằng asyncio
        translated_text = asyncio.run(translate_text_async(text, target_lang))
        return jsonify({'success': True, 'translated_text': translated_text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

async def translate_text_async(text, target_lang):
    return (await translator.translate(text, dest=target_lang)).text

