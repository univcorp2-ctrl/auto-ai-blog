import urllib.request
import json
import sys

NOTION_TOKEN = "ntn_E43853346674S2T0YcUYVUCOGCQaOU4v7ZTyflXB8Sx5JL"

def append_to_notion_page(page_id, content):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Split content into chunks
    chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
    blocks = []
    
    # Add a heading
    blocks.append({
        "object": "block",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "【AI分析】成功事例カスタマージャーニー"}}]
        }
    })
    
    for chunk in chunks:
        blocks.append({
            "object": "block",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}]
            }
        })

    data = {"children": blocks}
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="PATCH")
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Successfully appended to page {page_id}")
    except urllib.error.HTTPError as e:
        print(f"Failed to append: {e}")
        print(e.read().decode())

if __name__ == "__main__":
    analysis_text = """
1. 認知フェーズ（SNS集客）
- ストーリー：「私の悩み（課題）をわかってくれる！」という共感と、「こうなれる」という憧れを提示。
- 教育の仕組み：いきなり売り込まず、専門性（権威性）を示すコンテンツ（ショート動画、ビフォーアフター）でファン化させる。

2. 検討フェーズ（ブログ・Web媒体）
- ストーリー：SNSの「感情」からブログの「論理」への橋渡し。「なぜその手段（商品）が最適なのか」を証明する。
- 教育の仕組み：より深い成分解説、他社比較、デメリットの正直な開示などを行い、「失敗したくない」という不安を払拭する。

3. 決定フェーズ（キラーページ）
- ストーリー：「今、自分に必要なのはこれだ」と確信させる。
- 教育の仕組み：口コミ、限定性（今だけ）、権威の推薦を配置し、スムーズに購入導線（CTA）へ流す。

★応用パターン：
この一貫したストーリー（共感→論理的証明→後押し）を維持したまま、SNS用のキャッチーな画像作成と、ブログ・LP用の詳細な比較記事の作成を連動させることで、効果を最大化できる。
"""
    
    # Page 1: X投稿の内容を確認して実行可否を判断
    append_to_notion_page("38d10562-e58b-819b-be2f-f6e7b55866c9", analysis_text)
    
    # Page 2: 物件配信先コミュニティ開拓（配信先拡大）
    append_to_notion_page("38e10562-e58b-8127-8bbb-d56a00b2c24e", analysis_text)
    
    # Page 3: LINEと物件情報配信の自動連携
    append_to_notion_page("38e10562-e58b-819b-bb4b-dceeea8c3cb9", analysis_text)
