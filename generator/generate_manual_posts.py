from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.cli_runner import call_with_fallback
from generator.config_loader import load_yaml
from generator.git_ops import commit_and_push
from generator.markdown_post import build_post_markdown, save_post
from generator.models import Topic
from generator.runtime import JST, repo_root, setup_logging

# List of manuals and their attributes
MANUALS = [
    {
        "filename": "automated_investment_affiliate_manual.md",
        "title": "完全放置型・投資アフィリエイト自動化マニュアル",
        "category": "AI・テック",
        "keywords": ["アフィリエイト自動化", "投資アフィリエイト", "AI活用", "不労所得"],
        "myasp_id": "INVESTMENT_AFFILIATE_MYASP_ID",
    },
    {
        "filename": "auto_saas_affiliate_manual.md",
        "title": "海外SaaS＆ノーコードツール特化型・全自動AIブログアフィリエイト構築マニュアル",
        "category": "AI・テック",
        "keywords": ["海外SaaS", "ノーコードツール", "ブログアフィリエイト", "AI自動化"],
        "myasp_id": "SAAS_AFFILIATE_MYASP_ID",
    },
    {
        "filename": "pinterest_passive_income_machine_manual.md",
        "title": "ピンタレスト不労所得マシーン 構築マニュアル",
        "category": "AI・テック",
        "keywords": ["Pinterest", "Etsy販売", "デジタル商品", "AI画像生成"],
        "myasp_id": "PINTEREST_MACHINE_MYASP_ID",
    },
    {
        "filename": "niche_matching_system_manual.md",
        "title": "超ニッチ業種特化型マッチングシステム構築マニュアル",
        "category": "不動産マーケティング",
        "keywords": ["マッチングサービス", "Stripe決済", "LINE Bot", "無人化ビジネス"],
        "myasp_id": "NICHE_MATCHING_MYASP_ID",
    },
    {
        "filename": "vps_setup_manual.md",
        "title": "完全無人AIトレードBot VPS環境構築マニュアル",
        "category": "AI・テック",
        "keywords": ["VPS構築", "Ubuntuサーバー", "自動取引Bot", "アービトラージ"],
        "myasp_id": "VPS_SETUP_MYASP_ID",
    },
    {
        "filename": "ai_dance_video_manual.md",
        "title": "AI美女ダンス動画量産・収益化マニュアル",
        "category": "AI・テック",
        "keywords": ["AI美女", "ダンス動画", "AnimateDiff", "TikTok収益化"],
        "myasp_id": "AI_DANCE_VIDEO_MYASP_ID",
    },
    {
        "filename": "real_estate_ghost_story_manual.md",
        "title": "不動産怪談YouTubeチャンネル立ち上げ・収益化マニュアル",
        "category": "不動産投資",
        "keywords": ["不動産怪談", "YouTube自動化", "ゆっくり解説", "ずんだもん"],
        "myasp_id": "GHOST_STORY_MYASP_ID",
    },
]


def load_manual_state(root: Path) -> dict[str, int]:
    path = root / "generator" / ".manual_state.json"
    if not path.exists():
        return {"next_manual_index": 0}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"next_manual_index": 0}


