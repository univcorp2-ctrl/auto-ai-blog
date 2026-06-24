from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from slugify import slugify

from generator.models import Topic


def strip_front_matter(markdown: str) -> str:
    text = markdown.strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text


def clean_title(value: str) -> str:
    value = re.sub(r"^[#\s]+", "", value).strip()
    value = re.sub(r"[*_`]+", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:90] or "無題の記事"


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return clean_title(stripped)
    return clean_title(fallback)


def remove_first_h1(markdown: str) -> str:
    lines = markdown.strip().splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        return "\n".join(lines[1:]).strip()
    return markdown.strip()


def make_description(markdown: str, fallback: str, max_len: int = 150) -> str:
    for line in markdown.splitlines():
        text = line.strip()
        if not text or text.startswith("#") or text.startswith("-") or text.startswith("|"):
            continue
        text = re.sub(r"[*_`>#\[\]()]+", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            return text[:max_len]
    return fallback[:max_len]


def make_slug(title: str) -> str:
    slug = slugify(title, lowercase=True, max_length=80, word_boundary=True)
    if slug:
        return slug
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
    return f"post-{digest}"


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_post_markdown(article: str, topic: Topic, blog_config: dict[str, Any], now: datetime) -> tuple[str, str]:
    body = strip_front_matter(article)
    title = extract_title(body, topic.topic)
    body_without_h1 = remove_first_h1(body)
    description = make_description(body_without_h1, topic.topic)
    tags = list(dict.fromkeys([*topic.keywords, "AI", "不動産"]))
    category = topic.category or str(blog_config.get("default_category", "AI・テック"))

    front_matter = [
        "---",
        f"title: {yaml_quote(title)}",
        f"date: {now.isoformat(timespec='seconds')}",
        "draft: false",
        "tags:",
        *[f"  - {yaml_quote(tag)}" for tag in tags],
        "categories:",
        f"  - {yaml_quote(category)}",
        f"description: {yaml_quote(description)}",
        "---",
        "",
    ]
    return "\n".join(front_matter) + body_without_h1.strip() + "\n", title


def unique_post_path(posts_dir: Path, now: datetime, title: str) -> Path:
    base_name = f"{now:%Y-%m-%d}-{make_slug(title)}"
    candidate = posts_dir / f"{base_name}.md"
    suffix = 2
    while candidate.exists():
        candidate = posts_dir / f"{base_name}-{suffix}.md"
        suffix += 1
    return candidate


def resolve_site_dir(root: Path, topic: Topic, blog_config: dict[str, Any]) -> Path:
    site_map = blog_config.get("site_map", {})
    if isinstance(site_map, dict) and topic.category in site_map:
        return root / str(site_map[topic.category])
    return root / str(blog_config.get("default_site", "hugo-site"))


def save_post(root: Path, post_markdown: str, title: str, now: datetime, topic: Topic, blog_config: dict[str, Any]) -> Path:
    posts_dir = resolve_site_dir(root, topic, blog_config) / "content" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    path = unique_post_path(posts_dir, now, title)
    path.write_text(post_markdown, encoding="utf-8")
    logging.info("Saved post: %s", path)
    return path

