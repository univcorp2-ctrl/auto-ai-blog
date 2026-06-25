from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_API_URL = "https://auto-ai-blog-post-ingest.univcorp2.workers.dev/api/posts"
IMAGE_MODEL = "gpt-image-2"


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("payload JSON must be an object")
    return data


def post_json(url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"post failed: HTTP {exc.code}: {detail}") from exc


def generate_image_base64(api_key: str, prompt: str, *, quality: str) -> str:
    request_body = json.dumps(
        {
            "model": IMAGE_MODEL,
            "prompt": f"{prompt}\nJapanese editorial web article image, no text, no watermark.",
            "size": "1536x1024",
            "quality": quality,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=request_body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"image generation failed: HTTP {exc.code}: {detail}") from exc
    image = data.get("data", [{}])[0].get("b64_json")
    if not image:
        raise RuntimeError("image generation returned no b64_json")
    return str(image)


def prepare_payload(payload: dict[str, Any], *, openai_api_key: str, image_quality: str) -> dict[str, Any]:
    prepared = dict(payload)
    if prepared.get("cover_image_prompt") and not prepared.get("cover_image_base64") and not prepared.get("cover_image_url"):
        prepared["cover_image_base64"] = generate_image_base64(
            openai_api_key,
            str(prepared["cover_image_prompt"]),
            quality=image_quality,
        )
        prepared.setdefault("cover_image_extension", ".png")

    inline_images = []
    for raw_image in prepared.get("inline_images", []) or []:
        if not isinstance(raw_image, dict):
            continue
        image = dict(raw_image)
        prompt = image.get("prompt") or image.get("image_prompt")
        has_image = image.get("base64") or image.get("image_base64") or image.get("url")
        if prompt and not has_image:
            image["base64"] = generate_image_base64(openai_api_key, str(prompt), quality=image_quality)
            image.setdefault("extension", ".png")
        inline_images.append(image)
    if inline_images:
        prepared["inline_images"] = inline_images
    return prepared


def write_dry_run(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate article images from the CLI and submit a post payload.")
    parser.add_argument("payload", type=Path, help="JSON payload from an external AI writer.")
    parser.add_argument("--api-url", default=os.environ.get("AUTO_AI_BLOG_API_URL", DEFAULT_API_URL))
    parser.add_argument("--ingest-key", default=os.environ.get("INGEST_API_KEY"))
    parser.add_argument("--openai-api-key", default=os.environ.get("OPENAI_API_KEY"))
    parser.add_argument("--image-quality", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--dry-run-output", type=Path, help="Write the generated payload and do not submit it.")
    args = parser.parse_args()

    payload = read_json(args.payload)
    needs_generation = bool(payload.get("cover_image_prompt")) or any(
        isinstance(image, dict) and (image.get("prompt") or image.get("image_prompt"))
        for image in payload.get("inline_images", []) or []
    )
    if needs_generation and not args.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required for CLI image generation.")

    prepared = prepare_payload(payload, openai_api_key=str(args.openai_api_key or ""), image_quality=args.image_quality)
    if args.dry_run_output:
        write_dry_run(args.dry_run_output, prepared)
        print(args.dry_run_output)
        return 0

    if not args.ingest_key:
        raise RuntimeError("INGEST_API_KEY is required to submit the generated payload.")
    response = post_json(args.api_url, args.ingest_key, prepared)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
