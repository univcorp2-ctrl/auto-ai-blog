from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SlopCheck:
    name: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class SlopReport:
    score: int
    minimum_score: int
    passed: bool
    checks: list[SlopCheck]
    banned_hits: list[str]
    source_pages: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "minimum_score": self.minimum_score,
            "passed": self.passed,
            "checks": [check.__dict__ for check in self.checks],
            "banned_hits": self.banned_hits,
            "source_pages": self.source_pages,
        }


def load_guidelines(root: Path) -> dict[str, Any]:
    path = root / "generator" / "ai_slop_guidelines.json"
    if not path.exists():
        path = Path(__file__).resolve().parent / "ai_slop_guidelines.json"
    return json.loads(path.read_text(encoding="utf-8"))


def strip_front_matter(markdown: str) -> str:
    if markdown.startswith("---"):
        parts = markdown.split("---", 2)
        if len(parts) == 3:
            return parts[2]
    return markdown


def plain_text(markdown: str) -> str:
    body = strip_front_matter(markdown)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"!\[[^\]]*]\([^)]*\)", " image ", body)
    body = re.sub(r"\[[^\]]+]\([^)]*\)", " link ", body)
    body = re.sub(r"[#*_`>|]", " ", body)
    body = re.sub(r"\s+", " ", body)
    return body.strip()


def has_any(text: str, words: list[str]) -> bool:
    return any(word in text for word in words)


def has_grounded_number(text: str) -> bool:
    if not re.search(r"\d", text):
        return False
    grounding_words = ["実績", "確認", "出典", "データ", "ログ", "URL", "円", "%", "件", "日", "月", "年"]
    return has_any(text, grounding_words)


def find_banned_hits(text: str, banned_patterns: list[str]) -> list[str]:
    return [pattern for pattern in banned_patterns if pattern and pattern in text]


def evaluate_markdown(markdown: str, guidelines: dict[str, Any]) -> SlopReport:
    text = plain_text(markdown)
    banned_hits = find_banned_hits(text, [str(item) for item in guidelines.get("banned_patterns", [])])
    image_count = len(re.findall(r"!\[[^\]]*]\([^)]*\)", markdown))
    checks = [
        SlopCheck(
            "Hiroの実体験・固有データ",
            has_any(text, ["Hiro", "太田", "私", "実際", "ログ", "データ", "検証"]),
            "Hiro/太田/私/実際/ログ/データ/検証のいずれかを確認",
        ),
        SlopCheck(
            "一人称の具体エピソード",
            has_any(text, ["私は", "私が", "実際に", "今日", "昨日", "先週", "2026年"]),
            "一人称または日時付きの具体記述を確認",
        ),
        SlopCheck(
            "他者が書けない独自情報",
            has_any(text, ["このサイト", "このマニュアル", "実行ログ", "本番", "検証", "自動投稿", "API"]),
            "固有プロジェクトや実行結果に触れているか確認",
        ),
        SlopCheck("根拠ある数字", has_grounded_number(text), "数字と根拠語の同時出現を確認"),
        SlopCheck(
            "冒頭で役立つ",
            len(text[:500]) > 120 and has_any(text[:700], ["できる", "分かる", "確認", "手順", "解決", "作る"]),
            "冒頭700字以内に便益や手順があるか確認",
        ),
        SlopCheck("AI定型文体の回避", not banned_hits, f"禁止表現: {', '.join(banned_hits) if banned_hits else 'なし'}"),
        SlopCheck("視覚的証拠", image_count > 0 or has_any(text, ["スクリーンショット", "グラフ", "画像", "図解"]), "画像Markdownまたは視覚証拠語を確認"),
        SlopCheck("反論・限界・注意点", has_any(text, ["注意", "限界", "リスク", "使えない", "失敗", "対策"]), "注意点や失敗対策を確認"),
        SlopCheck("読後アクション", has_any(text, ["次に", "今すぐ", "ステップ", "チェック", "確認してください", "作ります"]), "読者の次アクションを確認"),
        SlopCheck("差別化", has_any(text, ["差別化", "独自", "他社", "類似", "このコンテンツ", "このマニュアル"]), "独自性や差別化表現を確認"),
    ]
    score = sum(1 for check in checks if check.passed)
    minimum_score = int(guidelines.get("minimum_score", 8))
    return SlopReport(
        score=score,
        minimum_score=minimum_score,
        passed=score >= minimum_score,
        checks=checks,
        banned_hits=banned_hits,
        source_pages=[dict(item) for item in guidelines.get("source_pages", [])],
    )


def assert_not_slop(markdown: str, guidelines: dict[str, Any]) -> SlopReport:
    report = evaluate_markdown(markdown, guidelines)
    if not report.passed:
        failed = ", ".join(check.name for check in report.checks if not check.passed)
        raise ValueError(f"AI slop validation failed: score={report.score}/{report.minimum_score}; failed={failed}")
    return report
