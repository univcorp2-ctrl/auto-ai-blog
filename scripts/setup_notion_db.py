import json
import urllib.request
import os

NOTION_TOKEN = "ntn_E43853346674S2T0YcUYVUCOGCQaOU4v7ZTyflXB8Sx5JL"
NOTION_PAGE_ID = "38f10562e58b80b793a3c310eb9e4584"
STATE_FILE = ".notion_db_state"

def create_database():
    url = "https://api.notion.com/v1/databases"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": { "type": "page_id", "page_id": NOTION_PAGE_ID },
        "title": [ { "type": "text", "text": { "content": "自動生成LP一覧（テーマ別）" } } ],
        "properties": {
            "タイトル": { "title": {} },
            "テーマ": { "select": {} },
            "公開URL": { "url": {} }
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            db_id = res_data["id"]
            with open(STATE_FILE, "w") as f:
                f.write(db_id)
            print(f"Successfully created Database! ID: {db_id}")
            return db_id
    except urllib.error.HTTPError as e:
        print(f"Failed to create DB: {e}")
        print(e.read().decode())
        return None

if __name__ == "__main__":
    create_database()
