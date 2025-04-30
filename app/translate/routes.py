from flask import render_template, request, jsonify, session
from deep_translator import GoogleTranslator
import os
from datetime import datetime
import hashlib
import functools
import json
from app.translate import bp
from app.extensions import translate_cache, csrf
from flask import current_app

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
    cached_result = translate_cache.get(key)
    if cached_result:
        return cached_result
    
    # If not in cache, translate and store in cache
    try:
        translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        translate_cache.set(key, translated)
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

@bp.route('/', methods=['GET'])
def index():
    """Render the translation homepage"""
    return render_template("translate/index.html")

@bp.route('/translate', methods=['GET'])
def translate_text():
    """Handle translation page rendering"""
    history = session.get('translate_history', [])
    return render_template("translate/translate_text.html", history=history, languages=LANGUAGES)

@bp.route('/translate', methods=['POST'])
@csrf.exempt
def translate_text_api():
    """Handle translation API requests"""
    # Debug thông tin request
    print(f"Request headers: {request.headers}")
    print(f"Request content type: {request.content_type}")
    print(f"Request is JSON: {request.is_json}")
    try:
        print(f"Request raw data: {request.get_data()}")
    except Exception as e:
        print(f"Error reading request data: {e}")

    if not request.is_json:
        error_response = jsonify({'success': False, 'error': 'Request must be JSON'})
        print(f"Returning error: {error_response.get_data(as_text=True)}")
        return error_response, 400

    data = request.get_json(silent=True)
    print(f"Parsed JSON data: {data}")
    
    if not data or 'text' not in data or 'target_lang' not in data or 'source_lang' not in data:
        error_response = jsonify({'success': False, 'error': 'Invalid JSON format'})
        print(f"Returning error: {error_response.get_data(as_text=True)}")
        return error_response, 400

    text = data['text'].strip()
    target_lang = data['target_lang'].strip()
    source_lang = data['source_lang'].strip()
    
    print(f"Processing translation: text='{text[:50]}{'...' if len(text) > 50 else ''}', source={source_lang}, target={target_lang}")

    if not text:
        return jsonify({'success': False, 'error': 'No text to translate'}), 400

    if source_lang == 'auto':
        return jsonify({'success': False, 'error': 'Automatic language detection is not supported. Please select a source language.'}), 400

    # Check text length
    max_length = current_app.config.get('TRANSLATE_MAX_LENGTH', 5000)
    if len(text) > max_length:
        return jsonify({'success': False, 'error': f'Text is too long. Maximum length is {max_length} characters.'}), 400

    try:
        # Use cached translation
        translated_text = translate_with_cache(text, source_lang, target_lang)
        print(f"Translation result: '{translated_text[:50]}{'...' if translated_text and len(translated_text) > 50 else ''}'")

        if not translated_text:
            error_response = jsonify({'success': False, 'error': 'Translation failed'})
            print(f"Translation failed, returning: {error_response.get_data(as_text=True)}")
            return error_response, 500

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

        success_response = jsonify({
            'success': True,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'detected_lang': source_lang
        })
        print(f"Returning success response: {success_response.get_data(as_text=True)[:100]}...")
        return success_response
    except Exception as e:
        print(f"Translation API error: {str(e)}")
        error_response = jsonify({'success': False, 'error': str(e)})
        print(f"Returning error: {error_response.get_data(as_text=True)}")
        return error_response, 500

@bp.route('/translate/file', methods=['POST'])
@csrf.exempt
def translate_file():
    """Handle translation requests for files"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    target_lang = request.form.get('target_lang', current_app.config.get('TRANSLATE_DEFAULT_TARGET', 'en'))
    source_lang = request.form.get('source_lang', current_app.config.get('TRANSLATE_DEFAULT_SOURCE', 'auto'))

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if source_lang == 'auto':
        return jsonify({'success': False, 'error': 'Automatic language detection is not supported. Please select a source language.'}), 400

    try:
        content = file.read().decode('utf-8')
        max_length = current_app.config.get('TRANSLATE_MAX_LENGTH', 5000)

        # For large files, break into chunks to avoid API limits
        if len(content) > max_length:
            chunks = []
            words = content.split()
            current_chunk = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= max_length:  # +1 for space
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
            'translated_text': translated_text,
            'source_text': content,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    except Exception as e:
        print(f"File translation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 