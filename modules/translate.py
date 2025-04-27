from flask import Flask, Blueprint, render_template, request, jsonify, session
from deep_translator import GoogleTranslator
import os
from datetime import datetime
import hashlib
import functools
import json
from cachelib import SimpleCache

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Create a cache with a timeout of 1 day (86400 seconds)
cache = SimpleCache(default_timeout=86400)

# Create Blueprint for translation module
translate_bp = Blueprint('translate', __name__)

# Initialize translator
translator = GoogleTranslator()

# Get supported languages from GoogleTranslator
LANGUAGES = translator.get_supported_languages(as_dict=True)

def cache_key(text, source_lang, target_lang):
    """Generate a cache key for translation requests"""
    key_data = f"{text}|{source_lang}|{target_lang}"
    return hashlib.md5(key_data.encode('utf-8')).hexdigest()

def translate_with_cache(text, source_lang, target_lang):
    """Translate text with caching to reduce API calls"""
    if not text:
        return None
        
    # Generate a unique cache key
    key = cache_key(text, source_lang, target_lang)
    
    # Try to get from cache first
    cached_result = cache.get(key)
    if cached_result:
        return cached_result
    
    # If not in cache, translate and store in cache
    try:
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        cache.set(key, translated)
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return None

def batch_translate(text_list, source_lang, target_lang):
    """Efficiently translate a batch of texts"""
    # Join texts with a special delimiter for a single API call
    # This reduces the number of API calls when translating multiple short texts
    delimiter = "|||DELIMITER|||"
    combined_text = delimiter.join(text_list)
    
    # Translate combined text
    translated_combined = translate_with_cache(combined_text, source_lang, target_lang)
    
    # Split the result
    if translated_combined:
        return translated_combined.split(delimiter)
    return None

@translate_bp.route('/translate', methods=['GET', 'POST'])
def translate_text():
    if request.method == 'GET':
        history = session.get('translate_history', [])
        return render_template("translate_text.html", history=history, languages=LANGUAGES)

    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

    data = request.get_json(silent=True)
    if not data or 'text' not in data or 'target_lang' not in data or 'source_lang' not in data:
        return jsonify({'success': False, 'error': 'Invalid JSON format'}), 400

    text = data['text'].strip()
    target_lang = data['target_lang'].strip()
    source_lang = data['source_lang'].strip()

    if not text:
        return jsonify({'success': False, 'error': 'No text to translate'}), 400

    if source_lang == 'auto':
        return jsonify({'success': False, 'error': 'Automatic language detection is not supported. Please select a source language.'}), 400

    try:
        # Use cached translation
        translated_text = translate_with_cache(text, source_lang, target_lang)

        if not translated_text:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500

        # Add to history
        history_entry = {
            'text': text,
            'translated': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Update session
        history = session.get('translate_history', [])
        history.insert(0, history_entry)
        history = history[:10]  # Keep only the last 10 entries
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
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    target_lang = request.form.get('target_lang', 'en')
    source_lang = request.form.get('source_lang', 'auto')

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if source_lang == 'auto':
        return jsonify({'success': False, 'error': 'Automatic language detection is not supported. Please select a source language.'}), 400

    try:
        content = file.read().decode('utf-8')

        # For large files, break into chunks to avoid API limits
        if len(content) > 5000:  # If content is longer than 5000 chars
            chunks = []
            words = content.split()
            current_chunk = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= 5000:  # +1 for space
                    current_chunk.append(word)
                    current_length += len(word) + 1
                else:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
            
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            
            # Translate each chunk and join results
            translated_chunks = []
            for chunk in chunks:
                chunk_translation = translate_with_cache(chunk, source_lang, target_lang)
                if chunk_translation:
                    translated_chunks.append(chunk_translation)
                else:
                    return jsonify({'success': False, 'error': 'Error translating file content'}), 500
            
            translated_text = ' '.join(translated_chunks)
        else:
            translated_text = translate_with_cache(content, source_lang, target_lang)
            
        if not translated_text:
            return jsonify({'success': False, 'error': 'Translation failed'}), 500

        return jsonify({
            'success': True,
            'translated_text': translated_text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

app.register_blueprint(translate_bp)

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5001)