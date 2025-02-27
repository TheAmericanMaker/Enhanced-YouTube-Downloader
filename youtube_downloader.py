import yt_dlp
import os
from typing import Optional, Callable, Dict, Any, List, Union
from dataclasses import dataclass
from tqdm import tqdm
import logging
from colorama import init, Fore, Style
from queue import Queue
from threading import Thread
import time

# Initialize colorama for cross-platform color support
init()

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

@dataclass
class QueueItem:
    url: str
    quality: str = 'best'
    audio_only: bool = False
    status: str = 'pending'  # pending, downloading, completed, failed

class YouTubeDownloader:
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
        
        self.download_queue = Queue()
        self.queue_items = []
        self.is_processing = False

    def print_status(self, message: str, status_type: str = 'info'):
        """Print colored status messages"""
        colors = {
            'info': Fore.BLUE,
            'success': Fore.GREEN,
            'error': Fore.RED,
            'warning': Fore.YELLOW
        }
        print(f"{colors.get(status_type, '')}{message}{Style.RESET_ALL}")

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Fetch video/playlist information without downloading"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            self.logger.error(f"Error fetching video info: {str(e)}")
            return None

    def list_formats(self, url: str) -> List[Dict[str, Any]]:
        """List all available formats for a video"""
        info = self.get_video_info(url)
        if info and 'formats' in info:
            return info['formats']
        return []

    def create_progress_bar(self, d: Dict[str, Any]) -> None:
        """Create and update download progress bar using tqdm"""
        if d['status'] == 'downloading':
            if not hasattr(self, '_progress_bar'):
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                self._progress_bar = tqdm(
                    total=total,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=d.get('filename', ''),
                    leave=True,
                    ncols=100,
                    bar_format='\r{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
                )
            
            downloaded = d.get('downloaded_bytes', 0)
            self._progress_bar.update(downloaded - self._progress_bar.n)
            
        elif d['status'] == 'finished' and hasattr(self, '_progress_bar'):
            self._progress_bar.close()
            delattr(self, '_progress_bar')

    def download(self, url: str, options: DownloadOptions) -> bool:
        """Enhanced download method with support for all features"""
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

        # Add progress hook
        download_options['progress_hooks'] = [self.create_progress_bar]

        # Only show URL and initial download path
        print(f"Download URL: {url}")
        print(f"Downloading to: {download_options['outtmpl']}")
        print()  # Blank line before progress

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

        # After download completes, show the actual filename that was downloaded
        actual_filename = os.path.basename(download_options['outtmpl'])
        print(f"\nDownloaded: {actual_filename}")
        return True

    def process_queue(self):
        """Process the download queue in a separate thread"""
        self.is_processing = True
        while not self.download_queue.empty():
            item = self.download_queue.get()
            self.print_status(f"Processing: {item.url}", 'info')
            item.status = 'downloading'
            
            options = DownloadOptions(
                quality=item.quality,
                output_path="~/Downloads",
                audio_only=item.audio_only
            )
            
            success = self.download(item.url, options)
            item.status = 'completed' if success else 'failed'
            
            self.download_queue.task_done()
        self.is_processing = False

    def show_queue_status(self):
        """Display the current queue status"""
        if not self.queue_items:
            self.print_status("Queue is empty", 'info')
            return

        print("\nDownload Queue Status:")
        for i, item in enumerate(self.queue_items, 1):
            status_colors = {
                'pending': Fore.YELLOW,
                'downloading': Fore.BLUE,
                'completed': Fore.GREEN,
                'failed': Fore.RED
            }
            color = status_colors.get(item.status, '')
            print(f"{i}. {color}{item.url} - {item.status}{Style.RESET_ALL}")

def interactive_cli():
    """Enhanced interactive CLI interface"""
    downloader = YouTubeDownloader()
    
    def print_help():
        print(f"\n{Fore.CYAN}Available commands:{Style.RESET_ALL}")
        print("  download <url> [quality] - Download video")
        print("  audio <url>             - Download audio only")
        print("  queue <url> [quality]   - Add to download queue")
        print("  start-queue            - Start processing queue")
        print("  show-queue             - Show queue status")
        print("  clear-queue            - Clear download queue")
        print("  formats <url>           - List available formats")
        print("  batch <file>           - Load URLs from file")
        print("  help                    - Show this help")
        print("  quit                    - Exit program")

    downloader.print_status("YouTube Downloader Interactive CLI", 'info')
    print("Type 'help' for available commands")

    while True:
        try:
            command = input(f"\n{Fore.GREEN}Enter command:{Style.RESET_ALL} ").strip().split()
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
            elif command[0] == "queue" and len(command) > 1:
                url = command[1]
                quality = command[2] if len(command) > 2 else 'best'
                item = QueueItem(url=url, quality=quality)
                downloader.queue_items.append(item)
                downloader.download_queue.put(item)
                downloader.print_status(f"Added to queue: {url}", 'success')
            elif command[0] == "start-queue":
                if not downloader.is_processing:
                    Thread(target=downloader.process_queue, daemon=True).start()
                    downloader.print_status("Queue processing started", 'info')
                else:
                    downloader.print_status("Queue is already processing", 'warning')
            elif command[0] == "show-queue":
                downloader.show_queue_status()
            elif command[0] == "clear-queue":
                while not downloader.download_queue.empty():
                    downloader.download_queue.get()
                downloader.queue_items.clear()
                downloader.print_status("Queue cleared", 'info')
            elif command[0] == "batch" and len(command) > 1:
                try:
                    with open(command[1], 'r') as f:
                        urls = [line.strip() for line in f if line.strip()]
                        for url in urls:
                            item = QueueItem(url=url)
                            downloader.queue_items.append(item)
                            downloader.download_queue.put(item)
                        downloader.print_status(f"Added {len(urls)} URLs from {command[1]}", 'success')
                except FileNotFoundError:
                    downloader.print_status(f"File not found: {command[1]}", 'error')
            elif command[0] == "download" and len(command) > 1:
                url = command[1]
                quality = command[2] if len(command) > 2 else 'best'
                options = DownloadOptions(quality=quality, output_path="~/Downloads")
                if downloader.download(url, options):
                    downloader.print_status("Download completed successfully!", 'success')
                else:
                    downloader.print_status("Download failed!", 'error')
            elif command[0] == "audio" and len(command) > 1:
                url = command[1]
                options = DownloadOptions(audio_only=True, output_path="~/Downloads")
                if downloader.download(url, options):
                    downloader.print_status("Audio download completed successfully!", 'success')
                else:
                    downloader.print_status("Audio download failed!", 'error')
            else:
                print("Invalid command. Type 'help' for usage.")

        except KeyboardInterrupt:
            downloader.print_status("\nUse 'quit' to exit properly", 'warning')
        except Exception as e:
            downloader.print_status(f"Error: {str(e)}", 'error')

def download_video(url, output_path):
    try:
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        
        # Show initial information
        print(f"Download URL: {url}")
        print(f"Downloading to: {output_path}")
        print()
        
        # Get the filesize for the progress bar
        filesize = stream.filesize
        
        with tqdm(
            total=filesize,  # Use filesize instead of total_size
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
            desc="",
            leave=True,
            ncols=100,
            bar_format='{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        ) as pbar:
            # Download with progress callback
            stream.download(
                output_path=os.path.dirname(output_path),
                filename=os.path.basename(output_path),
                progress_callback=lambda chunk, file_handle, bytes_remaining: pbar.update(len(chunk))
            )
            
        actual_filename = stream.default_filename
        print(f"\nDownloaded: {actual_filename}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    interactive_cli()