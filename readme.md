# Enhanced YouTube Downloader

A Python-based command line tool for downloading YouTube videos with advanced features. This tool supports downloading videos at various quality settings, extracting audio, downloading entire playlists, fetching available formats, and even downloading subtitles and thumbnails.

## Features

- **Download Videos**: Retrieve high-quality YouTube videos with customizable quality (e.g., 1080p, 720p).
- **Audio Only Mode**: Extract audio tracks from videos and convert them to MP3.
- **List Formats**: Get a list of available download formats for any video.
- **Playlist Support**: Download complete playlists by providing a playlist URL.
- **Subtitles & Thumbnails**: Optionally download subtitles and thumbnails, with options for embedding.
- **Progress Bar**: Real-time download progress displayed using the `tqdm` progress bar.
- **Logging**: Detailed logging for tracking download progress and troubleshooting.
- **Configurable Options**: Easily adjust quality, output path, retry attempts, file naming conventions, and more via a configurable options dataclass.

## Requirements

- **Python 3.7+**
- [**yt-dlp**](https://github.com/yt-dlp/yt-dlp)
- [**tqdm**](https://github.com/tqdm/tqdm)
- [**FFmpeg**](https://ffmpeg.org/) (required for audio extraction and additional post-processing)

## Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/yourusername/Enhanced-YouTube-Downloader.git
cd Enhanced-YouTube-Downloader
pip install yt-dlp tqdm
```

> **Note:** To use audio extraction and embed subtitles, ensure that [FFmpeg](https://ffmpeg.org/) is installed and available in your system's PATH.

## Usage

Run the interactive command line interface:

```bash
python youtube_downloader.py
```

Once running, you can use the following commands:

- **download `<url>` [quality]**  
  Download a video from the specified YouTube URL. Optionally, specify a quality (e.g., `720p`, `1080p`).

- **audio `<url>`**  
  Download the audio track only (saved as MP3) from the specified video.

- **formats `<url>`**  
  List all available formats for the given YouTube video.

- **playlist `<url>`**  
  Download an entire playlist using the provided playlist URL.

- **help**  
  Display the list of available commands.

- **quit**  
  Exit the application.

### Example

```bash
Enter command: download https://www.youtube.com/watch?v=example 1080p
```

This command will download the video from the given URL at 1080p quality.

## Code Overview

The project is encapsulated in a single file, `youtube_downloader.py`, which includes:

- **DownloadOptions Dataclass**: Stores various configuration options such as video quality, output path, and flags for audio-only mode, subtitles, thumbnails, and playlist downloads.
- **YouTubeDownloader Class**:  
  - Sets up logging and default configurations.
  - Provides methods to fetch video information, list available formats, manage download progress with a `tqdm` progress bar, and execute downloads with support for retries.
- **Interactive CLI**: A user-friendly command line interface that processes user commands (download, audio, formats, playlist, help, quit) and interacts with the downloader.

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! If you have ideas for improvements, new features, or bug fixes, please open an issue or submit a pull request.

## Disclaimer

This tool is intended for personal use only. Please ensure you comply with YouTube's terms of service when downloading videos. The author is not responsible for any misuse of this tool.

---

Enjoy using the Enhanced YouTube Downloader and happy downloading!