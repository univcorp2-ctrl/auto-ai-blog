import sys
import json
import urllib.request
import os

NOTION_TOKEN = "ntn_E43853346674S2T0YcUYVUCOGCQaOU4v7ZTyflXB8Sx5JL"
def save_to_notion(title, content, link, theme="その他"):
    # Read DB ID
    if not os.path.exists(".notion_db_state"):
        print("Notion DB not set up yet.")
        return
    with open(".notion_db_state", "r") as f:
        NOTION_DB_ID = f.read().strip()
        
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Split content into chunks to avoid 2000 character limit per block
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    blocks = []
    for chunk in chunks:
        blocks.append({ "object": "block", "paragraph": { "rich_text": [ { "text": { "content": chunk } } ] } })

    data = {
        "parent": { "database_id": NOTION_DB_ID },
        "properties": {
            "タイトル": { "title": [ { "text": { "content": title } } ] },
            "テーマ": { "select": { "name": theme } },
            "公開URL": { "url": link }
        },
        "children": blocks
    }
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            print("Successfully saved to Notion!")
    except urllib.error.HTTPError as e:
        print(f"Failed to save to Notion: {e}")
        print(e.read().decode())

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        save_to_notion(sys.argv[1], sys.argv[2], "https://example.com/affiliate", sys.argv[3])
    elif len(sys.argv) >= 3:
        save_to_notion(sys.argv[1], sys.argv[2], "https://example.com/affiliate", "AI副業")
