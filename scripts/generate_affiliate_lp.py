import sys
import os
from pathlib import Path
from datetime import datetime
import json
import urllib.request

# Add repo root to path
root = Path(__file__).resolve().parents[1]
sys.path.append(str(root))

from generator.cli_runner import call_with_fallback
from generator.git_ops import commit_and_push
from generator.markdown_post import make_slug

# Notion API Config
NOTION_TOKEN = "ntn_E43853346674S2T0YcUYVUCOGCQaOU4v7ZTyflXB8Sx5JL"
NOTION_DB_ID = os.environ.get("NOTION_DB_ID", "") # Needs to be set!

def save_to_notion(title, content, link):
    if not NOTION_DB_ID:
        print("Notion DB ID is missing. Skipping Notion upload.")
        return
        
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": { "database_id": NOTION_DB_ID },
        "properties": {
            "Name": {
                "title": [
                    { "text": { "content": title } }
                ]
            },
            "Link": {
                "url": link
            }
        },
        "children": [
            {
                "object": "block",
                "paragraph": {
                    "rich_text": [
                        { "text": { "content": content[:2000] } } # Notion limit
                    ]
                }
            }
        ]
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            print("Successfully saved to Notion!")
    except Exception as e:
        print(f"Failed to save to Notion: {e}")

def main():
    print("Starting affiliate LP generation...")
    
    # 1. Topic generation
    topic = "AIを活用した完全自動アフィリエイトの始め方とおすすめツール"
    keywords = ["AI", "アフィリエイト", "自動化", "副業"]
    
    # 2. AI Prompt
    prompt = f"テーマ「{topic}」について、読者が商品を購入したくなるような魅力的なランディングページ（ブログ記事）を作成してください。最低でも100文字以上で、読者の悩みに寄り添い、解決策を提示する構成にしてください。文章の最後に必ずアフィリエイトリンクのプレースホルダーとして「[特別割引での購入はこちら(アフィリエイトリンク)]」を入れてください。"
    
    result = call_with_fallback(["gemini", "codex", "claude"], prompt, 120, "lp_generation")
    if not result.ok:
        print(f"Error generating LP: {result.error}")
        return
        
    content = result.output
    
    # 3. Save to HP
    now = datetime.now()
    slug = make_slug(topic)
    file_path = root / "sites" / "business" / "content" / "posts" / f"{slug}-{now.strftime('%Y%m%d%H%M%S')}.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    frontmatter = f"""---
title: "{topic}"
date: {now.isoformat()}
draft: false
tags: {keywords}
---

{content}
"""
    file_path.write_text(frontmatter, encoding="utf-8")
    print(f"Saved HP post to {file_path}")
    
    # 4. Push to git (triggers Cloudflare pages deployment)
    try:
        commit_and_push(root, f"Add Affiliate LP: {topic}", {}, dry_run=False)
        print("Pushed to GitHub successfully.")
    except Exception as e:
        print(f"Git push failed: {e}")
    
    # 5. Notion Save
    save_to_notion(topic, content, "https://example.com/affiliate")

if __name__ == "__main__":
    main()
