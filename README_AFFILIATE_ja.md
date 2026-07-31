# A8成果計測型アフィリエイト・エージェント MVP

この追加機能は、既存のHugo＋Pythonブログを「記事生成」だけで終わらせず、無料診断、案件条件確認、匿名計測、実験、改善までつなぐための最小実働版です。累計100万円は目標値であり、収益を保証しません。

## 公開ページ

- `https://business-blog.pages.dev/diagnosis/`: 通信費・固定費診断
- `https://business-blog.pages.dev/affiliate-dashboard/`: ローカル匿名イベントのファネル確認

## ローカル確認

```powershell
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest tests/test_affiliate_agent.py
ruff check affiliate_agent tests/test_affiliate_agent.py
hugo --source sites/business --gc --minify
```

## A8管理画面から手入力する項目

`affiliate_agent/data/programs.demo.json` と `sites/business/static/data/affiliate-programs.demo.json` のDEMOをコピーし、program_id、案件名、カテゴリ、報酬、EPC、確定率、確定日数、リスティング条件、SNS条件、商標除外、登録媒体、広告URL、PR表示、最終確認日、activeを入力します。

案件条件が不明、期限切れ、媒体未登録、PR文言なし、URL未設定、人間未承認の場合は表示・遷移を停止します。A8のログイン情報、Cookie、管理画面の自動取得は扱いません。

## 数式

- 期待承認報酬 = 報酬額 × 確定率
- 期待クリック価値 = EPC × 確定率
- 推奨上限CPC = 期待クリック価値 × 0.55（変更可能）

EPCや確定率は過去実績であり、将来の成果を保証しません。A8上の発生、未確定、確定、入金を混同せず、ダッシュボードの実績は確定報酬だけを手入力します。

## 100万円のKPI分解例

平均確定単価が10,000円なら100件、17,500円なら約58件、7,000円なら約143件が必要です。必要クリック数は、確定CVR、案件CTR、診断完了率を逆算して設定します。最初の30日は売上額より、診断開始、完了、案件表示、クリック、確定の各落ち率を特定します。

## 人間が残すゲート

広告出稿、案件提携、実リンク公開、商標除外語、PR表記、記事の事実確認、SNS投稿は必ず人間が承認します。既定設定は `dry_run=true`、`human_approved=false` です。

詳細は `docs/AFFILIATE_OPERATIONS_PLAYBOOK.md` と `docs/AFFILIATE_30_DAY_PLAN.md` を参照してください。
