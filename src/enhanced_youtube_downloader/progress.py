"""tqdm-based download progress reporting."""

from __future__ import annotations

import logging
from typing import Any

from tqdm import tqdm

logger = logging.getLogger(__name__)

__all__ = ["ProgressBar"]


class ProgressBar:
    """Manage a tqdm progress bar across yt-dlp progress-hook events.

    All state lives on the instance, so one bar can be created per
    download and concurrent downloads never interfere with each other.

    Args:
        enabled: when False, :meth:`hook` is a no-op (useful in tests or
            non-TTY contexts).
        description: label shown next to the bar.
    """

    def __init__(self, enabled: bool = True, description: str = "Downloading") -> None:
        self._enabled = enabled
        self._description = description
        self._bar: tqdm | None = None
        self._reported = 0

    def hook(self, d: dict[str, Any]) -> None:
        """Handle a single yt-dlp progress-hook payload."""
        if not self._enabled:
            return
        status = d.get("status")
        if status == "downloading":
            if self._bar is None:
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or None
                self._bar = tqdm(
                    total=total,
                    unit="B",
                    unit_scale=True,
                    desc=self._description,
                )
            downloaded = d.get("downloaded_bytes") or 0
            delta = downloaded - self._reported
            if delta > 0:
                self._bar.update(delta)
                self._reported = downloaded
        elif status == "finished" and self._bar is not None:
            self.close()

    def close(self) -> None:
        """Close the bar. Safe to call multiple times."""
        if self._bar is not None:
            self._bar.close()
            self._bar = None
            self._reported = 0
