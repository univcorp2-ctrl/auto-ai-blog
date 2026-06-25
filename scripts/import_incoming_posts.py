from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.config_loader import load_yaml
from generator.markdown_post import make_slug, unique_post_path, yaml_quote
from generator.routing import route_category_to_site
from generator.runtime import JST, repo_root


def load_payload(source: Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(source, dict):
        return source
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Incoming JSON must be an object")
        return data
    return {"title": source.stem, "category": "AI・テック", "body_markdown": text}


def store_cover_image(root: Path, site_dir: Path, payload: dict[str, Any], slug: str) -> str | None:
    images_dir = root / site_dir / "static" / "images" / "posts"
    image_source = payload.get("cover_image_path")
    image_base64 = payload.get("cover_image_base64")
    if not image_source and not image_base64:
        return None
    images_dir.mkdir(parents=True, exist_ok=True)
    extension = str(payload.get("cover_image_extension") or ".png")
    if not extension.startswith("."):
        extension = f".{extension}"
    target = images_dir / f"{slug}{extension}"
    if image_base64:
        target.write_bytes(base64.b64decode(str(image_base64)))
    else:
        shutil.copyfile(Path(str(image_source)), target)
    return f"/images/posts/{target.name}"


def build_markdown(payload: dict[str, Any], cover_url: str | None, now: datetime) -> str:
    title = str(payload.get("title") or "外部AI記事").strip()
    category = str(payload.get("category") or "AI・テック").strip()
    tags = [str(tag) for tag in payload.get("tags", ["AI"])]
    body = str(payload.get("body_markdown") or payload.get("free_body_markdown") or "").strip()
    summary = str(payload.get("summary") or title).strip()
    front_matter = [
        "---",
        f"title: {yaml_quote(title)}",
        f"date: {now.isoformat(timespec='seconds')}",
        "draft: false",
        "tags:",
        *[f"  - {yaml_quote(tag)}" for tag in tags],
        "categories:",
        f"  - {yaml_quote(category)}",
        f"description: {yaml_quote(summary[:150])}",
    ]
    if cover_url:
        front_matter.extend(["cover:", f"  image: {yaml_quote(cover_url)}", "  relative: false"])
    front_matter.extend(["---", ""])
    return "\n".join(front_matter) + body + "\n"


def import_payload(root: Path, config: dict[str, Any], source: Path | dict[str, Any]) -> Path:
    payload = load_payload(source)
    now = datetime.now(JST).replace(microsecond=0)
    site_dir = route_category_to_site(config, str(payload.get("category") or "AI・テック"))
    title = str(payload.get("title") or "外部AI記事")
    slug = make_slug(title)
    cover_url = store_cover_image(root, site_dir, payload, slug)
    posts_dir = root / site_dir / "content" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    post_path = unique_post_path(posts_dir, now, title)
    post_path.write_text(build_markdown(payload, cover_url, now), encoding="utf-8")
    return post_path


def iter_incoming(root: Path) -> list[Path]:
    incoming = root / "incoming"
    if not incoming.exists():
        return []
    return sorted([*incoming.glob("*.json"), *incoming.glob("*.md")])


def main() -> int:
    parser = argparse.ArgumentParser(description="Import external AI posts from incoming/ into routed Hugo sites.")
    parser.add_argument("--archive", action="store_true", help="Move imported files to incoming/_archive.")
    args = parser.parse_args()

    root = repo_root()
    config = load_yaml(root / "generator" / "config.yaml")
    imported = []
    for source in iter_incoming(root):
        post_path = import_payload(root, config, source)
        imported.append(post_path)
        if args.archive:
            archive_dir = root / "incoming" / "_archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), archive_dir / source.name)
    for path in imported:
        print(path.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