def save_manual_state(root: Path, state: dict[str, int]) -> None:
    path = root / "generator" / ".manual_state.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_manual_promo_prompt(manual_title: str, manual_content: str, myasp_id: str) -> str:
    return f"""
以下は販売用の有料ノウハウマニュアル「{manual_title}」の内容です。
このマニュアルの魅力を伝え、ブログ読者に購入を促すための、高品質なSEOに配慮した紹介・販促ブログ記事（日本語）を書いてください。

--- マニュアル内容 ---
{manual_content}
----------------------

### 構成要件：
1. 最初の行に H1 見出しとして、読者を惹きつける魅力的なタイトルを記述してください（例：【完全放置】AIでPinterestからEtsyへ自動誘導！ドルを稼ぐ不労所得マシーン構築法）。
2. 本文構成：
   - 導入：ターゲット読者の悩み（副業で時間が取れない、不労所得を作りたいなど）に寄り添い、このマニュアルがどう解決するかを提示。
   - 本論：マニュアルの核心となるアプローチや、なぜこの手法が今チャンスなのか（競合の少なさ、自動化の容易さなど）を3〜4個のセクションに分けて解説する（各セクションに必ずH2見出しを付けること）。
   - マニュアル詳細：どのような内容がマニュアル（目次、具体的な構成要素など）に含まれているかを紹介する。
   - まとめとCTA（行動喚起）：最後に購入を促す熱いメッセージとともに、以下の購入リンクボタンを必ず配置する。

### CTAボタンの挿入ルール：
記事の最後（まとめの直後）に、以下のHTML形式の購入ボタンを正確に挿入してください。
---
<div style="text-align: center; margin: 35px 0;">
  <a href="https://www.yurubusi-web.com/dm/ent/e/{myasp_id}/s/" target="_blank" style="background-color: #28a745; color: white; padding: 15px 30px; font-size: 22px; font-weight: bold; text-decoration: none; border-radius: 5px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: background-color 0.3s;">
    今すぐマニュアルを購入する
  </a>
  <p style="font-size: 13px; color: #666; margin-top: 10px;">※本マニュアルの購読用リンクは準備中です。詳細は <a href="https://yurui-business.com/contact/" target="_blank">お問合せ</a> よりご連絡ください。</p>
</div>
---

### 重要：
- 文字数は 2000〜3000字程度 としてください。
- 専門的でありながら親切で行動を促すトーンで執筆してください。
- front matter は絶対に付けないでください。
"""


def generate_manual_promo_post(root: Path, dry_run: bool = False) -> Path | None:
    setup_logging(root)
    config = load_yaml(root / "generator" / "config.yaml")
    state = load_manual_state(root)

    index = state.get("next_manual_index", 0) % len(MANUALS)
    manual_info = MANUALS[index]

    manual_path = root / "generator" / "source_manuals" / manual_info["filename"]
    if not manual_path.exists():
        logging.error("Manual source file not found: %s", manual_path)
        return None

    logging.info("Selected manual %s/%s: %s", index + 1, len(MANUALS), manual_info["title"])
    manual_content = manual_path.read_text(encoding="utf-8")

    generation_config = config.get("generation", {})
    blog_config = config.get("blog", {})
    git_config = config.get("git", {})
    timeout = int(generation_config.get("cli_timeout_seconds", 120))

    prompt = make_manual_promo_prompt(
        manual_info["title"],
        manual_content,
        manual_info.get("myasp_id", "REPLACE_WITH_YOUR_MYASP_LINK"),
    )

    # Call AI CLI (Codex is the primary choice as per configs)
    result = call_with_fallback(["codex"], prompt, timeout, "manual_draft")
    if not result.ok:
        logging.error("Codex execution failed for manual promo post: %s", result.error)
        return None

    now = datetime.now(JST).replace(microsecond=0)
    topic_obj = Topic(
        topic=manual_info["title"],
        keywords=manual_info["keywords"],
        category=manual_info["category"],
    )

    post_markdown, title = build_post_markdown(result.output, topic_obj, blog_config, now)
    post_path = save_post(root, post_markdown, title, now, topic_obj, blog_config)

    # Update state
    state["next_manual_index"] = (index + 1) % len(MANUALS)
    save_manual_state(root, state)

    # Git push
    commit_and_push(root, f"販促記事: {title}", git_config, dry_run=dry_run)
    return post_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate blog posts pitching Notion manuals.")
    parser.add_argument("--dry-run", action="store_true", help="Generate post but skip git push.")
    args = parser.parse_args()

    root_dir = repo_root()
    try:
        res = generate_manual_promo_post(root_dir, dry_run=args.dry_run)
        if res:
            print(f"Successfully generated promo post: {res}")
            sys.exit(0)
        else:
            print("Failed to generate promo post.")
            sys.exit(1)
    except Exception as exc:
        logging.exception("Failed to run manual post generator: %s", exc)
        sys.exit(2)
