"""Tests for enhanced_youtube_downloader.downloader (yt-dlp is mocked)."""

from __future__ import annotations

import pytest

from enhanced_youtube_downloader.downloader import (
    DownloadResult,
    YouTubeDownloader,
    validate_url,
)
from enhanced_youtube_downloader.options import (
    DEFAULT_FILENAME_TEMPLATE,
    DownloadOptions,
    QualityError,
)


class TestValidateUrl:
    def test_accepts_http_and_https(self):
        url = "https://www.youtube.com/watch?v=x"
        assert validate_url(url) == url
        assert validate_url("  http://youtu.be/x  ") == "http://youtu.be/x"

    @pytest.mark.parametrize("url", ["ftp://example.com/x", "not a url", "https://", ""])
    def test_rejects_bad_urls(self, url):
        with pytest.raises(ValueError):
            validate_url(url)

    def test_rejects_non_string(self):
        with pytest.raises(ValueError):
            validate_url(123)


class TestBuildYdlOptions:
    def test_default_video(self, tmp_path):
        options = YouTubeDownloader().build_ydl_options(DownloadOptions(output_path=str(tmp_path)))
        assert options["format"] == "bestvideo+bestaudio/best"
        assert options["noprogress"] is True
        assert options["quiet"] is True
        assert str(tmp_path) in options["outtmpl"]
        assert "postprocessors" not in options

    def test_no_output_path_keeps_plain_template(self):
        options = YouTubeDownloader().build_ydl_options(DownloadOptions())
        assert options["outtmpl"] == DEFAULT_FILENAME_TEMPLATE

    def test_quality(self):
        options = YouTubeDownloader().build_ydl_options(DownloadOptions(quality="720p"))
        assert "height<=720" in options["format"]

    def test_audio_only(self, tmp_path):
        options = YouTubeDownloader().build_ydl_options(
            DownloadOptions(
                output_path=str(tmp_path),
                audio_only=True,
                audio_format="opus",
                audio_quality="128",
            )
        )
        assert options["format"] == "bestaudio/best"
        post = options["postprocessors"][0]
        assert post["key"] == "FFmpegExtractAudio"
        assert post["preferredcodec"] == "opus"
        assert post["preferredquality"] == "128"

    def test_subtitles(self):
        options = YouTubeDownloader().build_ydl_options(
            DownloadOptions(download_subtitles=True, subtitle_languages=["en", "de"])
        )
        assert options["writesubtitles"] is True
        assert options["subtitleslangs"] == ["en", "de"]
        assert {"key": "FFmpegEmbedSubtitle"} in options["postprocessors"]

    def test_subtitles_audio_only_skip_embed(self):
        options = YouTubeDownloader().build_ydl_options(
            DownloadOptions(audio_only=True, download_subtitles=True)
        )
        assert options["writesubtitles"] is True
        assert all(pp["key"] != "FFmpegEmbedSubtitle" for pp in options["postprocessors"])

    def test_thumbnails(self):
        options = YouTubeDownloader().build_ydl_options(DownloadOptions(download_thumbnails=True))
        assert options["writethumbnail"] is True
        assert options["embedthumbnail"] is True
        assert any(pp["key"] == "FFmpegThumbnailsConvertor" for pp in options["postprocessors"])

    def test_thumbnails_audio_only_skip_embed(self):
        options = YouTubeDownloader().build_ydl_options(
            DownloadOptions(audio_only=True, download_thumbnails=True)
        )
        assert options["writethumbnail"] is True
        assert "embedthumbnail" not in options

    def test_playlist(self):
        options = YouTubeDownloader().build_ydl_options(
            DownloadOptions(playlist=True, playlist_items="1-3")
        )
        assert options["playlist_items"] == "1-3"
        assert options["ignoreerrors"] is True
        assert options["noplaylist"] is False
        assert "%(playlist_title" in options["outtmpl"]

    def test_single_video_uses_noplaylist(self):
        options = YouTubeDownloader().build_ydl_options(DownloadOptions())
        assert options["noplaylist"] is True
        assert options["ignoreerrors"] is False

    def test_output_path_tilde_expansion(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        options = YouTubeDownloader().build_ydl_options(DownloadOptions(output_path="~/downloads"))
        assert str(tmp_path) in options["outtmpl"]

    def test_retries_passthrough(self):
        options = YouTubeDownloader().build_ydl_options(DownloadOptions(retries=7))
        assert options["retries"] == 7

    def test_invalid_options_raise(self):
        with pytest.raises(QualityError):
            YouTubeDownloader().build_ydl_options(DownloadOptions(quality="sparkly"))


class TestDownload:
    def test_success(self, fake_yt_dlp, tmp_path):
        downloader = YouTubeDownloader(progress=True)
        result = downloader.download(
            "https://www.youtube.com/watch?v=abc",
            DownloadOptions(output_path=str(tmp_path)),
        )
        assert result.ok is True
        assert result.error is None
        assert result.filename == "Fake Title [abc123].mp4"
        assert len(fake_yt_dlp.instances) == 1
        assert fake_yt_dlp.instances[0].params["progress_hooks"]

    def test_failure_returns_result(self, fake_yt_dlp):
        fake_yt_dlp.raise_download_error = RuntimeError("network down")
        result = YouTubeDownloader(progress=False).download("https://www.youtube.com/watch?v=abc")
        assert isinstance(result, DownloadResult)
        assert result.ok is False
        assert "network down" in result.error

    def test_invalid_url_raises(self, fake_yt_dlp):
        with pytest.raises(ValueError):
            YouTubeDownloader().download("ftp://example.com/x")

    def test_invalid_options_raise(self, fake_yt_dlp):
        with pytest.raises(QualityError):
            YouTubeDownloader().download(
                "https://www.youtube.com/watch?v=x", DownloadOptions(quality="nope")
            )


class TestInfo:
    def test_list_formats(self, fake_yt_dlp):
        fake_yt_dlp.info_override = {"formats": [{"format_id": "137"}, {"format_id": "250"}]}
        formats = YouTubeDownloader().list_formats("https://www.youtube.com/watch?v=x")
        assert [f["format_id"] for f in formats] == ["137", "250"]

    def test_list_formats_empty(self, fake_yt_dlp):
        assert YouTubeDownloader().list_formats("https://www.youtube.com/watch?v=x") == []

    def test_info_error_returns_none(self, fake_yt_dlp):
        fake_yt_dlp.raise_info_error = RuntimeError("extractor error")
        assert YouTubeDownloader().get_video_info("https://www.youtube.com/watch?v=x") is None

    def test_bad_url_raises(self, fake_yt_dlp):
        with pytest.raises(ValueError):
            YouTubeDownloader().get_video_info("nope")
