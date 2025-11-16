import os
import uuid
import logging
import atexit
import time
import signal
from multiprocessing import Process, Manager
from flask import Flask, render_template, request, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from ..downloader.manager import DownloadManager

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/tmp/downloads")
CLEANUP_INTERVAL_MINUTES = int(os.environ.get("CLEANUP_INTERVAL_MINUTES", 30))
MAX_FILE_AGE_SECONDS = CLEANUP_INTERVAL_MINUTES * 60

# --- App Initialization ---
app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Download Manager Initialization ---
proxy_url = os.environ.get('PROXY_URL')
cookies_file = os.environ.get('COOKIES_FILE_PATH')
download_manager = DownloadManager(proxy=proxy_url, cookies_file=cookies_file)
logging.info("DownloadManager initialized.")
if proxy_url:
    logging.info(f"Using proxy: {proxy_url}")
if cookies_file and os.path.exists(cookies_file):
    logging.info(f"Using cookies file: {cookies_file}")
else:
    logging.info("No valid cookies file found, using default extractor args.")

# In-memory job store using a multiprocessing Manager
process_manager = Manager()
JOBS = process_manager.dict()

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    logging.info(f"Created download directory: {DOWNLOAD_DIR}")

# --- File Cleanup ---
def cleanup_old_files():
    logging.info("Running scheduled cleanup of old files...")
    now = time.time()
    for filename in os.listdir(DOWNLOAD_DIR):
        file_path = os.path.join(DOWNLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path) and (now - os.path.getmtime(file_path)) > MAX_FILE_AGE_SECONDS:
                os.unlink(file_path)
                logging.info(f"Removed old file: {filename}")
        except Exception as e:
            logging.error(f"Error during file cleanup for {file_path}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_files, trigger="interval", minutes=CLEANUP_INTERVAL_MINUTES)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# --- Worker ---
def download_worker(job_id, url, filename, format_choice, quality):
    JOBS[job_id].update({'status': 'running', 'message': 'Download is in progress...'})
    result = download_manager.download_media(
        url=url,
        download_dir=DOWNLOAD_DIR,
        output_filename=filename,
        format_choice=format_choice,
        quality=quality
    )
    if result['status'] == 'success':
        final_filename = os.path.basename(result['filepath'])
        JOBS[job_id].update({'status': 'completed', 'filename': final_filename})
    else:
        JOBS[job_id].update({'status': 'failed', 'message': result.get('message', 'An unknown error occurred.')})

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info', methods=['POST'])
def get_info_route():
    url = request.json.get('url')
    if not url: return jsonify({'error': 'URL is required.'}), 400
    info = download_manager.get_info(url)
    return jsonify(info)

@app.route('/start_download', methods=['POST'])
def start_download_route():
    data = request.json
    url, filename = data.get('url'), data.get('filename')
    if not all([url, filename]):
        return jsonify({'error': 'URL and filename are required.'}), 400

    job_id = str(uuid.uuid4())
    process = Process(target=download_worker, args=(job_id, url, filename, data.get('format', 'mp4'), data.get('quality', 'best')))

    # Initialize job state before starting
    JOBS[job_id] = {'status': 'pending', 'message': 'Your download is preparing.'}
    process.start()

    # Update job state with the PID
    JOBS[job_id].update({'pid': process.pid})

    logging.info(f"Started download job {job_id} with PID {process.pid} for URL: {url}")
    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def status_route(job_id):
    job = JOBS.get(job_id)
    if not job: return jsonify({'status': 'error', 'message': 'Job not found.'}), 404

    status = job.get('status')
    if status == 'completed':
        download_url = f"/downloads/{job.get('filename')}"
        return jsonify({'status': 'completed', 'download_url': download_url})

    return jsonify({'status': status, 'message': job.get('message', '')})

@app.route('/cancel/<job_id>')
def cancel_route(job_id):
    job_info = JOBS.get(job_id)
    if not job_info:
        return jsonify({'status': 'error', 'message': 'Job not found.'}), 404

    pid = job_info.get('pid')
    if not pid or job_info.get('status') not in ['pending', 'running']:
        return jsonify({'status': 'error', 'message': 'Job is not in a cancellable state.'}), 400

    try:
        os.kill(pid, signal.SIGTERM)
        JOBS[job_id].update({'status': 'cancelled', 'message': 'Download has been cancelled.'})
        logging.info(f"Cancelled job {job_id} with PID {pid}.")
        return jsonify({'status': 'cancelled'})
    except ProcessLookupError:
        logging.warning(f"Attempted to cancel job {job_id} (PID {pid}), but process was not found.")
        JOBS[job_id].update({'status': 'failed', 'message': 'Process not found, it may have crashed.'})
        return jsonify({'status': 'error', 'message': 'Process not found.'}), 404
    except Exception as e:
        logging.error(f"Error cancelling job {job_id} (PID {pid}): {e}")
        return jsonify({'status': 'error', 'message': f'An error occurred: {e}'}), 500

@app.route('/downloads/<path:filename>')
def serve_download(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
