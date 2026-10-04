"""Tests for the config-file feature (config.py) and the browser-spec helper.

The config loader is exercised both in isolation (parse_config_file /
apply_config) and end-to-end through cli.main(), with the default config path
redirected to a temp dir so tests never touch ~/.config/eyd.
"""

from __future__ import annotations

from argparse import Namespace

import pytest

from enhanced_youtube_downloader import cli as cli_module
from enhanced_youtube_downloader.cli import main
from enhanced_youtube_downloader.config import (
    apply_config,
    default_config_path,
    parse_config_file,
)
from enhanced_youtube_downloader.options import cookie_browser_to_tuple

URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


class TestCookieBrowserToTuple:
    def test_with_profile(self):
        assert cookie_browser_to_tuple("chrome+Default") == ("chrome", "Default", None, None)

    def test_without_profile(self):
        assert cookie_browser_to_tuple("firefox") == ("firefox", None, None, None)

    def test_result_is_always_a_tuple(self):
        # yt-dlp unpacks this value with `*`, so it must never be a string.
        assert isinstance(cookie_browser_to_tuple("edge"), tuple)

    def test_rejects_unknown_browser(self):
        with pytest.raises(ValueError):
            cookie_browser_to_tuple("ie6")


@pytest.fixture
def cfg_home(tmp_path, monkeypatch):
    """Redirect the default config path into a temp home and return that dir."""
    cfg = tmp_path / "config.ini"
    monkeypatch.setattr(cli_module, "default_config_path", lambda: str(cfg))
    return cfg


class TestParseConfigFile:
    def test_parses_key_value_pairs(self, tmp_path):
        p = tmp_path / "c.ini"
        p.write_text("output = /tmp/videos\nquality = 1080p\n# a comment\nretries = 3\n")
        data = parse_config_file(str(p))
        assert data == {"output": "/tmp/videos", "quality": "1080p", "retries": "3"}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(ValueError):
            parse_config_file(str(tmp_path / "nope.ini"))

    def test_unknown_key_strict_raises(self, tmp_path):
        p = tmp_path / "c.ini"
        p.write_text("bogus = 1\n")
        with pytest.raises(ValueError):
            parse_config_file(str(p), strict=True)

    def test_unknown_key_lenient_warns_and_skips(self, tmp_path, capsys):
        p = tmp_path / "c.ini"
        p.write_text("bogus = 1\nquality = 720p\n")
        data = parse_config_file(str(p))  # lenient by default
        assert data == {"quality": "720p"}
        assert "bogus" in capsys.readouterr().err

    def test_case_insensitive_keys(self, tmp_path):
        p = tmp_path / "c.ini"
        p.write_text("Output = /x\nQUALITY = 480p\n")
        assert parse_config_file(str(p)) == {"output": "/x", "quality": "480p"}


