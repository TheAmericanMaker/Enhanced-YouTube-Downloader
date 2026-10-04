"""Config-file support for the ``eyd`` CLI.

The config file is an INI-style ``key=value`` file (comments start with ``#``
or ``;``). Keys map to CLI flags and act as *defaults*: any flag the user
supplies on the command line takes precedence over the config file.
"""

from __future__ import annotations

import configparser
import os
import sys
from argparse import Namespace
from collections.abc import Sequence

__all__ = [
    "CONFIG_KEY_TO_ARG",
    "apply_config",
    "default_config_path",
    "parse_config_file",
]

DEFAULT_CONFIG_PATH = "~/.config/eyd/config.ini"

# config key -> (CLI flag tokens that count as "explicitly provided", args dest)
CONFIG_KEY_TO_ARG: dict[str, tuple[list[str], str]] = {
    "output": (["-o", "--output"], "output"),
    "quality": (["-q", "--quality"], "quality"),
    "audio_format": (["-f", "--audio-format"], "audio_format"),
    "audio_quality": (["--audio-quality"], "audio_quality"),
    "subtitles": (["--subtitles"], "subtitles"),
    "write_auto_sub": (["--write-auto-sub"], "write_auto_sub"),
    "subtitle_langs": (["--subtitle-langs"], "subtitle_langs"),
    "thumbnails": (["--thumbnails"], "thumbnails"),
    "no_embed_metadata": (["--no-embed-metadata"], "no_embed_metadata"),
    "playlist": (["--playlist"], "playlist"),
    "playlist_items": (["--playlist-items"], "playlist_items"),
    "retries": (["--retries"], "retries"),
    "no_progress": (["--no-progress"], "no_progress"),
    "cookies": (["--cookies"], "cookies"),
    "cookies_from_browser": (["--cookies-from-browser"], "cookies_from_browser"),
    "proxy": (["--proxy"], "proxy"),
    "concurrency": (["--concurrency"], "concurrency"),
    "no_overwrites": (["--no-overwrites"], "no_overwrites"),
    "filename_template": (["--filename-template"], "filename_template"),
}

_BOOL_KEYS = {
    "subtitles",
    "write_auto_sub",
    "thumbnails",
    "no_embed_metadata",
    "playlist",
    "no_progress",
    "no_overwrites",
}

_INT_KEYS = {"retries", "concurrency"}

_TRUE = {"1", "true", "yes", "on", "y", "t"}
_FALSE = {"0", "false", "no", "off", "n", "f", ""}


def default_config_path() -> str:
    """The default config file location (``~/.config/eyd/config.ini``)."""
    return os.path.expanduser(DEFAULT_CONFIG_PATH)


def _to_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in _TRUE:
        return True
    if normalized in _FALSE:
        return False
    raise ValueError(f"invalid boolean {value!r}; use one of true/false")


def _warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr)


def parse_config_file(path: str, *, strict: bool = False) -> dict[str, str]:
    """Parse a ``key=value`` config file into a dict of raw string values.

    Args:
        path: path to the config file (``~`` is expanded).
        strict: when True, unknown keys are an error; when False they are
            skipped with a warning (used for the auto-loaded default file).

    Returns:
        A dict mapping recognized config keys to their raw (stripped) string
        values.

    Raises:
        ValueError: if the file does not exist, or a key is not recognized and
            ``strict`` is True.
    """
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        raise ValueError(f"config file not found: {path}")
    parser = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))

    def _keep_case(optionstr: str) -> str:
        return optionstr

    parser.optionxform = _keep_case
    with open(expanded, encoding="utf-8") as handle:
        body = handle.read()
    lines = [
        line
        for line in body.splitlines()
        if line.strip() and not line.strip().startswith(("#", ";"))
    ]
    parser.read_string("[config]\n" + "\n".join(lines))
    data: dict[str, str] = {}
    for key, value in parser["config"].items():
        key = key.strip().lower()
        if key not in CONFIG_KEY_TO_ARG:
            if strict:
                raise ValueError(f"unknown config key {key!r} in {path}")
            _warn(f"ignoring unknown config key {key!r} in {path}")
            continue
        data[key] = value.strip()
    return data


def _token_matches(token: str, flags: list[str]) -> bool:
    """Return True if a raw argv token supplies any of the given flags.

    Handles ``--flag value``, ``--flag=value`` and short flags with an attached
    value (e.g. ``-q1080p``).
    """
    for flag in flags:
        if token == flag:
            return True
        if token.startswith(flag + "="):
            return True
        if len(flag) == 2 and len(token) >= 3 and token.startswith(flag):
            return True
    return False


def _explicitly_provided(argv: Sequence[str]) -> set[str]:
    """Return the set of config keys the user passed on the command line."""
    provided: set[str] = set()
    for key, (flags, _dest) in CONFIG_KEY_TO_ARG.items():
        if any(_token_matches(tok, flags) for tok in argv):
            provided.add(key)
    return provided


def apply_config(args: Namespace, argv: Sequence[str], path: str, *, explicit: bool) -> None:
    """Merge a config file into an already-parsed ``args`` namespace in place.

    Config values are only applied to flags the user did not pass on the command
    line, so the CLI always wins.

    Args:
        args: the parsed argparse namespace to mutate.
        argv: the raw command-line tokens, used to detect explicit overrides.
        path: the config file path to load (``~`` is expanded).
        explicit: when True (the user passed ``--config``), a missing file is an
            error; when False (the default path), a missing file is ignored.

    Raises:
        ValueError: if the file is missing (and ``explicit``), a key is unknown
            (and ``explicit``), or a value is malformed for its type.
    """
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        if explicit:
            raise ValueError(f"config file not found: {path}")
        return
    config = parse_config_file(path, strict=explicit)
    provided = _explicitly_provided(argv)
    current = ""
    try:
        for key, value in config.items():
            current = key
            if key in provided:
                continue
            _flags, dest = CONFIG_KEY_TO_ARG[key]
            if key in _BOOL_KEYS:
                setattr(args, dest, _to_bool(value))
            elif value:
                setattr(args, dest, int(value) if key in _INT_KEYS else value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid value for {current!r} in {path}") from exc
