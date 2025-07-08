from flask import Flask, render_template, request, send_file, jsonify
import pyttsx3
import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'temp_files'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def text_to_speech(text, output_filename):
    """Converts text to speech and saves to a file."""
    try:
        engine = pyttsx3.init()
        # You might want to list available voices and let the user choose
        # voices = engine.getProperty('voices')
        # engine.setProperty('voice', voices[0].id) # Example: Set to the first available voice
        engine.save_to_file(text, output_filename)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"Error in text_to_speech: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tts', methods=['POST'])
def api_tts():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400

    text_input = data['text']
    if not text_input.strip():
        return jsonify({"error": "Text cannot be empty"}), 400

    unique_id = uuid.uuid4()
    output_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"tts_audio_{unique_id}.mp3")

    if text_to_speech(text_input, output_filename):
        try:
            return send_file(output_filename, as_attachment=True, download_name='speech.mp3', mimetype='audio/mpeg')
        except Exception as e:
            print(f"Error sending file: {e}")
            return jsonify({"error": "Failed to send audio file"}), 500
        finally:
            # Clean up the file after sending
            # For a more robust solution, consider a scheduled cleanup task
            if os.path.exists(output_filename):
                try:
                    os.remove(output_filename)
                except Exception as e:
                    print(f"Error deleting temp file {output_filename}: {e}")
    else:
        return jsonify({"error": "Failed to generate speech"}), 500

# Required for Pytesseract - specify Tesseract CMD if not in PATH
# In a sandboxed environment, Tesseract might not be installed or accessible.
# This will likely be a point of failure if Tesseract is not pre-installed in the environment.
# import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract' # Or your Tesseract path

from PIL import Image
import pytesseract # Moved import here to see if it helps with sandbox initialization

@app.route('/api/image-to-speech', methods=['POST'])
def api_image_to_speech():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400

    if file:
        try:
            # Save uploaded image temporarily
            unique_id = uuid.uuid4()
            temp_image_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"upload_{unique_id}_{file.filename}")
            file.save(temp_image_filename)

            # Perform OCR
            extracted_text = pytesseract.image_to_string(Image.open(temp_image_filename))
            os.remove(temp_image_filename) # Clean up uploaded image

            if not extracted_text.strip():
                return jsonify({"error": "No text found in image"}), 400

            # Convert extracted text to speech
            tts_output_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"tts_audio_from_image_{unique_id}.mp3")
            if text_to_speech(extracted_text, tts_output_filename):
                try:
                    return send_file(tts_output_filename, as_attachment=True, download_name='speech_from_image.mp3', mimetype='audio/mpeg')
                finally:
                    if os.path.exists(tts_output_filename):
                        try:
                            os.remove(tts_output_filename)
                        except Exception as e:
                            print(f"Error deleting temp audio file {tts_output_filename}: {e}")
            else:
                return jsonify({"error": "Failed to generate speech from image text"}), 500

        except pytesseract.TesseractNotFoundError:
            print("Tesseract is not installed or not in your PATH.")
            return jsonify({"error": "OCR processing unavailable: Tesseract not found on server."}), 500
        except Exception as e:
            print(f"Error in image-to-speech: {e}")
            # Clean up temp image if it exists and an error occurred
            if os.path.exists(temp_image_filename):
                try:
                    os.remove(temp_image_filename)
                except Exception as del_e:
                    print(f"Error deleting temp image file {temp_image_filename} during error handling: {del_e}")
            return jsonify({"error": "Failed to process image"}), 500

from moviepy.editor import TextClip, ColorClip, CompositeVideoClip, AudioFileClip
import time # To ensure unique filenames for video components

@app.route('/api/text-to-video', methods=['POST'])
def api_text_to_video():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided for video"}), 400

    video_text = data['text']
    if not video_text.strip():
        return jsonify({"error": "Video text cannot be empty"}), 400

    unique_id = uuid.uuid4()
    audio_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"video_audio_{unique_id}.mp3")
    video_filename = os.path.join(app.config['UPLOAD_FOLDER'], f"video_output_{unique_id}.mp4")

    # 1. Generate Speech
    if not text_to_speech(video_text, audio_filename):
        return jsonify({"error": "Failed to generate audio for video"}), 500

    try:
        # 2. Create Video Clips
        audio_clip = AudioFileClip(audio_filename)
        duration = audio_clip.duration
        if duration == 0: # Handle case where audio might be silent or very short
            duration = max(1, len(video_text) * 0.2) # Estimate duration based on text length, min 1 sec

        # Create a background clip (dark blue)
        # Dimensions can be adjusted, e.g., 720p
        bg_color = (22, 36, 71) # Corresponds to #162447
        background_clip = ColorClip(size=(1280, 720), color=bg_color, ismask=False, duration=duration)

        # Create a text clip
        # You might need to install a font in the environment or specify a path to a .ttf file
        # For simplicity, relying on MoviePy's default font or one available in the environment.
        # More advanced: split text into lines, adjust font size, color, position.
        txt_clip = TextClip(video_text, fontsize=70, color='white', font='Arial', size=(1200, None), method='caption')
        txt_clip = txt_clip.set_position('center').set_duration(duration)

        # 3. Composite Video
        video = CompositeVideoClip([background_clip, txt_clip])
        video = video.set_audio(audio_clip)

        # 4. Write Video File
        # Codec can be specified, e.g., libx264 for H.264. Default is often fine.
        # Threads can be used to speed up rendering if environment supports it.
        video.write_videofile(video_filename, fps=24, codec='libx264', audio_codec='aac')

        return send_file(video_filename, as_attachment=True, download_name='voxir_video.mp4', mimetype='video/mp4')

    except Exception as e:
        print(f"Error in video generation: {e}")
        return jsonify({"error": f"Failed to generate video: {str(e)}"}), 500
    finally:
        # Clean up temporary audio and video files
        if os.path.exists(audio_filename):
            try:
                os.remove(audio_filename)
            except Exception as e_del_audio:
                print(f"Error deleting temp audio file {audio_filename}: {e_del_audio}")
        if os.path.exists(video_filename):
            try:
                # Ensure file is closed by MoviePy before attempting to delete, sometimes needs a small delay
                time.sleep(0.5)
                os.remove(video_filename)
            except Exception as e_del_video:
                 print(f"Error deleting temp video file {video_filename}: {e_del_video}")


if __name__ == '__main__':
    app.run(debug=True)
