from __future__ import annotations

from textwrap import dedent


def draft_prompt(topic: str, keywords: list[str], min_chars: int, max_chars: int) -> str:
    keyword_text = "、".join(keywords)
    return dedent(
        f"""
        以下のトピックについて、SEOを意識した日本語ブログ記事を書いてください。

        トピック: {topic}
        文字数: {min_chars}〜{max_chars}字
        構成: 導入 → 本論（3〜5セクション、各H2見出し付き） → まとめ
        トーン: 専門的だが読みやすい。初心者にも分かるように。
        SEOキーワード: {keyword_text}
        出力: Markdown形式（見出し・箇条書き・太字を活用）

        重要:
        - 不確実な情報は断定しないでください。
        - 投資助言と誤解される表現は避け、一般的な情報提供として書いてください。
        - 最初の行に H1 見出しとして魅力的な記事タイトルを書いてください。
        """
    ).strip()


def review_prompt(draft: str) -> str:
    return dedent(
        f"""
        以下のブログ記事をレビューし、改善版を出力してください。

        チェック項目:
        1. 事実誤認がないか
        2. 論理の飛躍がないか
        3. SEO的に改善できる点（見出し構成、キーワード配置）
        4. 読みやすさ（文の長さ、段落分け）
        5. 導入文のフック（読者の興味を引けるか）

        改善した完成版の記事全文を Markdown で出力してください。
        front matter は付けないでください。

        --- 元記事 ---
        {draft}
        """
    ).strip()


def final_check_prompt(improved: str) -> str:
    return dedent(
        f"""
        以下のブログ記事の最終チェックをしてください。
        問題があれば修正した完成版を、なければそのまま出力してください。

        チェック項目:
        1. 誤字脱字
        2. Markdown の構文エラー
        3. 不自然な日本語表現
        4. 記事タイトルが魅力的か（クリックしたくなるか）

        修正済みの記事全文を Markdown で出力してください。
        front matter は付けないでください。

        --- 記事 ---
        {improved}
        """
    ).strip()
