import os
import tempfile
import logging
import io
import shutil
import re
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def extract_video_id(url):
    """Extracts the YouTube video ID from various URL formats."""
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(url):
    """Gets video information without downloading."""
    video_id = extract_video_id(url)
    if not video_id:
        return None

    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Prepend Invidious instance to bypass age restrictions
            invidious_url = f"https://yewtu.be/watch?v={video_id}"
            return ydl.extract_info(invidious_url, download=False)
        except yt_dlp.utils.DownloadError as e:
            logging.error(f"Error extracting video info: {e}")
            return None

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def get_info():
    """Gets video info (title, thumbnail) from a URL."""
    url = request.get_json().get('url')
    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    info = get_video_info(url)
    if not info:
        return jsonify({'error': 'Could not retrieve video information. The URL might be invalid or private.'}), 404

    return jsonify({
        'title': info.get('title', 'No title'),
        'thumbnail': info.get('thumbnail', '')
    })

@app.route('/search', methods=['POST'])
def search():
    """Searches for videos on YouTube."""
    query = request.get_json().get('query')
    if not query:
        return jsonify({'error': 'Query is required.'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'default_search': 'ytsearch5',  # Search for 5 results
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(query, download=False)
            videos = []
            if 'entries' in result:
                for entry in result['entries']:
                    videos.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'thumbnail': entry.get('thumbnail'),
                    })
            return jsonify(videos)
    except Exception as e:
        logging.error(f"An unexpected error occurred during search: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected server error occurred during search.'}), 500

@app.route('/download', methods=['POST'])
def download():
    """Handles the download request."""
    if 'url' not in request.form:
        return jsonify({'error': 'URL is required.'}), 400

    url = request.form['url']
    format_type = request.form.get('format', 'mp4')
    quality = request.form.get('quality')

    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({'error': 'Invalid YouTube URL.'}), 400

    temp_dir = tempfile.mkdtemp(prefix='yt-dl-')

    try:
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'logger': logging.getLogger(),
            'limit_rate': '10M',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': {
                        'Low': '128',
                        'Medium': '192',
                        'High': '320'
                    }.get(quality, '192'),
                }],
            })
        else: # mp4
            format_note = {
                '360p': 'bestvideo[height<=360]+bestaudio/best',
                '720p': 'bestvideo[height<=720]+bestaudio/best',
                '1080p': 'bestvideo[height<=1080]+bestaudio/best',
            }.get(quality, 'bestvideo+bestaudio/best')
            ydl_opts['format'] = format_note

        # Prepend Invidious instance to bypass age restrictions
        invidious_url = f"https://yewtu.be/watch?v={video_id}"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info(f"Downloading with options: {ydl_opts}")
            info = ydl.extract_info(invidious_url, download=True)

            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                base, _ = os.path.splitext(filename)
                downloaded_file_path = base + '.mp3'
            else:
                downloaded_file_path = filename

            if not os.path.exists(downloaded_file_path):
                files_in_dir = os.listdir(temp_dir)
                if not files_in_dir:
                    return jsonify({'error': 'Could not produce downloadable file.'}), 500
                downloaded_file_path = os.path.join(temp_dir, files_in_dir[0])

            logging.info(f"File prepared for sending: {downloaded_file_path}")

            file_buffer = io.BytesIO()
            with open(downloaded_file_path, 'rb') as f:
                file_buffer.write(f.read())
            file_buffer.seek(0)

            return send_file(
                file_buffer,
                as_attachment=True,
                download_name=os.path.basename(downloaded_file_path),
                mimetype='application/octet-stream'
            )

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"yt-dlp download error: {e}")
        error_message = str(e)
        if 'HTTP Error 429' in error_message:
            error_message = 'Too many requests. Please try again later.'
        else:
            error_message = "Download failed. The video may be private or unavailable."
        return jsonify({'error': error_message}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected server error occurred.'}), 500
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info(f"Cleaned up directory: {temp_dir}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)