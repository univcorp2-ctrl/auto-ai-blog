# AI Blog Carrier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a carrier-style publishing system where external AIs can submit posts and images, route them to the correct Hugo site, publish free/paid marketing pages, and deploy to production.

**Architecture:** Add a Cloudflare Worker ingest API for remote AI投稿, a local incoming importer for file-based投稿, shared routing/product/budget modules, and Hugo pages for free/paid conversion. Existing Cloudflare Pages deploy script remains the production publish path.

**Tech Stack:** Python 3, Hugo/PaperMod, Cloudflare Pages, Cloudflare Worker, GitHub Contents API, Stripe Payment Links configuration, optional OpenAI image generation via API key.

---

### Task 1: Shared Routing and Product Configuration

**Files:**
- Create: `generator/routing.py`
- Create: `generator/products.yaml`
- Create: `generator/product_pages.py`
- Test: `tests/test_routing_and_products.py`

- [ ] Write failing tests for category-to-site routing and product loading.
- [ ] Implement routing helpers using existing `generator/config.yaml`.
- [ ] Add product metadata, free summaries, paid offer copy, and Stripe link placeholders.
- [ ] Generate Hugo landing/success pages from product metadata.

### Task 2: Incoming File Importer

**Files:**
- Create: `scripts/import_incoming_posts.py`
- Modify: `.gitignore`
- Test: `tests/test_import_incoming_posts.py`

- [ ] Write failing tests for importing JSON/Markdown into the right site.
- [ ] Implement `incoming/` scanning, front matter generation, optional image copy, and archive-on-success.
- [ ] Connect importer to build/deploy script for unattended publishing.

### Task 3: Cloudflare Worker Ingest API

**Files:**
- Create: `workers/post-ingest/wrangler.toml`
- Create: `workers/post-ingest/src/worker.js`
- Create: `workers/post-ingest/README.md`
- Test: `workers/post-ingest/test/worker.test.mjs`

- [ ] Implement `GET /health`.
- [ ] Implement `POST /api/posts` with bearer/API-key auth.
- [ ] Route category to site path.
- [ ] Commit Markdown/images to GitHub using the Contents API.
- [ ] Optionally generate an image from `cover_image_prompt` when `OPENAI_API_KEY` is configured.

### Task 4: Budget Guards and Daily Automation

**Files:**
- Create: `generator/budget.py`
- Create: `scripts/run_daily_guarded.py`
- Test: `tests/test_budget.py`

- [ ] Add local daily/weekly budget counters for article and image generation.
- [ ] Ensure external AI submissions can publish without consuming generation budget.
- [ ] Update daily run entrypoint to respect the guard and still deploy existing approved content.

### Task 5: Verification and Deploy

**Files:**
- Modify: `README_ja.md`
- Modify: `docs/cloud-mode.md`

- [ ] Run `pytest`.
- [ ] Run `ruff check .`.
- [ ] Build all Hugo sites.
- [ ] Deploy all Cloudflare Pages sites.
- [ ] Deploy Worker when Cloudflare/GitHub secrets are available.
- [ ] Verify production URLs and report links.
