"""Tests for enhanced_youtube_downloader.options."""

from __future__ import annotations

import pytest

from enhanced_youtube_downloader.options import (
    AUDIO_FORMATS,
    BROWSERS,
    DownloadOptions,
    QualityError,
    format_selector,
    parse_browser,
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


class TestParseBrowser:
    @pytest.mark.parametrize("browser", sorted(BROWSERS))
    def test_valid_browsers(self, browser):
        assert parse_browser(browser) == browser

    def test_case_insensitive_and_stripped(self):
        assert parse_browser("  Chrome ") == "chrome"

    def test_profile_preserved(self):
        assert parse_browser("chrome+Default") == "chrome+Default"

    def test_profile_case_insensitive_browser(self):
        assert parse_browser("CHROME+MyProfile") == "chrome+MyProfile"

    def test_invalid_browser(self):
        with pytest.raises(ValueError, match="unsupported browser"):
            parse_browser("ie6")

    def test_invalid_browser_with_profile(self):
        with pytest.raises(ValueError, match="unsupported browser"):
            parse_browser("ie6+Default")

    def test_empty(self):
        with pytest.raises(ValueError, match="must not be empty"):
            parse_browser("   ")

    def test_non_string(self):
        with pytest.raises(ValueError, match="must be a string"):
            parse_browser(42)  # type: ignore[arg-type]


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
        assert options.cookie_file is None
        assert options.cookies_from_browser is None
        assert options.proxy is None
        assert options.concurrent_fragments is None
        assert options.no_overwrites is False
        assert options.write_auto_subs is False

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

    def test_cookie_file_only_is_fine(self):
        assert DownloadOptions(cookie_file="/tmp/c.txt").validate()

    def test_cookies_from_browser_only_is_fine(self):
        assert DownloadOptions(cookies_from_browser="firefox").validate()

    def test_cookies_from_browser_with_profile_is_fine(self):
        assert DownloadOptions(cookies_from_browser="chrome+Work").validate()

    def test_both_cookie_sources_conflict(self):
        with pytest.raises(ValueError, match="at most one"):
            DownloadOptions(cookie_file="/tmp/c.txt", cookies_from_browser="chrome").validate()

    def test_cookies_from_browser_invalid_browser(self):
        with pytest.raises(ValueError, match="unsupported browser"):
            DownloadOptions(cookies_from_browser="netscape").validate()

    def test_concurrent_fragments_zero_invalid(self):
        with pytest.raises(ValueError, match="concurrent_fragments"):
            DownloadOptions(concurrent_fragments=0).validate()

    def test_concurrent_fragments_positive_is_fine(self):
        assert DownloadOptions(concurrent_fragments=8).validate()

    def test_proxy_whitespace_invalid(self):
        with pytest.raises(ValueError, match="proxy"):
            DownloadOptions(proxy="   ").validate()

    def test_proxy_is_fine(self):
        assert DownloadOptions(proxy="socks5://127.0.0.1:1080").validate()
