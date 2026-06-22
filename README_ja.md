# AI × 不動産 自動ブログ

Hugo + PaperMod + Python CLI 自動生成 + GitHub + Cloudflare Pages で動く、日本語 AI ブログ自動運用システムです。

AI API は一切使いません。記事生成はローカル PC にインストール済みの `claude` / `gemini` / `codex` CLI を `subprocess` で呼び出すだけです。

---

## 画像で読む全体像

### 1. システム全体アーキテクチャ

![Hugo + Cloudflare Pages 全自動AIブログ 全体アーキテクチャ](docs/images/01-architecture-overview.svg)

この図は、ローカル Windows PC で記事生成を行い、GitHub に push し、Cloudflare Pages が自動デプロイする全体の流れです。記事生成はローカルPCで完結し、GitHub Actions は生成ではなく検証を担当します。

### 2. 毎朝9時のローカル自動実行

![ローカル毎日実行フロー](docs/images/02-local-daily-flow.svg)

Windows タスクスケジューラが `run_daily.bat` を起動し、`generator/generate.py` を実行します。文字コードと作業ディレクトリをバッチで固定するため、日本語パスや日本語記事でも文字化けしにくい構成です。

### 3. generate.py の内部動作

![generator/generate.py 内部処理フロー](docs/images/03-generate-py-internal-flow.svg)

`generate.py` は、設定読み込み、トピック選択、AI CLI 呼び出し、front matter 生成、記事保存、git commit & push までを担当します。記事生成ロジックが1ファイルに集約されているため、運用時の確認箇所が明確です。

### 4. Claude / Gemini / Codex のフォールバック

![AI CLI フォールバック設計](docs/images/04-ai-cli-fallback.svg)

Claude が失敗したら Gemini、Gemini が失敗したら Codex、Codex が失敗した場合は直前の成果物を採用する設計です。全 CLI が失敗してドラフトすら作れない場合だけ、ログを残して記事生成をスキップします。

### 5. 各設定ファイルの役割

![設定ファイルとデータファイルの役割](docs/images/05-data-files-roles.svg)

`topics.yaml` は記事テーマ、`config.yaml` は生成条件、`prompts.py` はAIへの指示、`config.toml` はHugo公開設定を担当します。プログラムを触らずに運用調整しやすい構成です。

---

## プログラム別の動き

| ファイル | 役割 |
|---|---|
| `run_daily.bat` | Windows から Python を起動する入口。文字コードと作業ディレクトリを固定します。 |
| `generator/generate.py` | 記事生成の本体。トピック選択、CLI実行、front matter、保存、git pushを行います。 |
| `generator/prompts.py` | Claude / Gemini / Codex に渡すプロンプトを生成します。 |
| `generator/topics.yaml` | 1ヶ月分以上のトピック、SEOキーワード、カテゴリを管理します。 |
| `generator/config.yaml` | 文字数、CLI timeout、優先順位、git commit設定を管理します。 |
| `hugo-site/config.toml` | Hugo、PaperMod、日本語、SEO、RSS、sitemap、OGPを設定します。 |
| `hugo-site/content/posts/` | 生成された Markdown 記事が保存されます。 |
| `docs/daily-post.yml` | GitHub Actions workflow テンプレートです。 |

---

## ディレクトリ構成

```text
auto-ai-blog/
├── hugo-site/
│   ├── config.toml
│   ├── content/posts/
│   ├── static/
│   ├── themes/
│   ├── layouts/partials/extend_head.html
│   └── archetypes/default.md
├── generator/
│   ├── generate.py
│   ├── topics.yaml
│   ├── config.yaml
│   └── prompts.py
├── tests/
├── docs/
│   ├── images/
│   ├── architecture.md
│   ├── setup.md
│   ├── review.md
│   └── daily-post.yml
├── run_daily.bat
├── requirements.txt
├── requirements-dev.txt
├── CODEX.md
└── README_ja.md
```

---

## セットアップ

### 1. ローカル配置先

```powershell
G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog
```

```powershell
cd G:\マイドライブ\AI_Agents\github\repos
git clone --recursive <YOUR_REPOSITORY_URL> auto-ai-blog
cd auto-ai-blog
```

`--recursive` を付け忘れた場合:

```powershell
git submodule update --init --recursive
```

PaperMod が取得できない場合:

```powershell
git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git hugo-site/themes/PaperMod
```

### 2. Hugo Extended

```powershell
winget install Hugo.Hugo.Extended
hugo version
```

### 3. Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. AI CLI

Python から AI API は叩きません。以下の CLI のうち、使うものをローカル PC に入れてログインしておきます。

```powershell
claude -p "テスト"
gemini -p "テスト"
codex -q "テスト"
```

### 5. 手動実行

```powershell
.\run_daily.bat
```

### 6. Windows タスクスケジューラ登録

```powershell
$action = New-ScheduledTaskAction -Execute "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog\run_daily.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00am
Register-ScheduledTask -TaskName "auto-ai-blog" -Action $action -Trigger $trigger
```

---

## Cloudflare Pages 設定

| 項目 | 値 |
|---|---|
| Framework preset | Hugo |
| Build command | `cd hugo-site && git submodule update --init --recursive || true; if [ ! -d themes/PaperMod ]; then git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod; fi; hugo --gc --minify` |
| Build output directory | `hugo-site/public` |
| Root directory | 空欄、または repository root |
| Production branch | `main` |

Cloudflare Pages の詳しい画面操作は [`docs/setup.md`](docs/setup.md) を参照してください。

---

## GitHub Actions の役割

`.github/workflows/daily-post.yml` は記事生成を行いません。GitHub Actions 上では Claude / Gemini / Codex CLI が利用できない、またはログイン状態を保持できない可能性が高いためです。

Actions は以下だけを実行します。

- `ruff check .`
- `pytest`
- PaperMod テーマ取得
- Hugo ビルド検証
- `hugo-site/public` artifact upload

Workflow テンプレートは `docs/daily-post.yml` に保存しています。

---

## 生成記事の front matter

```yaml
---
title: "記事タイトル"
date: 2026-06-22T09:00:00+09:00
draft: false
tags:
  - "AI"
  - "不動産"
categories:
  - "AI×不動産"
description: "150字以内の meta description"
---
```

ファイル名:

```text
hugo-site/content/posts/YYYY-MM-DD-{slug}.md
```

---

## 本番運用に必要なもの

- GitHub リポジトリ
- Cloudflare Pages プロジェクト
- ローカル Windows PC
- Hugo Extended
- Python 3.12
- Claude / Gemini / Codex CLI のいずれか1つ以上
- ローカル PC で `git push origin main` できる認証状態

API キーを Python へ渡す必要はありません。

---

## 詳細ドキュメント

- [`docs/architecture.md`](docs/architecture.md): アーキテクチャ詳細
- [`docs/setup.md`](docs/setup.md): セットアップ手順
- [`docs/review.md`](docs/review.md): 実装レビュー
- [`docs/daily-post.yml`](docs/daily-post.yml): GitHub Actions workflow テンプレート
