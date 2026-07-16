---
title: "pytestが30件通っても公開しない――AIブログ自動化を止めた4つの安全装置"
date: 2026-07-16T18:07:51+09:00
draft: false
tags:
  - "GitHub Actions"
  - "業務自動化"
  - "CI"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "自動化の価値は、記事を公開できた回数だけでは測れません。"
---
自動化の価値は、記事を公開できた回数だけでは測れません。

品質の低い記事、壊れたコード、タイムアウトした生成物を、公開前に止められた回数も重要です。とくにブログを収益資産として運用するなら、「動いたか」ではなく「公開してよい状態か」を判定する仕組みが欠かせません。

2026年7月16日、AIブログの自動生成パイプラインを検証したところ、次の結果になりました。

| 検証項目 | 実測結果 | 判定 |
|---|---:|---|
| pytest | 30件成功 | 通過 |
| ruff | 16件失敗 | 停止要因 |
| 記事生成 | 240秒でタイムアウト | 停止要因 |
| AIスロップ検査 | 5/8項目通過 | 公開基準未達 |
| 最終公開 | 実行せず | 正常な防御動作 |

テストが30件すべて成功していても、記事は公開しませんでした。

これは自動化の失敗ではありません。複数の検証を独立させ、「一つでも基準を満たさなければ公開しない」という設計が機能した結果です。

## 「テスト成功」と「公開可能」は別の状態

今回の結果で最も重要なのは、pytestの成功だけを見て公開判定をしなかったことです。

pytestが確認できるのは、主にプログラムが想定した入力に対して期待どおり動くかどうかです。しかし、次の問題までは保証しません。

- コード品質や保守性に問題がないか
- 生成処理が所定時間内に完了するか
- 記事に一次情報や具体例が含まれているか
- 読者にとって有用な内容になっているか
- 公開処理が二重に実行されないか
- Secretsや権限設定が安全か

つまり、30件のテスト成功は「30件の検証条件を満たした」という証拠であって、「公開してよい」という包括的な証明ではありません。

公開判定は、次のような複数のゲートを通過した結果として扱う必要があります。

```text
ソースコード
    ↓
自動テスト
    ↓
静的解析
    ↓
記事生成
    ↓
内容品質検査
    ↓
公開
    ↓
KPI計測
```

途中のどこかで失敗した場合は、公開処理へ進ませません。この「失敗時に安全側へ倒す」設計を、fail-closedと呼びます。

## 実測1：pytestは30件成功した

最初の検証では、pytestの対象となった30件がすべて成功しました。

```text
pytest: 30 passed
```

これは、少なくともテストで定義されていた機能について、明確な回帰が検出されなかったことを示します。

ただし、ここには限界があります。

テストされていない入力、外部APIの一時障害、生成内容の質、公開先の認証状態などは、通常の単体テストだけでは十分に確認できません。テスト件数そのものより、「収益や信用を損なう失敗をテストできているか」を確認する必要があります。

実務では、最低でも次のケースを追加します。

- 生成結果が空だった場合に公開しない
- 必須見出しが欠けていた場合に失敗させる
- 外部APIがタイムアウトした場合に再試行回数を制限する
- 同じ記事IDを二重公開しない
- dry-runでは公開APIを呼ばない
- Secretsが未設定なら処理開始前に停止する

## 実測2：ruffで16件の問題を検出した

pytestの成功後、ruffでは16件の違反が検出されました。

```text
ruff: 16 errors
```

静的解析の失敗を「見た目の問題」として無視してはいけません。

未使用の変数やimportだけなら、直ちに障害へつながらない場合もあります。しかし、例外処理の漏れ、曖昧な変数名、複雑すぎる分岐が混ざっていれば、将来の修正で不具合を埋め込む可能性が高まります。

ここで重要なのは、16件という数字だけで重大度を判断しないことです。修正時には、検出結果を次の3種類に分けます。

1. 実行結果に影響する問題
2. 保守性を下げる問題
3. プロジェクト方針上、明示的に除外できる問題

自動修正を使う場合も、いきなり全件を書き換えるのではなく、差分確認とpytestの再実行をセットにします。

```bash
ruff check .
ruff check . --fix
pytest -q
git diff --check
```

`--fix`で変更したあとにテストを再実行しなければ、静的解析だけ通って動作が変わる可能性があります。

## 実測3：記事生成が240秒でタイムアウトした

記事生成処理は240秒でタイムアウトしました。

```text
article generation: timeout after 240 seconds
```

この状態で最も危険なのは、「途中までファイルができているから使えるだろう」と判断して公開へ進めることです。

タイムアウト時の生成物には、次のような不整合が残る可能性があります。

