from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.runtime import repo_root

IMAGE_MODEL = "gpt-image-2"
IMAGE_SIZE = "1536x1024"


def extract_front_matter_value(markdown: str, key: str) -> str:
    match = re.search(rf'(?m)^{re.escape(key)}:\s*"?([^"\r\n]+)"?', markdown)
    return match.group(1).strip() if match else ""


def extract_category(markdown: str) -> str:
    match = re.search(r'(?m)^categories:\s*\n\s*-\s*"?([^"\r\n]+)"?', markdown)
    return match.group(1).strip() if match else "AI・テック"


def plain_excerpt(markdown: str, limit: int = 420) -> str:
    body = markdown.split("---", 2)[2] if markdown.startswith("---") and len(markdown.split("---", 2)) == 3 else markdown
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", body)
    body = re.sub(r"\[[^\]]+]\([^)]*\)", " ", body)
    body = re.sub(r"[#*_`>|-]+", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    return body[:limit]


def build_image_prompt(markdown: str) -> str:
    title = extract_front_matter_value(markdown, "title") or "Japanese educational article"
    category = extract_category(markdown)
    excerpt = plain_excerpt(markdown)
    return (
        "Create a unique, content-specific Japanese editorial web article cover image.\n"
        f"Title/topic: {title}\n"
        f"Category: {category}\n"
        f"Article context: {excerpt}\n"
        "The image must visually explain the core idea of this exact article, not just generic AI or business imagery.\n"
        "Use concrete objects, setting, workflow, or metaphor that matches the article content.\n"
        "Style: premium realistic editorial photography or polished explanatory editorial illustration, trustworthy and conversion-oriented.\n"
        "Composition: landscape cover image with clear focal point, usable on a Hugo/PaperMod article page.\n"
        "Constraints: no readable text, no logos, no watermark, no fake app screenshots, no repeated generic desk-only composition."
    )


def page_slug(path: Path) -> str:
    return path.parent.name if path.name == "index.md" else path.stem


def has_cover(markdown: str) -> bool:
    return bool(re.search(r"(?m)^cover:\s*$", markdown))


def insert_cover_front_matter(markdown: str, image_path: str) -> str:
    cover_block = f'cover:\n  image: "{image_path}"\n  relative: false\n'
    if has_cover(markdown):
        markdown = re.sub(
            r"(?ms)^cover:\s*\n(?:\s+.+\n)*",
            cover_block,
            markdown,
            count=1,
        )
        return markdown
    if not markdown.startswith("---"):
        return f"---\n{cover_block}---\n\n{markdown}"
    parts = markdown.split("---", 2)
    if len(parts) != 3:
        return markdown
    return f"---{parts[1]}{cover_block}---{parts[2]}"


def iter_pages(root: Path) -> list[Path]:
    pages: list[Path] = []
    for site in (root / "sites").iterdir():
        if not site.is_dir():
            continue
        content = site / "content"
        if not content.exists():
            continue
        for path in content.rglob("*.md"):
            if any(part in {"posts", "manuals"} for part in path.parts):
                pages.append(path)
    return sorted(pages)


def output_path_for_page(root: Path, page: Path) -> tuple[Path, str]:
    site = next(part for part in page.relative_to(root).parts if part in {"ai-tech", "business", "real-estate"})
    slug = page_slug(page)
    target = root / "sites" / site / "static" / "images" / "generated" / f"{slug}.png"
    return target, f"/images/generated/{target.name}"


def generate_image(api_key: str, prompt: str) -> bytes:
    request = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(
            {
                "model": IMAGE_MODEL,
                "prompt": prompt,
                "size": IMAGE_SIZE,
                "quality": "medium",
                "output_format": "png",
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = json.loads(response.read().decode("utf-8"))
    b64 = payload["data"][0]["b64_json"]
    return base64.b64decode(b64)


def process_pages(root: Path, *, overwrite: bool, dry_run: bool, prompt_manifest: Path | None) -> list[Path]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    manifest_rows = []
    written: list[Path] = []
    for page in iter_pages(root):
        markdown = page.read_text(encoding="utf-8")
        target, public_path = output_path_for_page(root, page)
        prompt = build_image_prompt(markdown)
        manifest_rows.append({"page": str(page.relative_to(root)), "image": str(target.relative_to(root)), "prompt": prompt})
        if dry_run:
            continue
        if not api_key:
            continue
        if target.exists() and not overwrite:
            if public_path not in markdown:
                page.write_text(insert_cover_front_matter(markdown, public_path), encoding="utf-8")
                written.append(page)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        image_bytes = generate_image(api_key, prompt)
        target.write_bytes(image_bytes)
        page.write_text(insert_cover_front_matter(markdown, public_path), encoding="utf-8")
        written.extend([target, page])
        time.sleep(1)
    if prompt_manifest:
        prompt_manifest.parent.mkdir(parents=True, exist_ok=True)
        prompt_manifest.write_text(json.dumps(manifest_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate content-specific cover images for every post and manual page.")
    parser.add_argument("--overwrite", action="store_true", help="Regenerate existing generated images.")
    parser.add_argument("--dry-run", action="store_true", help="Only create prompt manifest; do not call image API.")
    parser.add_argument("--prompt-manifest", default="tmp/page-image-prompts.json", help="Where to write generated prompts.")
    args = parser.parse_args()

    root = repo_root()
    manifest = root / args.prompt_manifest if args.prompt_manifest else None
    written = process_pages(root, overwrite=args.overwrite, dry_run=args.dry_run, prompt_manifest=manifest)
    if not os.getenv("OPENAI_API_KEY") and not args.dry_run:
        print("OPENAI_API_KEY is not set; wrote prompt manifest only and did not generate images.", file=sys.stderr)
        return 2
    for path in written:
        print(path.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
