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
