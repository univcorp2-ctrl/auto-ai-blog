# Affiliate Operations Playbook

## 案件登録

1. A8管理画面で報酬、EPC、確定率、確定日数、否認条件、リスティング、SNS、商標、登録媒体を確認する。
2. 公開してよい情報だけを台帳へ入力する。ログイン後限定情報を記事や公開リポジトリへ露出しない。
3. 最初は `active=false`、設定は `human_approved=false` のままテストする。
4. PR表記、比較根拠、広告URL、除外語、媒体登録を二者確認した後だけ有効化する。

## 日次・週次

- ページ閲覧→診断開始→完了→案件表示→クリックを確認。
- 案件終了、提携解除、URL異常があれば即停止。
- 日次予算または累計損失上限に達した実験を停止。
- 発生ではなく確定を基準に期待値を補正。
- 診断完了100件未満の小標本でA/B勝者を断定しない。
- CTR低下は診断結果と案件カテゴリの整合、確定率低下は成果条件と訴求のミスマッチを先に確認。

## 現行ルールの確認先

- `https://www.a8.net/compliance/listing.php`
- `https://www.a8.net/compliance/prohibited-matter.php`
- `https://www.a8.net/as/sns/`
- `https://support.a8.net/a8/as/faq/2025/post_2611.html`
- `https://support.a8.net/as/payment/`

条件は変わるため、公開ページだけで案件固有条件を確定しない。ログイン後の各プログラム詳細を人間が確認する。
