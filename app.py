from flask import Flask, request, send_file, render_template, jsonify
import os
from pedalboard.io import AudioFile
from pedalboard import Pedalboard, Gain
from pydub import AudioSegment
import wave
import speech_recognition as sr

app = Flask(__name__)

# Ensure the 'audio' directory exists
audio_directory = os.path.abspath("audio")
os.makedirs(audio_directory, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_audio', methods=['POST'])
def save_audio():
    try:
        audio_file = request.files['audio']
        
        if audio_file is None:
            return jsonify({"error": "No audio file provided."}), 400

        save_path = os.path.abspath("audio/recording.wav")

        audio_file.save(save_path)
        print("Audio file saved successfully:", os.path.isfile(save_path))

        try:
            sound = AudioSegment.from_file(save_path)
            sound.export(save_path, format="wav")
        except Exception as e:
            print(f"Error converting audio file: {e}")
            return jsonify({"error": "Invalid audio format"}), 400

        return jsonify({"message": "Audio saved successfully."}), 200
    except Exception as e:
        print(f"Error saving audio: {e}")
        return jsonify({"error": "Could not save audio file."}), 500


@app.route('/enhance', methods=['POST'])
def enhance_audio():
    try:
        input_path = os.path.join(audio_directory, "recording.wav")
        
        if not os.path.isfile(input_path):
            return jsonify({"error": "Audio file not found."}), 404

        # Validate WAV format compatibility
        try:
            with wave.open(input_path, 'rb') as file:
                if file.getnframes() == 0:
                    return jsonify({"error": "Audio file is empty or corrupted."}), 400
        except wave.Error as e:
            return jsonify({"error": f"Invalid audio file: {e}"}), 400

        # Process the audio file
        sr = 44100  # Set sample rate
        try:
            with AudioFile(input_path).resampled_to(sr) as f:
                audio = f.read(f.frames)
        except Exception as e:
            print(f"Error reading audio file: {e}")
            return jsonify({"error": "Could not read audio file"}), 400

        # Apply an example enhancement (e.g., gain boost)
        board = Pedalboard([Gain(gain_db=10)])  # Example effect for enhancement
        enhanced_audio = board(audio, sr)

        output_path = os.path.join(audio_directory, "enhanced_recording.wav")
        try:
            with AudioFile(output_path, 'w', sr, enhanced_audio.shape[0]) as f:
                f.write(enhanced_audio)
        except Exception as e:
            print(f"Error writing enhanced audio: {e}")
            return jsonify({"error": "Could not save enhanced audio"}), 500

        print("Audio processed and saved as:", output_path)
        response = send_file(output_path, as_attachment=True)
        return response

    except Exception as e:
        print(f"Error during audio enhancement: {e}")
        return jsonify({"error": "Error processing audio"}), 500

from pydub.silence import split_on_silence

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        audio_path = os.path.join(audio_directory, "recording.wav")
        
        # Check if the file exists
        if not os.path.isfile(audio_path):
            return jsonify({"error": "Audio file not found."}), 404

        # Convert to 16 kHz mono if needed
        try:
            sound = AudioSegment.from_file(audio_path)
            sound = sound.set_frame_rate(16000).set_channels(1)
            temp_path = os.path.join(audio_directory, "temp_recording.wav")
            sound.export(temp_path, format="wav")
        except Exception as e:
            print(f"Error converting audio for transcription: {e}")
            return jsonify({"error": "Could not prepare audio for transcription."}), 500

        # Load the processed audio for transcription
        recognizer = sr.Recognizer()
        audio_segments = []

        # Segment the audio on silent parts for better transcription accuracy
        sound = AudioSegment.from_wav(temp_path)
        chunks = split_on_silence(sound, min_silence_len=500, silence_thresh=sound.dBFS - 14, keep_silence=200)

        # Process each chunk and transcribe
        for i, chunk in enumerate(chunks):
            chunk_path = os.path.join(audio_directory, f"chunk_{i}.wav")
            chunk.export(chunk_path, format="wav")
            with sr.AudioFile(chunk_path) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                    audio_segments.append(text)
                except sr.UnknownValueError:
                    print(f"Unintelligible audio in chunk {i}")
                except sr.RequestError as e:
                    print(f"Request error from the service: {e}")
                    return jsonify({"error": f"Service error: {e}"}), 503
            os.remove(chunk_path)

        # Remove temporary file
        os.remove(temp_path)

        # Combine all transcribed chunks
        final_transcription = " ".join(audio_segments)
        if not final_transcription:
            return jsonify({"error": "Speech was unintelligible in all segments."}), 400
        
        return jsonify({"transcription": final_transcription}), 200

    except Exception as e:
        print(f"Error during transcription: {e}")
        return jsonify({"error": "Error processing audio for transcription"}), 500
    
@app.route('/predict_model', methods=['POST'])
def predict_model():
    try:
        model_path = os.path.join("model", "placeholder_model.pkl")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError("Model file not found. Placeholder logic here.")

        print(f"Loading model from {model_path}...")

        return jsonify({"status": "Model processing simulated"}), 200

    except FileNotFoundError as e:
        print(f"Model processing error: {e}")
        return jsonify({"error": "Model file missing or processing error occurred"}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

if __name__ == "__main__":
    app.run(debug=True,port=5004)
