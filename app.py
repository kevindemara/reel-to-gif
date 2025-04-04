import os
import uuid
import requests
from flask import Flask, render_template, request, send_file
from moviepy.editor import VideoFileClip
import imageio

app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 🔐 Replace with your own key
RAPIDAPI_HOST = "instagram-story-downloader-media-downloader.p.rapidapi.com"
RAPIDAPI_KEY = "02412ef3a0msh908c9697f7e8943p1ed5d8jsn4eda7a4cbe29"

def download_reel_with_api(insta_url, output_filename):
    url_encoded = requests.utils.quote(insta_url, safe="")
    endpoint = f"https://{RAPIDAPI_HOST}/index?url={url_encoded}"

    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': RAPIDAPI_HOST
    }

    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()

    try:
        data = response.json()
        with open("api_debug_log.txt", "w") as f:
            f.write(str(data))
    except ValueError:
        with open("api_debug_log.txt", "w") as f:
            f.write(response.text)
        raise Exception("API response is not in JSON format.")

    video_url = None
    if isinstance(data, dict):
        if "media" in data and isinstance(data["media"], str):
            video_url = data["media"]

    if not video_url:
        raise Exception("Could not retrieve video URL from API response.")

    video_response = requests.get(video_url, stream=True)
    with open(output_filename, "wb") as f:
        for chunk in video_response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

def convert_to_gif(input_path, output_path, start=None, end=None, palettesize=32):
    clip = VideoFileClip(input_path)
    if start and end:
        clip = clip.subclip(float(start), float(end))

    temp_gif = output_path.replace(".gif", "_raw.gif")
    clip.write_gif(temp_gif, fps=10)

    reader = imageio.get_reader(temp_gif)
    frames = [frame for frame in reader]

    imageio.mimsave(output_path, frames, format='GIF',
                    duration=clip.duration / len(frames),
                    palettesize=palettesize)
    
    os.remove(temp_gif)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        reel_url = request.form['url']
        start_time = request.form.get('start')
        end_time = request.form.get('end')
        quality = request.form.get('quality', 'medium')

        palettesize_map = {
            'low': 16,
            'medium': 32,
            'high': 64
        }
        palettesize = palettesize_map.get(quality, 32)

        unique_id = str(uuid.uuid4())
        video_path = os.path.join(DOWNLOAD_DIR, f"{unique_id}.mp4")
        gif_path = os.path.join(DOWNLOAD_DIR, f"{unique_id}.gif")

        try:
            download_reel_with_api(reel_url, video_path)
            convert_to_gif(video_path, gif_path, start_time, end_time, palettesize)
            return send_file(gif_path, as_attachment=True)
        except Exception as e:
            debug = ""
            if os.path.exists("api_debug_log.txt"):
                with open("api_debug_log.txt") as f:
                    debug = f.read()
            return f"<h3>Error: {str(e)}</h3><pre>{debug}</pre>"

    return render_template("index.html")
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
