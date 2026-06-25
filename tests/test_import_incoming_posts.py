from __future__ import annotations

import json
from pathlib import Path

from scripts.import_incoming_posts import import_payload


def test_import_payload_routes_post_and_cover_image(tmp_path: Path) -> None:
    root = tmp_path
    (root / "sites" / "business" / "content" / "posts").mkdir(parents=True)
    cover = root / "cover.txt"
    cover.write_text("fake image", encoding="utf-8")
    config = {
        "blog": {
            "default_site": "sites/ai-tech",
            "site_map": {"ビジネス・副業": "sites/business"},
        }
    }
    payload = {
        "title": "AI副業の始め方",
        "category": "ビジネス・副業",
        "tags": ["AI", "副業"],
        "summary": "無料で読める導入です。",
        "body_markdown": "## 無料で読める内容\n\n本文です。",
        "cover_image_path": str(cover),
    }

    post_path = import_payload(root, config, payload)
    markdown = post_path.read_text(encoding="utf-8")

    assert post_path.parent == root / "sites" / "business" / "content" / "posts"
    assert 'title: "AI副業の始め方"' in markdown
    assert "cover:" in markdown
    assert (root / "sites" / "business" / "static" / "images" / "posts").exists()


def test_import_payload_accepts_json_file(tmp_path: Path) -> None:
    root = tmp_path
    config = {"blog": {"default_site": "sites/ai-tech", "site_map": {}}}
    source = tmp_path / "incoming.json"
    source.write_text(
        json.dumps({"title": "外部AI記事", "category": "AI・テック", "body_markdown": "本文です。"}, ensure_ascii=False),
        encoding="utf-8",
    )

    post_path = import_payload(root, config, source)

    assert post_path.exists()
    assert post_path.parent == root / "sites" / "ai-tech" / "content" / "posts"


def test_import_payload_inserts_inline_images(tmp_path: Path) -> None:
    root = tmp_path
    config = {"blog": {"default_site": "sites/ai-tech", "site_map": {}}}
    image = root / "flow.txt"
    image.write_text("fake inline image", encoding="utf-8")
    payload = {
        "title": "CLI画像差し込みテスト",
        "category": "AI・テック",
        "body_markdown": "## 前半\n\n{{image:flow}}\n\n## 後半\n\n本文です。",
        "inline_images": [{"id": "flow", "path": str(image), "alt": "記事フロー図", "extension": ".png"}],
    }

    post_path = import_payload(root, config, payload)
    markdown = post_path.read_text(encoding="utf-8")

    assert "{{image:flow}}" not in markdown
    assert "![記事フロー図](/images/posts/" in markdown
    assert "-flow.png)" in markdown
    stored_images = list((root / "sites" / "ai-tech" / "static" / "images" / "posts").glob("*-flow.png"))
    assert len(stored_images) == 1
