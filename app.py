import os
import tempfile
import logging
import io
import shutil
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

def get_video_info(url, cookies_path=None):
    """Gets video information without downloading."""
    ydl_opts = {'quiet': True, 'no_warnings': True, 'skip_download': True}
    if cookies_path:
        ydl_opts['cookiefile'] = cookies_path
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            return ydl.extract_info(url, download=False)
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
    data = request.form or request.get_json() or {}
    url = data.get('url')

    cookies_file_path = None
    temp_cookies_file = None
    if 'cookies' in request.files:
        cookies = request.files['cookies']
        temp_cookies_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        cookies.save(temp_cookies_file)
        cookies_file_path = temp_cookies_file.name

    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    info = get_video_info(url, cookies_file_path)
    if not info:
        if cookies_file_path:
            os.remove(cookies_file_path)
        return jsonify({'error': 'Could not retrieve video information. The URL might be invalid or private.'}), 404

    if cookies_file_path:
        os.remove(cookies_file_path)

    return jsonify({
        'title': info.get('title', 'No title'),
        'thumbnail': info.get('thumbnail', '')
    })

@app.route('/download', methods=['POST'])
def download():
    """Handles the download request."""
    data = request.form if request.form else request.get_json()
    url = data.get('url')
    format_type = data.get('format', 'mp4')
    quality = data.get('quality')

    cookies_file_path = None
    temp_cookies_file = None
    if 'cookies' in request.files:
        cookies = request.files['cookies']
        temp_cookies_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        cookies.save(temp_cookies_file)
        cookies_file_path = temp_cookies_file.name
    elif data.get('cookies_path'):  # If cookies path supplied in JSON
        cookies_file_path = data.get('cookies_path')

    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    temp_dir = tempfile.mkdtemp(prefix='yt-dl-')

    try:
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'logger': logging.getLogger(),
        }
        if cookies_file_path:
            ydl_opts['cookiefile'] = cookies_file_path

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

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info(f"Downloading with options: {ydl_opts}")
            info = ydl.extract_info(url, download=True)

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
        error_message = str(e).split(':')[-1].strip()
        return jsonify({'error': f'Download failed: {error_message}'}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected server error occurred.'}), 500
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logging.info(f"Cleaned up directory: {temp_dir}")
        if cookies_file_path and os.path.exists(cookies_file_path):
            os.remove(cookies_file_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)