from __future__ import annotations

from pathlib import Path

from scripts.generate_page_images import (
    IMAGE_QUALITY,
    build_image_prompt,
    insert_cover_front_matter,
    iter_pages,
    page_slug,
)


def test_build_image_prompt_uses_page_content() -> None:
    markdown = """---
title: "LINEとStripeで作るマッチングサービス"
categories:
  - "ビジネス・副業"
---

## 無料で読める内容

LINE Bot、Stripe Connect、Supabaseを使って小さな市場を収益化する方法を解説します。
"""

    prompt = build_image_prompt(markdown)

    assert "LINEとStripeで作るマッチングサービス" in prompt
    assert "LINE Bot" in prompt
    assert "Stripe Connect" in prompt
    assert "no readable text" in prompt


def test_insert_cover_front_matter_adds_cover() -> None:
    markdown = """---
title: "記事"
draft: false
---

本文
"""

    updated = insert_cover_front_matter(markdown, "/images/generated/article.png")

    assert 'image: "/images/generated/article.png"' in updated
    assert "cover:" in updated


def test_page_slug_uses_directory_for_bundle_index() -> None:
    assert page_slug(Path("content/manuals/product/index.md")) == "product"
    assert page_slug(Path("content/posts/sample-post.md")) == "sample-post"


def test_image_generation_defaults_to_high_quality() -> None:
    assert IMAGE_QUALITY == "high"


def test_iter_pages_can_limit_to_manuals(tmp_path: Path) -> None:
    manual = tmp_path / "sites" / "business" / "content" / "manuals" / "sample" / "index.md"
    section_index = tmp_path / "sites" / "business" / "content" / "manuals" / "_index.md"
    post = tmp_path / "sites" / "business" / "content" / "posts" / "post.md"
    manual.parent.mkdir(parents=True)
    post.parent.mkdir(parents=True)
    manual.write_text("---\ntitle: manual\n---\n", encoding="utf-8")
    section_index.write_text("---\ntitle: manuals\n---\n", encoding="utf-8")
    post.write_text("---\ntitle: post\n---\n", encoding="utf-8")

    pages = iter_pages(tmp_path, content_kind="manuals", limit=1)

    assert pages == [manual]
