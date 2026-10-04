"""Tests for enhanced_youtube_downloader.cli (yt-dlp is mocked)."""

from __future__ import annotations

import pytest

from enhanced_youtube_downloader import cli as cli_module
from enhanced_youtube_downloader.cli import build_parser, main

URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


class TestMain:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--version"])
        assert exc.value.code == 0
        assert "eyd" in capsys.readouterr().out

    def test_missing_command_exits_2(self):
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code == 2

    def test_download_invalid_url(self, capsys):
        assert main(["download", "not-a-url"]) == 1
        assert "error" in capsys.readouterr().err

    def test_download_bad_quality(self, capsys):
        assert main(["download", URL, "-q", "sparkly"]) == 1
        assert "quality" in capsys.readouterr().err

    def test_download_success(self, fake_yt_dlp, capsys, tmp_path):
        code = main(["download", URL, "-o", str(tmp_path), "-q", "1080p"])
        out = capsys.readouterr().out
        assert code == 0
        assert "Saved:" in out

    def test_download_failure(self, fake_yt_dlp, capsys):
        fake_yt_dlp.raise_download_error = RuntimeError("boom")
        assert main(["download", URL]) == 1
        assert "boom" in capsys.readouterr().err

    def test_download_multi_file_reports_count(self, fake_yt_dlp, capsys):
        fake_yt_dlp.post_hook_files = ["a.mp4", "b.mp4"]
        code = main(["download", URL, "--playlist"])
        out = capsys.readouterr().out
        assert code == 0
        assert "Saved 2 files" in out
        assert "a.mp4" in out and "b.mp4" in out

    def test_download_partial_playlist_reports_failures_and_exits_1(self, fake_yt_dlp, capsys):
        fake_yt_dlp.post_hook_files = ["a.mp4"]
        fake_yt_dlp.failed_errors = ["ERROR: b: Video unavailable"]
        fake_yt_dlp.retcode = 1
        code = main(["download", URL, "--playlist"])
        err = capsys.readouterr().out
        assert code == 1
        assert "1 item(s) failed" in err
        assert "saved: a.mp4" in err
        assert "b" in err

    def test_download_no_files_is_failure(self, fake_yt_dlp, capsys):
        fake_yt_dlp.post_hook_files = []
        fake_yt_dlp.failed_errors = ["ERROR: x: unavailable"]
        fake_yt_dlp.retcode = 1
        assert main(["download", URL, "--playlist"]) == 1
        assert "no files" in capsys.readouterr().err

    def test_download_cookie_file_flag(self, fake_yt_dlp, capsys, tmp_path):
        code = main(["download", URL, "--cookies", "/tmp/c.txt", "-o", str(tmp_path)])
        assert code == 0
        assert fake_yt_dlp.instances[-1].params["cookiefile"] == "/tmp/c.txt"

    def test_download_cookies_from_browser_flag(self, fake_yt_dlp, capsys, tmp_path):
        code = main(
            ["download", URL, "--cookies-from-browser", "chrome+Default", "-o", str(tmp_path)]
        )
        assert code == 0
        # Must reach yt-dlp as a 4-tuple, not the raw string (yt-dlp unpacks it).
        assert fake_yt_dlp.instances[-1].params["cookiesfrombrowser"] == (
            "chrome",
            "Default",
            None,
            None,
        )

    def test_download_bad_cookies_from_browser_rejected(self, capsys):
        assert main(["download", URL, "--cookies-from-browser", "ie6"]) == 1
        assert "browser" in capsys.readouterr().err

    def test_download_both_cookie_sources_conflict(self, capsys):
        assert main(["download", URL, "--cookies", "a", "--cookies-from-browser", "chrome"]) == 1
        assert "at most one" in capsys.readouterr().err

    def test_download_proxy_flag(self, fake_yt_dlp, capsys, tmp_path):
        code = main(["download", URL, "--proxy", "socks5://127.0.0.1:1080", "-o", str(tmp_path)])
        assert code == 0
        assert fake_yt_dlp.instances[-1].params["proxy"] == "socks5://127.0.0.1:1080"

    def test_download_concurrency_flag(self, fake_yt_dlp, capsys, tmp_path):
        code = main(["download", URL, "--concurrency", "4", "-o", str(tmp_path)])
        assert code == 0
        assert fake_yt_dlp.instances[-1].params["concurrent_fragment_downloads"] == 4

    def test_download_no_overwrites_flag(self, fake_yt_dlp, capsys, tmp_path):
        code = main(["download", URL, "--no-overwrites", "-o", str(tmp_path)])
        assert code == 0
        assert fake_yt_dlp.instances[-1].params["nooverwrites"] is True

    def test_download_write_auto_sub_flag(self, fake_yt_dlp, capsys, tmp_path):
        code = main(
            ["download", URL, "--write-auto-sub", "--subtitle-langs", "en,de", "-o", str(tmp_path)]
        )
        assert code == 0
        params = fake_yt_dlp.instances[-1].params
        assert params["writeautomaticsub"] is True
        assert params["subtitleslangs"] == ["en", "de"]

    def test_download_subtitle_langs_without_flag_is_error(self, capsys):
        # --subtitle-langs alone was silently ignored before; now it is an error.
        assert main(["download", URL, "--subtitle-langs", "en"]) == 1
        assert "subtitle-langs" in capsys.readouterr().err

    def test_download_subtitle_langs_with_subtitles_ok(self, fake_yt_dlp, capsys, tmp_path):
        code = main(["download", URL, "--subtitles", "--subtitle-langs", "en", "-o", str(tmp_path)])
        assert code == 0

    def test_audio_success(self, fake_yt_dlp, capsys, tmp_path):
        code = main(["audio", URL, "-f", "opus", "-o", str(tmp_path)])
        assert code == 0
        assert "Saved:" in capsys.readouterr().out

    def test_audio_bad_format_rejected_by_parser(self, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["audio", URL, "-f", "avi"])
        assert exc.value.code == 2

    def test_formats(self, fake_yt_dlp, capsys):
        fake_yt_dlp.info_override = {
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "resolution": "360p",
                    "fps": 30,
                    "filesize": 1500000,
                    "note": "s",
                }
            ]
        }
        code = main(["formats", URL])
        out = capsys.readouterr().out
        assert code == 0
        assert "360p" in out
        assert "mp4" in out
        assert "1.4 MiB" in out

    def test_formats_none(self, fake_yt_dlp, capsys):
        assert main(["formats", URL]) == 1
        assert "No formats" in capsys.readouterr().err

    def test_formats_json(self, fake_yt_dlp, capsys):
        fake_yt_dlp.info_override = {
            "formats": [
                {"format_id": "18", "ext": "mp4", "resolution": "360p", "fps": 30},
            ]
        }
        assert main(["formats", URL, "--json"]) == 0
        out = capsys.readouterr().out
        assert out.strip().startswith("[")
        assert '"format_id": "18"' in out
        # Table columns should NOT appear in JSON mode.
        assert "Resolution" not in out

    def test_info_json(self, fake_yt_dlp, capsys):
        fake_yt_dlp.info_override = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 61,
            "view_count": 5,
        }
        assert main(["info", URL, "--json"]) == 0
        out = capsys.readouterr().out
        assert out.strip().startswith("{")
        assert '"title": "Test Video"' in out
        assert "Channel  :" not in out

    def test_info_video(self, fake_yt_dlp, capsys):
        fake_yt_dlp.info_override = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "duration": 3661,
            "view_count": 5,
        }
        assert main(["info", URL]) == 0
        out = capsys.readouterr().out
        assert "Test Video" in out
        assert "1:01:01" in out

    def test_info_playlist(self, fake_yt_dlp, capsys):
        fake_yt_dlp.info_override = {
            "_type": "playlist",
            "title": "My Playlist",
            "entries": [
                {"id": "aaaa", "title": "One", "duration": 61},
                {"id": "bbbb", "title": "Two", "duration": 3725},
            ],
        }
        assert main(["info", URL, "--playlist"]) == 0
        out = capsys.readouterr().out
        assert "My Playlist" in out
        assert "Entries  : 2" in out
        assert "1:01" in out
        assert "1:02:05" in out

    def test_info_failure(self, fake_yt_dlp, capsys):
        fake_yt_dlp.raise_info_error = RuntimeError("extractor error")
        assert main(["info", URL]) == 1
        assert "Could not fetch" in capsys.readouterr().err


