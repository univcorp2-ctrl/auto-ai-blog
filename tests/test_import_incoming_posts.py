from __future__ import annotations

import json
from pathlib import Path

from scripts.import_incoming_posts import import_payload

QUALITY_BODY = """
2026年6月26日、私はHiroの自動投稿APIで記事を送信し、本番URLが200で返るところまで実際に検証しました。
このサイトの実行ログ、画像表示、Cloudflare Pages反映を確認したうえで、次の手順をまとめます。

## 実際にやった手順

1. incoming JSONを作る
2. 画像を添付する
3. 本番URLで表示を確認する

## 注意点と失敗対策

OPENAI_API_KEYがない環境では画像生成は完了しません。その場合はプロンプトmanifestを残し、次回キーを入れて再実行します。

## 差別化と次のアクション

このコンテンツにしかない情報は、本番反映ログとAPI投稿の検証手順です。読者は次に、自分の記事JSONへ画像と検証ログを1つ追加してください。
"""


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
        "body_markdown": QUALITY_BODY,
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
        json.dumps({"title": "外部AI記事", "category": "AI・テック", "body_markdown": QUALITY_BODY}, ensure_ascii=False),
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
        "body_markdown": f"## 前半\n\n{{{{image:flow}}}}\n\n{QUALITY_BODY}",
        "inline_images": [{"id": "flow", "path": str(image), "alt": "記事フロー図", "extension": ".png"}],
    }

    post_path = import_payload(root, config, payload)
    markdown = post_path.read_text(encoding="utf-8")

    assert "{{image:flow}}" not in markdown
    assert "![記事フロー図](/images/posts/" in markdown
    assert "-flow.png)" in markdown
    stored_images = list((root / "sites" / "ai-tech" / "static" / "images" / "posts").glob("*-flow.png"))
    assert len(stored_images) == 1
