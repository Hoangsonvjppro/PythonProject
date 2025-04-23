import speech_recognition as sr
from flask import Blueprint, render_template, request, jsonify
import difflib  # For string comparison
import os
import requests
import json
import numpy as np
from pydub import AudioSegment
import tempfile

# Create Blueprint for this module
speech_bp = Blueprint('speech', __name__)

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            print("Listening...")
            audio = recognizer.listen(source, timeout=5)  # 5 second timeout
            # Save audio for later analysis
            audio_data = audio.get_wav_data()
            # Use Google Speech Recognition to convert to text
            text = recognizer.recognize_google(audio, language="en-US")
            return {
                "success": True, 
                "text": text,
                "audio_data": audio_data
            }
        except sr.UnknownValueError:
            return {"success": False, "error": "Could not recognize speech."}
        except sr.RequestError as e:
            return {"success": False, "error": f"Connection error: {e}"}
        except sr.WaitTimeoutError:
            return {"success": False, "error": "Timeout, please try again."}

# Sample sentences list (can be stored in database later)
SAMPLE_SENTENCES = [
    "She sells seashells by the seashore",
    "This restaurant serves delicious Vietnamese food",
    "Technology is transforming the way we communicate",
    "She often participates in academic discussions"
]

def evaluate_pronunciation_basic(user_text, sample_text):
    # Simple string comparison using difflib (fallback method)
    similarity = difflib.SequenceMatcher(None, user_text.lower(), sample_text.lower()).ratio()
    accuracy = similarity * 100
    if accuracy >= 90:
        feedback = "Excellent pronunciation!"
    elif accuracy >= 70:
        feedback = "Good effort, but could be clearer."
    else:
        feedback = "Needs improvement, try again."
    return {"accuracy": round(accuracy, 2), "feedback": feedback}

def analyze_audio_features(audio_data, sample_text):
    """
    Analyze audio features to evaluate pronunciation quality
    This is a more advanced method that could be implemented with:
    1. External API like Google Cloud Speech-to-Text with confidence scores
    2. A specialized pronunciation assessment API
    3. Local ML model analyzing audio features
    """
    # Save audio data to a temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
        temp_audio.write(audio_data)
        temp_audio_path = temp_audio.name
    
    try:
        # Example implementation with advanced features:
        # 1. Extract prosody features (rhythm, stress, intonation)
        # 2. Compare phoneme alignment with expected pronunciation
        # 3. Detect common pronunciation errors
        
        # For this example, we'll use a simplified simulation
        # In a production environment, you would integrate with a proper API
        
        # Simulate advanced analysis with improved results
        word_count = len(sample_text.split())
        
        # Extract basic audio features
        audio = AudioSegment.from_wav(temp_audio_path)
        
        # Calculate audio energy (volume)
        energy = np.array([chunk.dBFS for chunk in audio[::100]])
        energy_var = np.var(energy[energy > -40])  # Variance of non-silent parts
        
        # Simulated metrics that would come from a real API:
        # - Phoneme accuracy
        # - Prosody accuracy (rhythm and intonation)
        # - Fluency (pauses, hesitations)
        phoneme_accuracy = min(95, 70 + energy_var)
        prosody_accuracy = min(90, 65 + energy_var * 0.8)
        fluency = min(85, 60 + energy_var * 1.2)
        
        # Combine metrics for overall score
        overall_accuracy = (phoneme_accuracy * 0.5 + prosody_accuracy * 0.3 + fluency * 0.2)
        
        # Detailed feedback (would be more specific with a real API)
        if overall_accuracy >= 90:
            detailed_feedback = "Excellent pronunciation with good rhythm and intonation."
        elif overall_accuracy >= 80:
            detailed_feedback = "Good pronunciation. Minor improvements needed in rhythm and stress."
        elif overall_accuracy >= 70:
            detailed_feedback = "Adequate pronunciation. Work on word stress and intonation patterns."
        else:
            detailed_feedback = "Needs practice. Focus on individual sounds and word connections."
        
        # Cleanup
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
        # Fallback to basic method if advanced analysis fails
        print(f"Advanced analysis failed: {e}")
        os.unlink(temp_audio_path)
        return None

# Route for Speech to Text page
@speech_bp.route('/speech_to_text', methods=['GET', 'POST'])
def speech_to_text():
    if request.method == 'POST':
        sample_sentence = request.json.get('sample_sentence')
        if not sample_sentence:
            return jsonify({"success": False, "error": "No sample sentence provided."}), 400

        # Get speech recognition result
        result = recognize_speech()
        if result["success"]:
            user_text = result["text"]
            
            # Trích xuất audio_data từ result trước khi serialize thành JSON
            audio_data = result.pop("audio_data", None)  # Xóa audio_data khỏi result
            
            # Try advanced audio analysis if we have audio data
            if audio_data:
                advanced_evaluation = analyze_audio_features(audio_data, sample_sentence)
                if advanced_evaluation:
                    result.update(advanced_evaluation)
                    return jsonify(result)
            
            # Fallback to basic text comparison if advanced analysis is not available
            basic_evaluation = evaluate_pronunciation_basic(user_text, sample_sentence)
            result.update(basic_evaluation)
            
        return jsonify(result)
    
    return render_template('speech_to_text.html', sample_sentences=SAMPLE_SENTENCES)

