import os
import time
import logging
import atexit
from flask import Flask, render_template, request, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from ..downloader.manager import DownloadManager

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define the directory where files will be saved and the cleanup interval.
DOWNLOAD_DIRECTORY = "/tmp/downloads"
CLEANUP_INTERVAL_MINUTES = 30  # Files older than this will be removed
MAX_FILE_AGE_SECONDS = CLEANUP_INTERVAL_MINUTES * 60

# Ensure the download directory exists
if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)
    logging.info(f"Created download directory: {DOWNLOAD_DIRECTORY}")

app = Flask(__name__, template_folder='templates', static_folder='static')
download_manager = DownloadManager(download_path=DOWNLOAD_DIRECTORY)

# --- File Cleanup Scheduler ---
def cleanup_old_files():
    """Removes files from the download directory that are older than MAX_FILE_AGE_SECONDS."""
    logging.info("Running scheduled cleanup of old files...")
    now = time.time()
    for filename in os.listdir(DOWNLOAD_DIRECTORY):
        file_path = os.path.join(DOWNLOAD_DIRECTORY, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > MAX_FILE_AGE_SECONDS:
                    os.unlink(file_path)
                    logging.info(f"Removed old file: {filename}")
            elif os.path.isdir(file_path):
                 dir_age = now - os.path.getmtime(file_path)
                 if dir_age > MAX_FILE_AGE_SECONDS:
                    os.rmdir(file_path)
                    logging.info(f"Removed old directory: {filename}")
        except Exception as e:
            logging.error(f"Error cleaning up {file_path}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=CLEANUP_INTERVAL_MINUTES)
scheduler.start()
# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def get_info_route():
    """Gets video or playlist info from a URL."""
    url = request.get_json().get('url')
    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    info = download_manager.get_info(url)
    if 'error' in info:
        return jsonify({'error': info['error']}), 404

    return jsonify(info)

@app.route('/search', methods=['POST'])
def search_route():
    """Searches for videos."""
    query = request.get_json().get('query')
    if not query:
        return jsonify({'error': 'Query is required.'}), 400

    search_result = download_manager.search(query)
    if 'error' in search_result:
        return jsonify({'error': search_result['error']}), 500

    valid_entries = [entry for entry in search_result.get('entries', []) if entry.get('webpage_url')]
    return jsonify(valid_entries)


@app.route('/download', methods=['POST'])
def download_route():
    """Handles a download request."""
    data = request.get_json()
    url = data.get('url')
    format_choice = data.get('format', 'mp4')
    quality = data.get('quality', 'best')
    is_playlist = data.get('is_playlist', False)

    if not url:
        return jsonify({'error': 'URL is required.'}), 400

    result = download_manager.download_media(url, format_choice, quality, is_playlist)

    if result['status'] == 'success':
        filename = result.get('filename')
        download_url = f"/downloads/{filename}"
        return jsonify({'status': 'success', 'download_url': download_url})
    else:
        return jsonify({'status': 'error', 'message': result['message']}), 500

@app.route('/downloads/<path:filename>')
def serve_download(filename):
    """Serves a downloaded file."""
    logging.info(f"Serving file: {filename} from {DOWNLOAD_DIRECTORY}")
    return send_from_directory(
        DOWNLOAD_DIRECTORY,
        filename,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
