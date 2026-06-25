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

Optional secret:

```bash
wrangler secret put OPENAI_API_KEY
```

When `OPENAI_API_KEY` is configured, payloads with `cover_image_prompt` generate a cover image with OpenAI image generation. Payloads can also provide `cover_image_base64`, `cover_image_extension`, or `cover_image_url`.

Example:

```json
{
  "title": "AI副業の始め方",
  "category": "ビジネス・副業",
  "tags": ["AI", "副業"],
  "summary": "無料で読める概要です。",
  "free_body_markdown": "## 無料で読める内容\n\n本文...",
  "paid_teaser_markdown": "## 続きで学べる内容\n\n有料マニュアルの案内...",
  "product_id": "saas-affiliate",
  "cover_image_prompt": "Japanese editorial image about AI automation, no text"
}
```
