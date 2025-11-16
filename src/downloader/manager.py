import os
import uuid
import shutil
import zipfile
import yt_dlp
from yt_dlp.utils import ExtractorError, DownloadError

DOWNLOAD_DIR = "/tmp/downloads"

class DownloadManager:
    def __init__(self, download_path=DOWNLOAD_DIR):
        self.download_path = download_path
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)

    def search(self, query):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'default_search': f'ytsearch5:{query}',
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(None, download=False)
                entries = result.get('entries', [])
                sanitized_entries = [self._sanitize_entry(entry) for entry in entries]
                return {'entries': sanitized_entries}
        except Exception as e:
            return {'error': str(e)}

    def get_info(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'extract_flat': 'in_playlist',
            'extractor_args': {'youtube': {'player_client': ['android']}},
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self._sanitize_info(info)
        except ExtractorError:
            return {'error': "The content is private and cannot be downloaded without cookies."}
        except Exception as e:
            return {'error': str(e)}

    def _sanitize_info(self, info):
        if 'entries' in info:
            return {
                'type': 'playlist',
                'title': info.get('title'),
                'uploader': info.get('uploader'),
                'entries': [self._sanitize_entry(entry) for entry in info.get('entries', [])]
            }
        return self._sanitize_entry(info)

    def _sanitize_entry(self, entry):
        return {
            'type': 'video',
            'title': entry.get('title'),
            'uploader': entry.get('uploader'),
            'thumbnail': entry.get('thumbnail', 'https://i.imgur.com/3h2tS2A.png'),
            'duration': entry.get('duration'),
            'id': entry.get('id'),
            'webpage_url': entry.get('webpage_url'),
        }

    def download_media(self, url, format_choice='mp4', quality='best', is_playlist=False):
        if is_playlist:
            return self._download_playlist(url, format_choice, quality)
        else:
            return self._download_single_video(url, format_choice, quality)

    def _download_single_video(self, url, format_choice, quality):
        unique_id = str(uuid.uuid4())
        # Use a unique filename that is harder to guess
        output_template = os.path.join(self.download_path, f"{unique_id}.%(ext)s")

        ydl_opts = self._get_ydl_opts(format_choice, quality)
        ydl_opts['outtmpl'] = output_template

        self.final_filename = None
        ydl_opts['progress_hooks'] = [lambda d: self._hook(d)]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # Sanitize the final filename for the user
                final_user_filename = ydl.prepare_filename(info).replace(f'{unique_id}.', f'{info.get("title", "download")}.')

                # Rename the file on the server
                server_filepath = self.final_filename
                if server_filepath and os.path.exists(server_filepath):
                    final_server_path = os.path.join(self.download_path, os.path.basename(final_user_filename))
                    shutil.move(server_filepath, final_server_path)
                    return {'status': 'success', 'filename': os.path.basename(final_server_path)}
            return {'status': 'error', 'message': 'Could not determine final filename.'}
        except (DownloadError, ExtractorError):
            return {'status': 'error', 'message': "The content is private or unavailable."}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _download_playlist(self, url, format_choice, quality):
        unique_id = str(uuid.uuid4())
        playlist_download_dir = os.path.join(self.download_path, unique_id)
        os.makedirs(playlist_download_dir, exist_ok=True)

        ydl_opts = self._get_ydl_opts(format_choice, quality)
        ydl_opts['outtmpl'] = os.path.join(playlist_download_dir, '%(title)s.%(ext)s')

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                playlist_title = info.get('title', 'playlist')
                zip_filename = f"{playlist_title}.zip"
                zip_filepath = os.path.join(self.download_path, zip_filename)

                # Create a zip file of the downloaded content
                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, _, files in os.walk(playlist_download_dir):
                        for file in files:
                            zipf.write(os.path.join(root, file), arcname=file)

                # Clean up the temporary directory
                shutil.rmtree(playlist_download_dir)

                return {'status': 'success', 'filename': zip_filename}

        except Exception as e:
            # Clean up in case of error
            if os.path.exists(playlist_download_dir):
                shutil.rmtree(playlist_download_dir)
            return {'status': 'error', 'message': str(e)}

    def _get_ydl_opts(self, format_choice, quality):
        ydl_opts = {
            'extractor_args': {'youtube': {'player_client': ['android']}},
            'retries': 5,
        }
        if format_choice in ['mp3', 'wav', 'm4a']:
            quality_map = {
                'high': 'bestaudio/best',
                'medium': 'bestaudio[abr<=192]/best',
                'low': 'bestaudio[abr<=128]/best',
            }
            ydl_opts.update({
                'format': quality_map.get(quality, 'bestaudio/best'),
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': format_choice}],
            })
        else: # Video formats like MP4
            quality_map = {
                'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
                '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',
            }
            ydl_opts['format'] = quality_map.get(quality, 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best')
        return ydl_opts

    def _hook(self, d):
        if d['status'] == 'finished':
            self.final_filename = d.get('filename')
