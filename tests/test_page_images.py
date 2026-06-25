from __future__ import annotations

from pathlib import Path

from scripts.generate_page_images import build_image_prompt, insert_cover_front_matter, page_slug


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
