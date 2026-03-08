from __future__ import annotations

from datetime import datetime, timezone as dt_timezone
from pathlib import Path

import markdown as md
from django.conf import settings
from django.utils import timezone
from django.utils.html import escape


DEFAULT_CHANGELOG_TEMPLATE = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Describe newly added features here.
"""


def get_changelog_path() -> Path:
    configured_path = getattr(settings, "CHANGELOG_PATH", settings.BASE_DIR / "CHANGELOG.md")
    return Path(configured_path)


def ensure_changelog_file(path: Path) -> bool:
    if path.exists():
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(DEFAULT_CHANGELOG_TEMPLATE, encoding="utf-8")
    return True


def render_changelog_html(content: str) -> str:
    # Escape raw HTML so the changelog remains safe to render inside the admin.
    escaped_content = escape(content)
    return md.markdown(
        escaped_content,
        extensions=[
            "markdown.extensions.fenced_code",
            "markdown.extensions.tables",
            "markdown.extensions.sane_lists",
        ],
    )


def get_changelog_page_context() -> dict[str, object]:
    changelog_path = get_changelog_path()
    file_created = ensure_changelog_file(changelog_path)
    content = changelog_path.read_text(encoding="utf-8")
    updated_at = timezone.localtime(
        datetime.fromtimestamp(changelog_path.stat().st_mtime, tz=dt_timezone.utc)
    )

    return {
        "changelog_exists": changelog_path.exists(),
        "changelog_file_created": file_created,
        "changelog_is_empty": not content.strip(),
        "changelog_path": str(changelog_path),
        "changelog_updated_at": updated_at,
        "changelog_html": render_changelog_html(content) if content.strip() else "",
    }
