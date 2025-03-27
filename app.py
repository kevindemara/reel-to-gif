import os
import uuid
import requests
from flask import Flask, render_template, request, send_file
from moviepy.editor import VideoFileClip

app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# ✅ Replace with your actual RapidAPI key when deploying
RAPIDAPI_HOST = "instagram-story-downloader-media-downloader.p.rapidapi.com"
RAPIDAPI_KEY = "278c376dfdmsh7de75a21db734cbp10b07cjsn5cab6b5bb454"

def download_reel_with_api(insta_url, output_filename):
    url_encoded = requests.utils.quote(insta_url, safe="")
    endpoint = f"https://{RAPIDAPI_HOST}/index?url={url_encoded}"

    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': RAPIDAPI_HOST
    }

    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Extract video URL from response (check structure)
    video_url = data.get("media", [{}])[0].get("url")
    if not video_url:
        raise Exception("Could not retrieve video URL from API response.")

    # Download the video
    video_response = requests.get(video_url, stream=True)
    with open(output_filename, "wb") as f:
        for chunk in video_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def convert_to_gif(input_path, output_path, start=None, end=None):
    clip = VideoFileClip(input_path)
    if start and end:
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
            download_reel_with_api(reel_url, video_path)
            convert_to_gif(video_path, gif_path, start_time, end_time)
            return send_file(gif_path, as_attachment=True)
        except Exception as e:
            return f"<h3>Error: {str(e)}</h3>"

    return render_template("index.html")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
