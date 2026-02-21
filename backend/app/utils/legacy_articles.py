"""Legacy article loading helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

import yaml


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", title).strip().lower()
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug


def load_legacy_articles(project_root: Path) -> list[dict]:
    yaml_path = project_root / "yaml" / "article.yml"
    if not yaml_path.exists():
        return []

    with yaml_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or []

    now = datetime.now(tz=timezone.utc).isoformat()
    articles = []
    for entry in payload:
        title = str(entry.get("title", "Untitled")).strip()
        if not title:
            continue
        articles.append(
            {
                "id": slugify(title),
                "slug": slugify(title),
                "title": title,
                "summary": str(entry.get("summary", "")).strip(),
                "content": str(entry.get("content", "")).strip(),
                "created_at": now,
            }
        )

    return articles
