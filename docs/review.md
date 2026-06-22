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

### 2. フォールバック

ドラフト生成は Claude → Gemini → Codex、レビューは Gemini → Codex、最終チェックは Codex です。最終チェック失敗時は改善版を採用します。

### 3. エラーログ

`generator/logs/generate.log` にログを出力します。全 CLI が失敗してドラフトが作れない場合は記事生成をスキップし、終了コード `2` を返します。

### 4. Hugo front matter

テストで title、date、draft、tags、categories、description の付与を確認しています。

### 5. Git 処理

`generator/generate.py` の最後で以下を実行します。

```text
git add hugo-site/content/posts/ generator/.state.json
git commit -m "📝 新記事: {title}"
git push origin main
```

push は最大3回リトライします。

### 6. GitHub Actions

Workflow 定義は `docs/daily-post.yml` に退避しています。`.github/workflows/daily-post.yml` への直接書き込みは、今回の GitHub API 権限で 404 になりました。

### 7. Cloudflare Pages

README と docs/setup.md に Build command、Build output directory、Production branch、baseURL 変更方法を明記しました。

## 注意点

PaperMod は `.gitmodules` を入れています。ただし、この自動ファイル作成環境では Git の submodule gitlink を直接作成できないため、CI と Cloudflare Pages の build command には clone フォールバックを入れています。

## 判定

アプリ本体・記事生成器・Hugo サイト・テスト・ドキュメントは初期運用可能な状態です。残る手動作業は Cloudflare Pages の接続、ローカル PC への Hugo / AI CLI インストール、Windows タスクスケジューラ登録、GitHub Actions workflow ファイルの有効化です。
