# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities.

- Preferred: use the **Security** tab of this repository's GitHub page to
  open a private vulnerability report.
- Alternative: email the maintainer (see the repository profile).

We aim to acknowledge reports within 7 days and to ship a fix in a
patch release as soon as reasonably possible.

## Scope

- The `enhanced-youtube-downloader` package and its CLI.
- In scope: path handling, input validation, and any behavior that could
  be abused through crafted URLs or options.
- Out of scope: vulnerabilities in upstream projects (yt-dlp, tqdm,
  FFmpeg) - please report those upstream.

## Supported versions

Only the latest stable release on PyPI is supported.
