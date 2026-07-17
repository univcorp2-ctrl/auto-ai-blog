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
    log_text = """【自動タスク 実行結果 (Iteration 19)】
- テーマ：「カゴ落ちを防ぐ：購入の壁をゼロにする『フリクションレス・チェックアウト』」
- アクション：
  1. カスタマージャーニーの最終関門である決済時の摩擦（フリクション）を極限まで減らす戦略に関する記事を生成・保存
  2. 決済の障壁がなくなり、光のトンネルを滑らかに通過していくような高品質な新規アイキャッチ画像を生成・保存
  3. GitHubのmainブランチへのプッシュを完了（Cloudflare Pagesによる自動デプロイがトリガーされています）"""
    append_log_to_notion(log_text)
