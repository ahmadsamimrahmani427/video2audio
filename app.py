from flask import Flask, request, send_file
from moviepy.editor import VideoFileClip
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_video():
    file = request.files['video']
    file.save("uploaded_video.mp4")
    
    video = VideoFileClip("uploaded_video.mp4")
    audio = video.audio
    audio.write_audiofile("output_audio.mp3")

    return send_file("output_audio.mp3", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, port=3000)