class TestHelpers:
    def test_human_size(self):
        assert cli_module._human_size(None) == ""
        assert cli_module._human_size(512) == "512 B"
        assert cli_module._human_size(1536) == "1.5 KiB"
        assert cli_module._human_size(1500000) == "1.4 MiB"

    def test_format_duration(self):
        assert cli_module._format_duration(None) == "n/a"
        assert cli_module._format_duration(0) == "n/a"
        assert cli_module._format_duration(65) == "1:05"
        assert cli_module._format_duration(3661) == "1:01:01"


class TestInteractive:
    def _patch_input(self, monkeypatch, lines):
        iterator = iter(lines)
        monkeypatch.setattr(
            "builtins.input",
            lambda prompt="": next(iterator, "quit"),
        )

    def test_quit_immediately(self, monkeypatch, fake_yt_dlp, capsys):
        self._patch_input(monkeypatch, [])
        args = build_parser().parse_args(["interactive"])
        assert cli_module.cmd_interactive(args) == 0
        assert "interactive mode" in capsys.readouterr().out

    def test_help_and_unknown_command(self, monkeypatch, fake_yt_dlp, capsys):
        self._patch_input(monkeypatch, ["help", "bogus", "quit"])
        args = build_parser().parse_args(["interactive"])
        assert cli_module.cmd_interactive(args) == 0
        out = capsys.readouterr().out
        assert "Available commands" in out
        assert "Unknown command" in out

    def test_download_and_dir(self, monkeypatch, fake_yt_dlp, capsys, tmp_path):
        self._patch_input(
            monkeypatch,
            [f"dir {tmp_path}", f"download {URL} 720p", "formats", "quit"],
        )
        fake_yt_dlp.info_override = {"formats": [{"format_id": "18", "ext": "mp4"}]}
        args = build_parser().parse_args(["interactive"])
        assert cli_module.cmd_interactive(args) == 0
        out = capsys.readouterr().out
        assert str(tmp_path) in out
        assert "Download completed." in out
        assert "usage: formats <url>" in out

    def test_cookies_command(self, monkeypatch, fake_yt_dlp, capsys, tmp_path):
        self._patch_input(
            monkeypatch,
            [f"cookies {tmp_path}/c.txt", "cookies", "download", "quit"],
        )
        args = build_parser().parse_args(["interactive"])
        assert cli_module.cmd_interactive(args) == 0
        out = capsys.readouterr().out
        assert "Cookies file:" in out
        assert str(tmp_path) in out
        assert "usage: download <url>" in out

    def test_download_bad_quality_is_reported_not_fatal(self, monkeypatch, fake_yt_dlp, capsys):
        self._patch_input(monkeypatch, [f"download {URL} sparkly", "quit"])
        args = build_parser().parse_args(["interactive"])
        assert cli_module.cmd_interactive(args) == 0
        out = capsys.readouterr().out
        assert "Error:" in out
