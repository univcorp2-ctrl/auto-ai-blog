from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from generator import cli_runner, generate, markdown_post
from generator.generate import CliResult, Topic

JST = timezone(timedelta(hours=9))


def test_make_slug_has_hash_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(markdown_post, "slugify", lambda *_args, **_kwargs: "")
    slug = generate.make_slug("完全に日本語だけのタイトル")
    assert slug.startswith("post-")
    assert len(slug) == len("post-") + 12


def test_build_post_markdown_adds_hugo_front_matter() -> None:
    topic = Topic(
        topic="ChatGPTを不動産投資に活用する5つの方法",
        keywords=["ChatGPT", "不動産投資", "AI活用"],
        category="AI×不動産",
    )
    article = "# 魅力的な記事タイトル\n\n## 導入\n\nこれは本文です。初心者にも分かる内容です。"
    now = datetime(2026, 6, 22, 9, 0, tzinfo=JST)
    markdown, title = generate.build_post_markdown(article, topic, {"default_category": "AI・テック"}, now)

    assert title == "魅力的な記事タイトル"
    assert 'title: "魅力的な記事タイトル"' in markdown
    assert "date: 2026-06-22T09:00:00+09:00" in markdown
    assert "draft: false" in markdown
    assert '  - "ChatGPT"' in markdown
    assert '  - "AI×不動産"' in markdown
    assert not markdown.split("---", 2)[2].lstrip().startswith("# ")


def test_select_topic_rotates_with_state() -> None:
    topics = [
        Topic("A", ["a"], "cat"),
        Topic("B", ["b"], "cat"),
    ]
    index, topic = generate.select_topic(topics, {"next_index": 3})
    assert index == 1
    assert topic.topic == "B"


def test_call_with_fallback_uses_next_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_run_ai_cli(cli_name: str, prompt: str, timeout: int) -> CliResult:
        calls.append(cli_name)
        if cli_name == "claude":
            return CliResult(False, cli_name, "", "failed")
        return CliResult(True, cli_name, f"ok by {cli_name}")

    monkeypatch.setattr(cli_runner, "run_ai_cli", fake_run_ai_cli)
    result = generate.call_with_fallback(["claude", "gemini"], "prompt", 1, "draft")

    assert result.ok is True
    assert result.cli_name == "gemini"
    assert calls == ["claude", "gemini"]


def test_strip_front_matter() -> None:
    markdown = "---\ntitle: test\n---\n# Body\n\ncontent"
    assert generate.strip_front_matter(markdown).startswith("# Body")
