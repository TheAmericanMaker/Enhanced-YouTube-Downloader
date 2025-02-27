import yt_dlp
import os
from typing import Optional, Callable, Dict, Any, List, Union
from dataclasses import dataclass
from tqdm import tqdm
import logging

@dataclass
class DownloadOptions:
    """Configuration options for download"""
    quality: str = 'best'
    output_path: Optional[str] = None
    audio_only: bool = False
    audio_format: str = 'mp3'
    audio_quality: str = '192'
    download_thumbnails: bool = False
    download_subtitles: bool = False
    subtitle_languages: List[str] = None
    playlist: bool = False
    playlist_items: Optional[str] = None
    retries: int = 3
    embed_metadata: bool = True
    filename_template: str = '%(title)s.%(ext)s'

class YouTubeDownloader:
    """Enhanced YouTube downloader with advanced features"""
    
    def __init__(self):
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Base configuration
        self.default_options = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'writethumbnail': False,
            'writesubtitles': False,
            'embedthumbnail': True,
            'embedmetadata': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        Fetch video/playlist information without downloading
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            self.logger.error(f"Error fetching video info: {str(e)}")
            return None

    def list_formats(self, url: str) -> List[Dict[str, Any]]:
        """
        List all available formats for a video
        """
        info = self.get_video_info(url)
        if info and 'formats' in info:
            return info['formats']
        return []

    def create_progress_bar(self, d: Dict[str, Any]) -> None:
        """
        Create and update download progress bar using tqdm
        """
        if d['status'] == 'downloading':
            if not hasattr(self, '_progress_bar'):
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                self._progress_bar = tqdm(
                    total=total,
                    unit='iB',
                    unit_scale=True,
                    desc=f"Downloading {d.get('filename', '')}"
                )
            
            downloaded = d.get('downloaded_bytes', 0)
            self._progress_bar.update(downloaded - self._progress_bar.n)
            
        elif d['status'] == 'finished' and hasattr(self, '_progress_bar'):
            self._progress_bar.close()
            delattr(self, '_progress_bar')

    def download(self, url: str, options: DownloadOptions) -> bool:
        """
        Enhanced download method with support for all features
        """
        download_options = self.default_options.copy()
        
        # Configure output path
        if options.output_path:
            try:
                os.makedirs(options.output_path, exist_ok=True)
                if not os.access(options.output_path, os.W_OK):
                    self.logger.error(f"No write permission for directory: {options.output_path}")
                    return False
                download_options['outtmpl'] = os.path.join(options.output_path, options.filename_template)
            except Exception as e:
                self.logger.error(f"Error with output directory: {str(e)}")
                return False

        # Audio configuration
        if options.audio_only:
            download_options.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': options.audio_format,
                    'preferredquality': options.audio_quality,
                }]
            })
        # Video quality configuration
        elif options.quality.endswith('p'):
            try:
                resolution = int(options.quality[:-1])
                download_options['format'] = f"bestvideo[height<={resolution}]+bestaudio/best"
            except ValueError:
                download_options['format'] = 'best'

        # Subtitle configuration
        if options.download_subtitles:
            download_options.update({
                'writesubtitles': True,
                'subtitleslangs': options.subtitle_languages or ['en'],
                'postprocessors': download_options.get('postprocessors', []) + [
                    {'key': 'FFmpegEmbedSubtitle'}
                ]
            })

        # Thumbnail configuration
        if options.download_thumbnails:
            download_options['writethumbnail'] = True
            if not options.audio_only:
                download_options['postprocessors'] = download_options.get('postprocessors', []) + [
                    {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'}
                ]

        # Playlist configuration
        if options.playlist:
            download_options['playlist'] = True
            if options.playlist_items:
                download_options['playlist_items'] = options.playlist_items

        # Add progress hook
        download_options['progress_hooks'] = [self.create_progress_bar]

        # Attempt download with retries
        for attempt in range(options.retries):
            try:
                with yt_dlp.YoutubeDL(download_options) as ydl:
                    ydl.download([url])
                return True
            except Exception as e:
                self.logger.error(f"Download attempt {attempt + 1} failed: {str(e)}")
                if attempt == options.retries - 1:
                    return False
                continue

def interactive_cli():
    """Interactive CLI interface for the downloader"""
    downloader = YouTubeDownloader()
    
    def print_help():
        print("\nAvailable commands:")
        print("  download <url> [quality] - Download video (quality: best, 720p, 1080p, etc)")
        print("  audio <url>             - Download audio only (MP3)")
        print("  formats <url>           - List available formats")
        print("  playlist <url>          - Download entire playlist")
        print("  help                    - Show this help")
        print("  quit                    - Exit program")

    print("YouTube Downloader Interactive CLI")
    print("Type 'help' for available commands")

    while True:
        try:
            command = input("\nEnter command: ").strip().split()
            if not command:
                continue

            if command[0] == "quit":
                break
            elif command[0] == "help":
                print_help()
            elif command[0] == "formats" and len(command) > 1:
                formats = downloader.list_formats(command[1])
                print("\nAvailable formats:")
                for f in formats:
                    print(f"Format: {f.get('format_id', 'N/A')}, "
                          f"Resolution: {f.get('resolution', 'N/A')}, "
                          f"Extension: {f.get('ext', 'N/A')}")
            elif command[0] in ["download", "audio", "playlist"] and len(command) > 1:
                url = command[1]
                quality = command[2] if len(command) > 2 else 'best'
                options = DownloadOptions(
                    quality=quality,
                    output_path="~/Downloads",
                    audio_only=(command[0] == "audio"),
                    playlist=(command[0] == "playlist")
                )
                if downloader.download(url, options):
                    print("\nDownload completed successfully!")
                else:
                    print("\nDownload failed!")
            else:
                print("Invalid command. Type 'help' for usage.")

        except KeyboardInterrupt:
            print("\nUse 'quit' to exit properly")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    interactive_cli() 