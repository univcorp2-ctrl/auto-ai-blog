# アーキテクチャ詳細

このシステムは、ローカル PC 上の AI CLI を使って日本語ブログ記事を自動生成し、Hugo 静的サイトとして Cloudflare Pages へ自動デプロイする構成です。

AI API は使用しません。Python からは `subprocess` で CLI を起動するだけです。

```mermaid
flowchart LR
    subgraph Local[ローカル Windows PC]
        TS[Windows タスクスケジューラ]
        BAT[run_daily.bat]
        PY[generator/generate.py]
        CLI1[Claude CLI]
        CLI2[Gemini CLI]
        CLI3[Codex CLI]
        POSTS[hugo-site/content/posts]
    end

    subgraph GitHub[GitHub]
        REPO[auto-ai-blog repository]
        ACTIONS[GitHub Actions Build Check]
    end

    subgraph Cloudflare[Cloudflare Pages]
        BUILD[Hugo Build]
        CDN[Global CDN]
    end

    TS --> BAT --> PY
    PY --> CLI1
    CLI1 -->|fail| CLI2
    CLI2 -->|fail| CLI3
    PY --> POSTS
    POSTS --> REPO
    REPO --> ACTIONS
    REPO --> BUILD --> CDN
```

## 処理フロー

1. Windows タスクスケジューラが毎朝 9:00 に `run_daily.bat` を起動します。
2. `generator/generate.py` が `topics.yaml` から次のトピックを選択します。
3. Claude CLI でドラフトを生成します。
4. Claude が失敗したら Gemini、さらに失敗したら Codex にフォールバックします。
5. Gemini CLI でレビューと改善を行います。
6. Gemini が失敗したら Codex にフォールバックします。
7. Codex CLI で最終チェックします。
8. Codex が失敗した場合はレビュー済み版を採用します。
9. Hugo front matter を付与して Markdown を保存します。
10. `git add`、`git commit`、`git push` を実行します。
11. Cloudflare Pages が GitHub の変更を検知して自動デプロイします。

## フォールバック設計

```mermaid
flowchart TD
    A[Draft: Claude] -->|success| B[Review: Gemini]
    A -->|fail| A2[Draft: Gemini]
    A2 -->|fail| A3[Draft: Codex]
    A3 -->|fail| X[記事生成スキップ + error log]
    B -->|success| C[Final: Codex]
    B -->|fail| B2[Review: Codex]
    B2 -->|fail| C2[Draft を採用]
    C -->|success| D[記事保存]
    C -->|fail| D2[改善版を採用して記事保存]
```

## GitHub Actions

GitHub Actions は記事生成を行いません。Python lint、unit test、Hugo build、artifact upload だけを担当します。

Workflow 本体のテンプレートは `docs/daily-post.yml` にあります。

## Cloudflare Pages

推奨 build command:

```bash
cd hugo-site && git submodule update --init --recursive || true; if [ ! -d themes/PaperMod ]; then git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git themes/PaperMod; fi; hugo --gc --minify
```

Output directory:

```text
hugo-site/public
```
