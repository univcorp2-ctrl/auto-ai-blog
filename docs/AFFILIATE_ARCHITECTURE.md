# Affiliate Growth Agent Architecture

## 目的

既存のHugo/PaperMod公開基盤とPython生成器を維持したまま、通信費・固定費診断から成果計測までを追加する。外部副作用は人間承認の後に限定し、条件不明は停止する。

## 構成

1. **Diagnosis UI**: `sites/business/content/diagnosis/`。個人情報なしの概算入力。
2. **Program Ledger**: JSON台帳。A8管理画面で確認した値を手入力する。
3. **Scoring Engine**: `affiliate_agent/scoring.py`。期待承認報酬、期待クリック価値、推奨CPC。
4. **Compliance Gate**: `affiliate_agent/compliance.py`。active、鮮度、媒体登録、掲載条件、PR、人間承認をfail-closedで検査。
5. **First-party Analytics**: ブラウザlocalStorage。page_view、diagnosis_start、diagnosis_complete、offer_impression、affiliate_clickのみ。
6. **Experiment Layer**: 匿名IDによる安定割当。見出し、CTA、案件順を変更する。
7. **Operations Dashboard**: シミュレーションと手入力確定実績を分離する。
8. **Agent Workflow**: Opportunity Scout → Compliance Auditor → Diagnosis Builder → Content Repurposer → Analytics Optimizer。全出力はdraft。

## 安全境界

A8ログイン、Cookie保存、認証後画面の回避スクレイピング、大量提携申請、広告課金、購入、メール、SNS投稿は実装しない。X/TwitterへのA8広告直接掲載は候補外とし、許可SNSでも媒体登録と案件固有条件を必須にする。

## 公開前ゲート

`active=true`、確認日がTTL以内、媒体登録済み、対象チャネル許可、PR文言あり、実URLあり、`human_approved=true` の全条件が必要。paid searchではリスティング許可と商標除外確認も必要。
