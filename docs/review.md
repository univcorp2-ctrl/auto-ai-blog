# 実装レビュー記録

## レビュー日

2026-06-22

## 確認結果

### 1. AI API 不使用

`generator/generate.py` は AI API SDK を import していません。呼び出しは `subprocess.run()` のみです。

対応 CLI:

- `claude -p`
- `gemini -p`
- `codex -q`

Local Mode と Cloud Mode のどちらでもこの制約は同じです。

### 2. Local Mode

Local Mode は以下で動きます。

```text
Windows Task Scheduler → run_daily.bat → python generator/generate.py
```

ローカルPCにログイン済みの AI CLI と git 認証状態を使います。

### 3. Cloud Mode

Cloud Mode を追加しました。

```text
GitHub Actions / Cloud VM → scripts/cloud_prepare_ai_cli.sh → scripts/cloud_generate.sh → python generator/generate.py --cloud
```

Cloud Mode では以下を行います。

- `BLOG_EXECUTION_MODE=cloud` を設定
- git author を `github-actions[bot]` デフォルトで設定
- AI CLI のインストール確認
- 記事生成
- front matter 付与
- Markdown 保存
- `git commit` / `git push`
- Hugo build
- artifact upload
- 任意で Cloudflare Pages Deploy Hook 呼び出し

### 4. フォールバック

ドラフト生成は Claude → Gemini → Codex、レビューは Gemini → Codex、最終チェックは Codex です。最終チェック失敗時は改善版を採用します。

### 5. エラーログ

`generator/logs/generate.log` にログを出力します。全 CLI が失敗してドラフトが作れない場合は記事生成をスキップし、終了コード `2` を返します。

### 6. Hugo front matter

テストで title、date、draft、tags、categories、description の付与を確認しています。

### 7. Git 処理

`generator/generate.py` の最後で以下を実行します。

```text
git add hugo-site/content/posts/ generator/.state.json
git commit -m "📝 新記事: {title}"
git push origin {branch}
```

branch は `BLOG_GIT_BRANCH`、`generator/config.yaml` の `git.branch`、最後に `main` の順で決まります。

push は最大3回リトライします。

### 8. GitHub Actions

Workflow 定義は以下に保存しています。

- ビルド検証のみ: `docs/daily-post.yml`
- クラウド生成込み: `docs/workflows/cloud-daily-post.yml`

`.github/workflows/*.yml` への直接書き込みは、今回の GitHub API 権限で `404 Not Found` になりました。

### 9. Cloudflare Pages

README、docs/setup.md、docs/cloud-mode.md に以下を明記しました。

- Build command
- Build output directory
- Production branch
- baseURL 変更方法
- Deploy Hook の任意利用

### 10. 画像解説

README には以下15枚のSVG画像を追加しています。

1. 全体アーキテクチャ
2. ローカル毎日実行フロー
3. generate.py 内部処理
4. AI CLI フォールバック
5. 設定ファイルの役割
6. git push → Cloudflare Pages
7. Hugo build
8. エラー処理とログ
9. プログラム責務マップ
10. 初期設定と運用チェックリスト
11. Local + Cloud 二系統構成
12. Cloud Mode GitHub Actions
13. Cloud Secrets と CLI 認証
14. Cloudflare Deploy Hook
15. Cloud VM / self-hosted runner

## 注意点

PaperMod は `.gitmodules` を入れています。ただし、この自動ファイル作成環境では Git の submodule gitlink を直接作成できないため、CI と Cloudflare Pages の build command には clone フォールバックを入れています。

GitHub Actions workflow はテンプレートとして docs に保存済みですが、実際に Actions として起動するには `.github/workflows/` に配置できる権限が必要です。

## 判定

アプリ本体・記事生成器・Local Mode・Cloud Mode・Hugo サイト・テスト・ドキュメント・画像解説は初期運用可能な状態です。残る外部設定は、Cloudflare Pages 接続、ローカルまたはクラウド runner の AI CLI 認証、GitHub Actions workflow の有効化です。
