import urllib.request
import json
import datetime

NOTION_TOKEN = "ntn_E43853346674S2T0YcUYVUCOGCQaOU4v7ZTyflXB8Sx5JL"
TARGET_PAGE_ID = "38d10562-e58b-819b-be2f-f6e7b55866c9"

def append_log_to_notion(content):
    url = f"https://api.notion.com/v1/blocks/{TARGET_PAGE_ID}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_text = f"[{now_str}] 実行ログ\n{content}"
    
    blocks = [
        {
            "object": "block",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": full_text}}]
            }
        }
    ]

    data = {"children": blocks}
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="PATCH")
    
    try:
        with urllib.request.urlopen(req) as response:
            print("Successfully logged to Notion page!")
    except urllib.error.HTTPError as e:
        print(f"Failed to log: {e}")
        print(e.read().decode())

if __name__ == "__main__":
    log_text = """【自動タスク 実行結果 (Iteration 17)】
- テーマ：「活字の1000倍の熱量：動画マーケティングがジャーニーを加速させる理由」
- アクション：
  1. カスタマージャーニーの全フェーズにおいて威力を発揮する「動画（ショート/長尺/VSL）」の活用戦略に関する記事を生成・保存
  2. （※画像生成APIの制限中のため、既存の高品質画像をアイキャッチとして設定）
  3. GitHubのmainブランチへのプッシュを完了（Cloudflare Pagesによる自動デプロイがトリガーされています）"""
    append_log_to_notion(log_text)
