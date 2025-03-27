import os
from flask import Flask, render_template, request, send_file
from moviepy.editor import VideoFileClip
import yt_dlp
import uuid

app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def download_reel(url, output_filename):
    ydl_opts = {
        'outtmpl': output_filename,
        'quiet': True,
        'noplaylist': True,
        'format': 'mp4',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def convert_to_gif(input_path, output_path, start=None, end=None):
    clip = VideoFileClip(input_path)
    if start is not None and end is not None:
        clip = clip.subclip(float(start), float(end))
    clip.write_gif(output_path, fps=10)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        reel_url = request.form['url']
        start_time = request.form.get('start')
        end_time = request.form.get('end')

        unique_id = str(uuid.uuid4())
        video_path = os.path.join(DOWNLOAD_DIR, f"{unique_id}.mp4")
        gif_path = os.path.join(DOWNLOAD_DIR, f"{unique_id}.gif")

        try:
            download_reel(reel_url, video_path)
            convert_to_gif(video_path, gif_path, start_time, end_time)
            return send_file(gif_path, as_attachment=True)
        except Exception as e:
            return f"<h3>Error: {str(e)}</h3>"

    return render_template("index.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
