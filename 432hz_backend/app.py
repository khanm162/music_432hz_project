from flask import Flask, request, jsonify, send_file
import os
import subprocess
import yt_dlp
from pathlib import Path
import re

app = Flask(__name__)

DOWNLOAD_DIR = 'downloads'
CONVERTED_DIR = 'converted'

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CONVERTED_DIR, exist_ok=True)


@app.route('/convert', methods=['POST'])
def convert():
    def safe_filename(name):
        return re.sub(r'[\\/*?:"<>|]', "_", name)

    data = request.get_json()
    youtube_url = data.get('url')

    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required'}), 400

    try:
        # Step 1: Extract title
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            title = info.get('title', 'audio')

        safe_title = safe_filename(title)
        input_base = os.path.join(DOWNLOAD_DIR, safe_title)
        input_file = f"{input_base}.mp3"
        output_file = os.path.join(CONVERTED_DIR, f"{safe_title}_432hz.mp3")

        # Step 2: Download audio using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': input_base,  # no .mp3 here to avoid .mp3.mp3
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Step 3: Convert to 432Hz using ffmpeg
        command = [
            'ffmpeg', '-y', '-i', str(Path(input_file)),
            '-af', 'asetrate=44100*432/440,aresample=44100',
            str(Path(output_file))
        ]

        subprocess.run(command, check=True)

        return jsonify({
            'message': '✅ Successfully converted and downloaded the song!',
            'file_path': f"/{output_file}"
        }), 200

    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'FFmpeg failed: {e}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return "🎶 432Hz Converter API is running!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