- 記事本文が途中で切れている
- Markdownのコードブロックが閉じていない
- 画像URLだけが欠落している
- 品質検査用のメタデータが書き出されていない
- 一時ファイルと完成ファイルを区別できない

対策は、生成先と公開対象を分離することです。

```text
tmp/article-draft.md
        ↓ 検証成功時のみ
output/article-approved.md
        ↓
公開処理
```

生成開始時から完成ファイルへ直接書き込んではいけません。一時ファイルへ出力し、生成・構文・品質の検証がすべて成功した時点で、初めて公開対象へ昇格させます。

また、タイムアウト時間を長くするだけでは根本解決になりません。次の情報を計測して原因を切り分けます。

- AI APIの応答開始までの時間
- 応答完了までの時間
- 再試行回数
- 入出力トークン数
- Markdown整形や画像生成に要した時間
- 外部サービスごとの待機時間

生成時間を工程別に記録できれば、API応答が遅いのか、プロンプトが大きすぎるのか、後処理で止まっているのかを判断できます。

## 実測4：AIスロップ検査は5/8で公開停止

生成記事に対するAIスロップ検査は、8項目中5項目の通過でした。

```text
AI slop gate: 5/8
publication threshold: not met
```

ここでいうAIスロップとは、文章としては読めても、具体性、検証可能性、独自性が不足しているコンテンツです。

典型的には、次の特徴があります。

- 「重要です」「効果的です」といった抽象語が多い
- 実測値や失敗例がない
- 誰にでも当てはまる結論しかない
- 手順を読んでも再現できない
- 制約や失敗条件に触れていない
- 見出しを読んだだけで本文の内容が推測できる
- 一次情報と一般論が区別されていない
- 読者が次に取る行動が示されていない

今回、基準を5/8しか満たさなかった以上、そのまま公開しない判断が妥当です。

ただし、「8項目」という数だけを品質の保証として使うのも危険です。検査項目が曖昧なら、点数は簡単に形骸化します。それぞれを機械的に判定できる条件へ落とし込む必要があります。

たとえば「具体性があるか」ではなく、次のように定義します。

```text
- 実測値が1つ以上ある
- 実行日が明記されている
- 成功例と失敗例の両方がある
- 読者が試せるコマンドまたは手順がある
- この結果だけでは分からない限界が明記されている
```

品質基準は、感想ではなく検証可能な条件にすることが重要です。

## 公開ジョブは最後に一つだけ置く

安全なワークフローでは、テスト、静的解析、生成、内容検査を通過したあとにだけ、公開ジョブを実行します。

以下は設計の骨格を示す簡略例です。実際のコマンド名や公開方法は、各リポジトリに合わせて置き換えてください。

```yaml
name: Generate and publish article

on:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: blog-production
  cancel-in-progress: false

jobs:
  validate:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -q

      - name: Run static analysis
        run: ruff check .

  generate:
    needs: validate
    runs-on: ubuntu-latest
    timeout-minutes: 4

    steps:
      - uses: actions/checkout@v4

      - name: Generate draft
        env:
          AI_API_KEY: ${{ secrets.AI_API_KEY }}
        run: python scripts/generate_article.py --output tmp/article-draft.md

      - name: Validate article quality
        run: python scripts/check_article.py tmp/article-draft.md

      - name: Preserve diagnostic files
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: article-diagnostics
          path: |
            tmp/
            logs/
          if-no-files-found: ignore
          retention-days: 7

  publish:
    needs: generate
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Publish approved article
        env:
          PUBLISH_TOKEN: ${{ secrets.PUBLISH_TOKEN }}
        run: python scripts/publish_article.py
```

この構成では、`validate`または`generate`が失敗すると、依存する`publish`は実行されません。`needs`によって、前段ジョブの成功を公開の前提条件にできます。

また、`permissions`はワークフロー全体で読み取りに制限し、書き込みが必要な公開ジョブだけ権限を上げています。GitHub Actionsでは、`permissions`で明示しなかった権限は`none`として扱われます。詳細は[GitHub Actionsのワークフロー構文](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)を確認してください。

失敗時のログやテスト結果はArtifactとして保存できます。GitHubも、テスト結果、ログ、スクリーンショットなどをワークフローArtifactの代表的な用途として挙げています。[Workflow artifactsの公式資料](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts)も参考になります。

## 二重実行防止は「キャンセル」だけでは足りない

記事公開では、同じ処理の二重実行が売上集計や検索評価に影響します。

GitHub Actionsの`concurrency`を使えば、同じグループの実行を制御できます。ただし、`cancel-in-progress: true`にすると、実行中の公開処理を途中で中断する可能性があります。

公開処理に対しては、次の二段構えが安全です。

- ワークフロー側で同時実行を制限する
- アプリ側で記事IDや生成ハッシュを使い、公開済みか確認する

