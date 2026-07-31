# Affiliate Data Schema

## Program ledger

| field | type | purpose |
|---|---:|---|
| program_id | string | A8内で識別できるID。公開してよい範囲だけ保存 |
| name | string | 運用上の案件名 |
| category | string | mobile / internet / electricity など |
| reward_yen | number | 発生成果報酬。税込・税別を運用メモで統一 |
| epc_yen | number | A8表示値を確認日に転記 |
| approval_rate | 0..1 | 55%なら0.55 |
| approval_days | integer | 確定までの目安日数 |
| listing_policy | string | ok / partial_ok / ng / unknown |
| sns_policy | string | ok / ng / unknown |
| trademark_bidding_policy | string | paid searchで除外確認済みならexcluded |
| media_registration_status | string | registered / unregistered |
| affiliate_url | string | 実素材URL。DEMOはexample.invalid |
| disclosure_text | string | PR・広告表示 |
| last_verified_at | YYYY-MM-DD | 条件を管理画面で確認した日 |
| active | boolean | 公開候補フラグ |

## Event schema

`event_name`, `occurred_at`, `session_id`, `variant_id`, `payload`。氏名、メール、電話、住所、郵便番号は保存しない。`affiliate_click`のpayloadにはprogram_idと期待承認報酬だけを入れる。

## Actual results

A8の発生と確定を区別する。公開ダッシュボードの実績欄には確定報酬累計と確定件数だけを手入力する。入金日は別のキャッシュフロー台帳で管理する。
