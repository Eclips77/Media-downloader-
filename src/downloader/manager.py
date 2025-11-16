import os
import random
import yt_dlp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DownloadManager:
    def __init__(self, proxy=None, cookies_file=None):
        self.proxy = proxy
        self.cookies_file = cookies_file
        self._user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
        ]

    def _get_base_ydl_opts(self):
        """Constructs the base yt-dlp options dictionary with proxy, cookies, and browser simulation."""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'force_ipv4': True,
            'http_headers': {
                'User-Agent': random.choice(self._user_agents),
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }
        if self.proxy:
            opts['proxy'] = self.proxy
            logger.info(f"Using proxy: {self.proxy}")
        if self.cookies_file and os.path.exists(self.cookies_file):
            opts['cookiefile'] = self.cookies_file
            logger.info(f"Using cookies file: {self.cookies_file}")
        else:
            # Fallback to Android client simulation if no cookies are provided
            opts.setdefault('extractor_args', {}).setdefault('youtube', {}).setdefault('player_client', []).extend(['android'])

        return opts

    def get_info(self, url):
        """Fetches video or playlist information."""
        ydl_opts = self._get_base_ydl_opts()
        ydl_opts['extract_flat'] = 'in_playlist'

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return self._sanitize_info(info)
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"DownloadError fetching info for {url}: {e}")
            return {'error': f"Failed to fetch info. The content may be private, age-restricted, or blocked in your region. Original error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error fetching info for {url}: {e}")
            return {'error': str(e)}

    def download_media(self, url, download_dir, output_filename, format_choice='mp4', quality='best'):
        """Downloads a single video or an entire playlist with the specified options."""
        base_ydl_opts = self._get_base_ydl_opts()

        # Build format selector
        format_selector = self._get_format_selector(format_choice, quality)
        base_ydl_opts['format'] = format_selector

        # Configure post-processors for audio extraction
        if format_choice in ['mp3', 'wav', 'm4a']:
            base_ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_choice,
            }]

        # Set the output template
        output_template = os.path.join(download_dir, f"{output_filename}.%(ext)s")
        base_ydl_opts['outtmpl'] = output_template

        logger.info(f"Starting download for URL: {url} to {output_template}")

        try:
            with yt_dlp.YoutubeDL(base_ydl_opts) as ydl:
                ydl.download([url])

            # Find the downloaded file since we don't know the exact extension beforehand
            for f in os.listdir(download_dir):
                if f.startswith(output_filename):
                    final_filepath = os.path.join(download_dir, f)
                    logger.info(f"Download successful. File saved at: {final_filepath}")
                    return {'status': 'success', 'filepath': final_filepath}

            # This should ideally not be reached
            return {'status': 'error', 'message': 'Download finished but output file not found.'}

        except yt_dlp.utils.DownloadError as e:
            logger.error(f"DownloadError during download of {url}: {e}")
            return {'status': 'error', 'message': f"Download failed. The content is likely blocked or private. Please try a different proxy or cookies. Original error: {e}"}
        except Exception as e:
            logger.error(f"Unexpected error during download of {url}: {e}")
            return {'status': 'error', 'message': str(e)}

    def _get_format_selector(self, format_choice, quality):
        """Returns the appropriate yt-dlp format selector string."""
        if format_choice in ['mp3', 'wav', 'm4a']:  # Audio formats
            quality_map = {
                'best': 'bestaudio/best',
                'high': 'bestaudio[abr>=192]/best',
                'medium': 'bestaudio[abr<=192]/best',
                'low': 'bestaudio[abr<=128]/best',
            }
            return quality_map.get(quality, 'bestaudio/best')
        else:  # Video formats
            quality_map = {
                'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
                '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best',
            }
            return quality_map.get(quality, 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best')

    def _sanitize_info(self, info):
        """Sanitizes the info dict to return only the necessary fields."""
        if 'entries' in info:
            return {
                'type': 'playlist',
                'title': info.get('title'),
                'uploader': info.get('uploader'),
                'entries': [self._sanitize_entry(entry) for entry in info.get('entries', [])]
            }
        return self._sanitize_entry(info)

    def _sanitize_entry(self, entry):
        """Sanitizes a single entry (video)."""
        return {
            'type': 'video',
            'title': entry.get('title', 'N/A'),
            'uploader': entry.get('uploader', 'N/A'),
            'thumbnail': entry.get('thumbnail', '/static/img/placeholder.png'),
            'duration': entry.get('duration', 0),
            'id': entry.get('id'),
            'webpage_url': entry.get('webpage_url'),
        }
