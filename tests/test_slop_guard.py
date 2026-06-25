from __future__ import annotations

from pathlib import Path

import pytest

from generator.slop_guard import assert_not_slop, evaluate_markdown, load_guidelines


def quality_markdown() -> str:
    return """---
title: "HiroのAI自動投稿検証ログ"
---

![検証画面](/images/posts/sample.png)

2026年6月26日、私はこのサイトの自動投稿APIで記事を1本送信し、本番URLで200が返るところまで確認しました。
Hiroの実行ログでは、Cloudflare Pagesへの反映、画像の表示、CTAクリック導線をそれぞれ確認しています。

## 実際にやった手順

1. incoming JSONを作る
2. scripts/submit_external_post.pyでスロップ検査を通す
3. 本番URLを確認する

## 注意点

この方法は、OPENAI_API_KEYがない環境では画像生成まで完了しません。その場合は画像プロンプトだけ保存し、次回キーを入れて再実行します。

## 差別化

このコンテンツにしかない情報は、実際の本番反映ログと、失敗時にどこで止まるかを明記している点です。
読者は次に、自分の記事JSONに画像と具体的な検証ログを1つ追加してください。
"""


def test_slop_guard_passes_grounded_content() -> None:
    root = Path(__file__).resolve().parents[1]
    report = evaluate_markdown(quality_markdown(), load_guidelines(root))

    assert report.passed
    assert report.score >= 8


def test_slop_guard_rejects_generic_content() -> None:
    root = Path(__file__).resolve().parents[1]
    markdown = "# AI活用のメリット\n\n重要なのはAIを活用することです。まとめると、効率化できます。"

    with pytest.raises(ValueError):
        assert_not_slop(markdown, load_guidelines(root))
