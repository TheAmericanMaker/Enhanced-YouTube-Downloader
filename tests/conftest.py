"""Shared fixtures: an in-memory stand-in for yt-dlp."""

from __future__ import annotations

from types import SimpleNamespace
from typing import ClassVar

import pytest

import enhanced_youtube_downloader.downloader as dl_module


class FakeYoutubeDL:
    """Mimics the parts of yt_dlp.YoutubeDL used by the package.

    Behavior is controlled via class attributes, which tests can set
    before invoking the code under test.
    """

    instances: ClassVar[list] = []
    raise_download_error: ClassVar[Exception | None] = None
    raise_info_error: ClassVar[Exception | None] = None
    info_override: ClassVar[dict | None] = None

    def __init__(self, params):
        self.params = params
        self.finished_files: list = []
        FakeYoutubeDL.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def extract_info(self, url, download=False):
        if self.raise_info_error is not None:
            raise self.raise_info_error
        if self.info_override is not None:
            return self.info_override
        return {"title": "Fake Title", "formats": []}

    def download(self, urls):
        if self.raise_download_error is not None:
            raise self.raise_download_error
        filename = "Fake Title [abc123].mp4"
        self.finished_files.append(filename)
        for hook in self.params.get("progress_hooks", []):
            hook(
                {
                    "status": "downloading",
                    "filename": filename,
                    "downloaded_bytes": 50,
                    "total_bytes": 100,
                }
            )
            hook({"status": "finished", "filename": filename})
        for hook in self.params.get("post_hooks", []):
            hook(filename)


@pytest.fixture
def fake_yt_dlp(monkeypatch):
    FakeYoutubeDL.instances = []
    FakeYoutubeDL.raise_download_error = None
    FakeYoutubeDL.raise_info_error = None
    FakeYoutubeDL.info_override = None
    monkeypatch.setattr(dl_module, "yt_dlp", SimpleNamespace(YoutubeDL=FakeYoutubeDL))
    return FakeYoutubeDL
