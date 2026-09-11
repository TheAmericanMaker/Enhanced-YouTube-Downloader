"""Tests for enhanced_youtube_downloader.options."""

from __future__ import annotations

import pytest

from enhanced_youtube_downloader.options import (
    AUDIO_FORMATS,
    DownloadOptions,
    QualityError,
    format_selector,
    parse_langs,
    parse_quality,
)


class TestParseQuality:
    @pytest.mark.parametrize("raw", ["best", "Best", " BEST ", "worst", "WORST"])
    def test_special_qualities(self, raw):
        assert parse_quality(raw) in ("best", "worst")

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("1080p", "1080p"), ("720P", "720p"), (" 480p ", "480p"), ("144p", "144p")],
    )
    def test_height_qualities(self, raw, expected):
        assert parse_quality(raw) == expected

    @pytest.mark.parametrize("raw", ["", "abc", "720", "p", "1080", "0p", "143p", None, 1080])
    def test_invalid(self, raw):
        with pytest.raises(QualityError):
            parse_quality(raw)


class TestFormatSelector:
    def test_best(self):
        assert format_selector("best") == "bestvideo+bestaudio/best"

    def test_worst(self):
        assert format_selector("worst") == "worst"

    def test_height(self):
        selector = format_selector("720p")
        assert selector.startswith("bestvideo[height<=720]")
        assert "bestaudio" in selector

    def test_invalid_raises(self):
        with pytest.raises(QualityError):
            format_selector("blurry")


class TestParseLangs:
    def test_comma_separated(self):
        assert parse_langs("en,de") == ["en", "de"]

    def test_space_separated(self):
        assert parse_langs("en de fr") == ["en", "de", "fr"]

    def test_mixed_with_extra_whitespace(self):
        assert parse_langs("en,  de ,   fr") == ["en", "de", "fr"]

    def test_empty(self):
        assert parse_langs("") == []


class TestDownloadOptions:
    def test_defaults(self):
        options = DownloadOptions()
        assert options.quality == "best"
        assert options.output_path is None
        assert options.audio_only is False
        assert options.audio_format == "mp3"
        assert options.audio_quality == "192"
        assert options.retries == 3
        assert options.embed_metadata is True
        assert options.subtitle_languages == ["en"]
        assert options.filename_template

    def test_validate_returns_self(self):
        options = DownloadOptions()
        assert options.validate() is options

    def test_validate_bad_quality(self):
        with pytest.raises(QualityError):
            DownloadOptions(quality="ultra").validate()

    def test_validate_bad_audio_format(self):
        with pytest.raises(ValueError, match="audio format"):
            DownloadOptions(audio_only=True, audio_format="avi").validate()

    def test_validate_all_audio_formats(self):
        for fmt in AUDIO_FORMATS:
            assert DownloadOptions(audio_only=True, audio_format=fmt).validate()

    def test_validate_retries(self):
        with pytest.raises(ValueError, match="retries"):
            DownloadOptions(retries=0).validate()

    def test_validate_empty_template(self):
        with pytest.raises(ValueError, match="filename_template"):
            DownloadOptions(filename_template="   ").validate()

    def test_validate_empty_subtitle_langs(self):
        with pytest.raises(ValueError, match="subtitle_languages"):
            DownloadOptions(download_subtitles=True, subtitle_languages=[]).validate()

    def test_subtitle_languages_default_is_not_shared(self):
        first = DownloadOptions()
        first.subtitle_languages.append("de")
        second = DownloadOptions()
        assert second.subtitle_languages == ["en"]