class TestApplyConfig:
    def _write(self, tmp_path, text):
        p = tmp_path / "c.ini"
        p.write_text(text)
        return str(p)

    def test_missing_default_is_ignored(self, tmp_path):
        args = Namespace(quality=None)
        apply_config(args, [], str(tmp_path / "absent.ini"), explicit=False)
        assert args.quality is None

    def test_missing_explicit_raises(self, tmp_path):
        args = Namespace()
        with pytest.raises(ValueError):
            apply_config(args, [], str(tmp_path / "absent.ini"), explicit=True)

    def test_applies_values_for_unset_flags(self, tmp_path):
        args = Namespace(output=None, quality=None, retries=10, subtitles=False, concurrency=1)
        path = self._write(tmp_path, "output=/dl\nquality=720p\nretries=3\nsubtitles=true\n")
        # --retries was given on the CLI, so the config's retries=3 must not touch it.
        apply_config(args, ["download", URL, "--retries", "10"], path, explicit=False)
        assert args.output == "/dl"
        assert args.quality == "720p"
        assert args.subtitles is True
        assert args.retries == 10  # CLI beat the config
        assert args.concurrency == 1  # not in the config, so untouched

    def test_cli_flag_beats_config(self, tmp_path):
        args = Namespace(quality=None, output=None)
        path = self._write(tmp_path, "quality=360p\noutput=/cfg\n")
        # -q360p attached form and --output as a separate token both count as provided.
        apply_config(
            args, ["download", URL, "-q", "1080p", "--output", "/cli"], path, explicit=False
        )
        assert args.quality is None  # config skipped because -q was provided
        assert args.output is None  # config skipped because --output was provided

    def test_equals_form_counts_as_provided(self, tmp_path):
        args = Namespace(quality=None, output=None)
        path = self._write(tmp_path, "quality=360p\noutput=/cfg\n")
        apply_config(args, ["download", URL, "-q1080p", "--output=/cli"], path, explicit=False)
        assert args.quality is None
        assert args.output is None

    def test_empty_value_does_not_override_flag_default(self, tmp_path):
        args = Namespace(quality=None, subtitles=False)
        path = self._write(tmp_path, "quality=\nsubtitles=true\n")
        apply_config(args, [], path, explicit=False)
        assert args.quality is None  # empty value left the default untouched
        assert args.subtitles is True  # but a real bool was applied

    def test_invalid_int_raises(self, tmp_path):
        args = Namespace(retries=0)
        path = self._write(tmp_path, "retries = not-a-number\n")
        with pytest.raises(ValueError):
            apply_config(args, [], path, explicit=True)

    def test_invalid_bool_raises(self, tmp_path):
        args = Namespace(subtitles=False)
        path = self._write(tmp_path, "subtitles = maybe\n")
        with pytest.raises(ValueError):
            apply_config(args, [], path, explicit=True)


class TestCliConfigIntegration:
    def test_config_applies_to_download(self, fake_yt_dlp, tmp_path, cfg_home, capsys):
        cfg_home.write_text("quality = 720p\nretries = 5\nsubtitles = true\n")
        code = main(["download", URL, "-o", str(tmp_path)])
        assert code == 0
        params = fake_yt_dlp.instances[-1].params
        assert "height<=720" in params["format"]
        assert params["retries"] == 5
        assert params["writesubtitles"] is True

    def test_cli_overrides_config(self, fake_yt_dlp, tmp_path, cfg_home):
        cfg_home.write_text("quality = 720p\n")
        code = main(["download", URL, "-o", str(tmp_path), "-q", "360p"])
        assert code == 0
        assert "height<=360" in fake_yt_dlp.instances[-1].params["format"]

    def test_explicit_config_flag(self, fake_yt_dlp, tmp_path, monkeypatch):
        # Redirect the auto default to a non-existent path so only --config loads.
        monkeypatch.setattr(cli_module, "default_config_path", lambda: str(tmp_path / "absent"))
        custom = tmp_path / "custom.ini"
        custom.write_text("quality = 480p\n")
        code = main(["--config", str(custom), "download", URL, "-o", str(tmp_path)])
        assert code == 0
        assert "height<=480" in fake_yt_dlp.instances[-1].params["format"]

    def test_explicit_config_missing_is_error(self, tmp_path, capsys):
        assert main(["--config", str(tmp_path / "nope.ini"), "download", URL]) == 1
        assert "config file not found" in capsys.readouterr().err

    def test_stale_default_config_does_not_break_download(
        self, fake_yt_dlp, tmp_path, cfg_home, capsys
    ):
        # A lenient default config with an unknown key must warn, not fail.
        cfg_home.write_text("quality = 720p\nfrobnicate = 1\n")
        code = main(["download", URL, "-o", str(tmp_path)])
        assert code == 0
        assert "height<=720" in fake_yt_dlp.instances[-1].params["format"]
        assert "frobnicate" in capsys.readouterr().err


def test_default_config_path_points_into_home():
    path = default_config_path()
    assert path.endswith(".config/eyd/config.ini") or "config/eyd/config.ini" in path
