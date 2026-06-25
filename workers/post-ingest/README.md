# Auto AI Blog Post Ingest Worker

This Worker is the API gateway for external AI writers.

## Endpoints

- `GET /health`
- `POST /api/posts`

Authentication:

```http
Authorization: Bearer <INGEST_API_KEY>
```

Required secrets:

```bash
wrangler secret put INGEST_API_KEY
wrangler secret put GITHUB_TOKEN
```

Images are generated from the CLI before submission. Do not give `GITHUB_TOKEN` or
`OPENAI_API_KEY` to external writers. Give external writers only the ingest API
key, then run `scripts/submit_external_post.py` from this repository to generate
images and submit the finished payload.

```bash
set INGEST_API_KEY=<INGEST_API_KEY>
set OPENAI_API_KEY=<OPENAI_API_KEY>
python scripts/submit_external_post.py incoming\post.json
```

The Worker stores image data it receives. It does not generate article images.
The CLI can generate:

- `cover_image_base64` from `cover_image_prompt`
- `inline_images[].base64` from `inline_images[].prompt`

Use ASCII image IDs and insert them inside the article body with
`{{image:<id>}}`. The Worker replaces those placeholders with uploaded Markdown
image links.

All submissions must include the Notion-derived AI slop review. The normal path
is to use `scripts/submit_external_post.py`; it validates the article against
`generator/ai_slop_guidelines.json` and attaches `slop_review`. Direct API calls
without a review score of at least 8 are rejected with `422 ai_slop_review_required`.

Example:

```json
{
  "title": "AI副業の始め方",
  "category": "ビジネス・副業",
  "tags": ["AI", "副業"],
  "summary": "無料で読める概要です。",
  "body_markdown": "## 無料で読める内容\n\n本文...\n\n{{image:flow}}\n\n## まとめ\n\n本文...",
  "paid_teaser_markdown": "## 続きで学べる内容\n\n有料マニュアルの案内...",
  "product_id": "saas-affiliate",
  "cover_image_prompt": "Japanese editorial image about AI automation, no text",
  "slop_review": {
    "score": 8,
    "minimum_score": 8
  },
  "inline_images": [
    {
      "id": "flow",
      "alt": "AI記事投稿フロー",
      "prompt": "Diagram-style editorial image showing an AI article publishing flow, no text"
    }
  ]
}
```

External writers can also provide already generated images:

```json
{
  "body_markdown": "本文\n\n{{image:chart}}",
  "inline_images": [
    {
      "id": "chart",
      "alt": "比較図",
      "base64": "<PNG_BASE64>",
      "extension": ".png"
    }
  ]
}
```