```python
if repository.is_already_published(article_id, content_hash):
    raise RuntimeError("Duplicate publication prevented")
```

外側の排他制御だけに依存せず、公開処理自体を冪等にするのが実務上の要点です。GitHub Actionsの同時実行制御については、[公式のconcurrency解説](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)で現在の構文を確認できます。

## Secretsは生成ジョブと公開ジョブで分ける

AI APIを呼ぶ権限と、記事を公開する権限は別物です。

一つのジョブにすべてのSecretsを渡すと、記事生成スクリプトの脆弱性や依存パッケージの問題が、そのまま公開権限の漏えいにつながります。

最低限、次のように分離します。

| ジョブ | 必要な秘密情報 | 不要な権限 |
|---|---|---|
| テスト | 原則なし | AI API、公開権限 |
| 記事生成 | AI APIキー | 公開権限 |
| 品質検査 | 原則なし | AI API、公開権限 |
| 公開 | 公開用トークン | AI APIキー |

Secretsは必要なジョブにだけ渡し、ログへ値を出力しないようにします。dry-runでも本番用トークンを渡さない設計が理想です。

## 失敗を収益改善に変える記録項目

安全装置は、止めるだけではコストになります。停止理由を記録し、改善へつなげることで初めて資産になります。

1回の実行ごとに、少なくとも次の情報を残します。

```json
{
  "run_date": "2026-07-16",
  "tests_passed": 30,
  "lint_errors": 16,
  "generation_timeout_seconds": 240,
  "ai_slop_checks_passed": 5,
  "ai_slop_checks_total": 8,
  "published": false,
  "failed_gates": [
    "lint",
    "generation",
    "content_quality"
  ]
}
```

これを蓄積すると、次のKPIを計算できます。

- 生成成功率
- 品質検査通過率
- 公開前停止率
- 失敗理由別の件数
- 1記事あたりの再生成回数
- 生成開始から公開可能になるまでの時間
- 公開後の収益や検索流入との相関

「何記事生成したか」だけでは、自動化の健全性は分かりません。「何件を、なぜ止めたか」まで記録する必要があります。

## 今回の結果から断定できないこと

今回の実測から確認できるのは、次の4点です。

- pytestの対象30件が成功した
- ruffが16件の問題を検出した
- 記事生成が240秒でタイムアウトした
- AIスロップ検査が5/8で公開基準を満たさなかった

一方、この情報だけでは、次のことまでは証明できません。

- 30件のテストが十分な網羅性を持つこと
- ruffの16件すべてが重大な不具合であること
- タイムアウトの原因がAI APIにあること
- AIスロップ検査の8項目が品質を完全に評価できること
- ワークフロー全体にセキュリティ上の問題がないこと
- 公開後の記事が必ず収益を生むこと

また、この記事で示したYAMLは安全設計の骨格であり、今回の実測に使用した設定ファイルそのものではありません。実測ログと実装例を混同しないことも、再現性を保つうえで重要です。

## 初心者が今日やるべきこと

最初から大規模な自動化基盤を作る必要はありません。まず、現在の公開処理の直前に一つだけ検証ゲートを追加してください。

おすすめは「生成物が空なら公開しない」という条件です。

```python
article = output_path.read_text(encoding="utf-8").strip()

if len(article) < 1000:
    raise RuntimeError("Article is too short; publication stopped")
```

次に、以下の順番で増やします。

1. 空ファイルと短すぎる記事を拒否する
2. pytestとruffが失敗したら公開しない
3. 生成処理にタイムアウトを設定する
4. Markdown構文と必須見出しを検査する
5. AIスロップ検査を数値化する
6. dry-runを追加する
7. 二重公開防止を実装する
8. 失敗ログをArtifactとして保存する
9. 公開ジョブの権限を最小化する
10. 公開後のKPIと失敗理由を同じ実行IDで追跡する

最初の目標は、完全自動公開ではありません。

「危険な生成物を、自動で公開しない」状態を作ることです。

## 自動化の完成度は、止まれるかどうかで決まる

2026年7月16日の検証では、pytestは30件成功しました。しかし、ruffの16件失敗、240秒の生成タイムアウト、AIスロップ検査5/8という結果を受け、公開は停止されました。

表面的には失敗の多い実行です。しかし、収益資産を守るという観点では、安全装置が期待どおり機能した実行でもあります。

AIブログ自動化で本当に危険なのは、処理が止まることではありません。

品質が不足しているのに、成功したように見えて公開されることです。

公開本数を増やす前に、失敗を検出し、証拠を残し、安全側へ停止できる仕組みを作る。そのうえで停止理由をデータ化し、生成品質と収益性を改善する。

それが、使い捨ての記事生成ではなく、長期的な収益資産として運用できる自動化の条件です。
