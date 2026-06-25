from __future__ import annotations

from pathlib import Path

from scripts.validate_ai_slop import iter_targets


def test_iter_targets_excludes_section_indexes(tmp_path: Path) -> None:
    post = tmp_path / "sites" / "ai-tech" / "content" / "posts" / "post.md"
    index = tmp_path / "sites" / "ai-tech" / "content" / "posts" / "_index.md"
    manual = tmp_path / "sites" / "ai-tech" / "content" / "manuals" / "product" / "index.md"
    post.parent.mkdir(parents=True)
    manual.parent.mkdir(parents=True)
    post.write_text("# post", encoding="utf-8")
    index.write_text("# index", encoding="utf-8")
    manual.write_text("# manual", encoding="utf-8")

    targets = iter_targets(tmp_path, [], content_kind="posts")

    assert targets == [post]
