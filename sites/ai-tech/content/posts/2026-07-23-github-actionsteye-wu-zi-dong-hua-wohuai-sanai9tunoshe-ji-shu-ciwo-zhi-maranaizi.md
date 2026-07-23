---
title: "GitHub Actionsで業務自動化を壊さない9つの設計術｜CIを「止まらない自動化資産」に変える実践手順"
date: 2026-07-23T12:23:39+09:00
draft: false
tags:
  - "GitHub Actions"
  - "業務自動化"
  - "CI"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!GitHub Actionsで業務スクリプトを安全に運用する全体像https://image.pollinations.ai/prompt/secure%20GitHub%20Actions%20business%20automation%20workflow%20with%20CI%20test"
---
![GitHub Actionsで業務スクリプトを安全に運用する全体像](https://image.pollinations.ai/prompt/secure%20GitHub%20Actions%20business%20automation%20workflow%20with%20CI%20tests%20secrets%20monitoring%20and%20revenue%20dashboard%20professional%20infographic?width=800&height=400&nologo=true)

「毎朝CSVを集計してレポートを送る」「記事を生成して公開する」「価格や在庫を取得して通知する」。こうした業務自動化を始めても、担当者のパソコン上で動かしている限り、電源、通信、ログイン状態に左右されます。

GitHub Actionsへ移せば、GitHub上の実行環境で業務スクリプトを定期的、または特定の操作をきっかけに起動できます。しかし、単にcronを設定しただけでは、二重実行、秘密情報の漏えい、不完全なデータの公開、API利用料の暴走といった問題が起こり得ます。収益につながる処理ほど、誤作動したときの損失も大きくなります。

この記事では、**GitHub Actions、CI、Secrets、dry-run、ログ、KPI**を組み合わせ、担当者が毎回立ち会わなくても運用を継続できる設計を解説します。

目指すのは「一度も失敗しない仕組み」ではありません。失敗を自動検知し、危険な更新を止め、あとから原因を追跡できる仕組みです。これが整えば、集客記事の公開、アフィリエイトデータの更新、ポイント獲得条件の収集などを、時間の切り売りではない**自動化資産**へ近づけられます。

なお、自動化による収益やポイント獲得を保証するものではありません。成果は規約、需要、集客力、運用コストなどによって変わります。本記事は一般的な技術情報であり、特定サービスの規約適合性や収益性を保証するものではありません。

## GitHub ActionsとCIの全体像

GitHub Actionsは、リポジトリ内の `.github/workflows/*.yml` または `.github/workflows/*.yaml` に書いた手順を、GitHubのrunnerで実行する仕組みです。runnerとは、PythonやNode.jsなどを動かす実行環境です。

CIはContinuous Integrationの略で、変更を統合する前後にテストやビルドを自動実行する考え方です。例えば、記事公開スクリプトを実行する前に、リンク切れ、必須項目、生成物の形式を検査します。

役割を分けると理解しやすくなります。

| 要素 | 役割 | 具体例 |
|---|---|---|
| GitHub Actions | 決めた条件で処理を起動する | `main`へのpush、手動実行、定刻実行 |
| 業務スクリプト | 実際の仕事を処理する | CSV集計、記事生成、API取得 |
| CI | 壊れていないか検査する | pytest、lint、サイトビルド |
| Secrets | 秘密情報を保管する | APIキー、デプロイトークン |
| artifact | 結果を証拠として保存する | レポート、ビルド済みサイト、エラーログ |
| 通知 | 人間が見るべき例外を知らせる | 連続失敗、予算超過、データ欠損 |

安全な流れは、次の順序です。

**起動 → 入力確認 → テスト → dry-run → 本処理 → 出力検証 → 公開 → ログ保存 → 異常通知**

収益処理を先に実行し、最後に検査する構成では、誤った記事や価格を公開したあとで失敗に気づく可能性があります。公開、送信、購入、有料APIの呼び出しなど、副作用がある処理は検査に合格した後ろへ置きます。

## 最初に作るべき「事故の想定表」

YAMLを書く前に、何を防ぐのかを明確にします。少なくとも、次の4つは検討してください。

| 事故 | 起こり得る損失 | 防止策 | 検知方法 |
|---|---|---|---|
| 同じ処理の二重実行 | 二重投稿、重複課金 | `concurrency`、冪等性 | 実行キーの重複検査 |
| 不完全な成果物の公開 | 信頼低下、機会損失 | 出力検証、段階的デプロイ | 件数・必須項目・URL検査 |
| APIキーの漏えい | 不正利用、追加請求 | Secrets、最小権限 | secret scanning、利用履歴 |
| API利用量の暴走 | 想定外の請求 | 件数・回数・金額の上限 | 推定費用と実費の記録 |

この表がないと、「テストは通るが事業上は危険」という状態を見落とします。技術的な正常終了と、業務上の成功を分けて定義することが重要です。

## `auto-ai-blog`で確認した一次情報

この記事は一般論だけを並べたものではありません。2026年7月23日、Hiroが運用する `auto-ai-blog` リポジトリのworkflowとテストを実際に確認しました。

稼働用の `.github/workflows/daily-post.yml` では、次の構成を確認できました。

- 起動条件は`main`へのpushと`workflow_dispatch`
- `permissions`は`contents: read`と`deployments: write`
- Pythonは`3.12`、Node.jsは`22`
- Hugoは`0.163.3`に固定
- `ruff check .`の後に`pytest`を実行
- 検査通過後に`scripts/deploy_cloudflare_pages.py`を実行
- Cloudflareの認証情報はGitHub Secretsから環境変数へ渡す

実際の処理順は、概略として次のようになっています。

```yaml
- name: Python static check
  run: ruff check .

- name: Python tests
  run: pytest

- name: Build and deploy all Hugo sites to Cloudflare Pages
  env:
    CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
    CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
  run: python scripts/deploy_cloudflare_pages.py
```

別途用意されたCloud Mode用テンプレート `docs/workflows/cloud-daily-post.yml` では、次の項目を確認しました。

- UTCの`0 0 * * *`による定期起動
- `workflow_dispatch`から指定できるdry-run
- `timeout-minutes: 45`
- 重複実行を制御する`concurrency`
- 3つのHugoサイトのビルド
- `hugo-public-cloud`という名前でのartifact保存

さらに、次のコマンドをローカルで再実行しました。

```powershell
python -m pytest tests/test_deploy_config.py tests/test_cloud_mode.py tests/test_budget.py -q
```

結果は**8件すべて成功、終了コード0**でした。内訳は、予算関連2件、Cloud Mode関連4件、デプロイ設定関連2件です。

ただし、この結果が証明する範囲は限定的です。

- 証明できること：対象の予算ロジック、Cloud Mode、デプロイ設定に関するテストが現在の環境で通ること
- 証明できないこと：GitHub-hosted runner上での成功、Cloudflareへの実デプロイ成功、生成記事の品質、収益性
- 今回確認していないこと：GitHub Actionsのrun summary、実際のAPI利用額、公開後URLの疎通履歴

また、現在のファイルには改善余地もあります。

| 確認箇所 | 現在の状態 | 本番化前の改善候補 |
|---|---|---|
| 稼働用workflow | Hugoを`0.163.3`に固定 | 固定を維持し、更新手順を決める |
| Cloud Modeテンプレート | Hugoが`latest` | 稼働用と同じバージョンへ固定する |
| Cloud Modeテンプレート | dry-runの既定値が`false` | 初期導入時は`true`を検討する |
| 稼働用workflow | `concurrency`と`timeout-minutes`がない | 二重実行と長時間実行への対策を追加する |
| 稼働用workflow | artifact保存がない | 検証結果やビルド成果物を保存する |

「実際に使われているworkflow」と「将来利用するテンプレート」を混同しないことも重要です。テンプレートに安全策が書かれていても、稼働用workflowへ反映されていなければ、その安全策は本番では機能しません。

既存の入門記事との差別化点はここにあります。YAMLの書き方だけでなく、**「利益を生む処理」と「損失を止める検査」を同じworkflow内で分離する設計**まで扱います。

## ステップ・バイ・ステップで構築する

### 1. 自動化する業務を1行で定義する

最初に、入力、処理、出力を書き出します。

> 毎日取得した商品データを検査し、条件を満たす情報だけを記事へ反映する。

「売上を自動化する」では範囲が広すぎます。取得、判定、生成、公開、計測に分ければ、どこが失敗したか追跡できます。

併せて、副作用を分類します。

- 読み取り：APIからデータを取得する
- 内部書き込み：JSONやCSVを生成する
- 外部書き込み：記事を公開する、メールを送る
- 金銭影響：有料APIを呼ぶ、広告予算を変更する

後ろの項目ほど、厳しい検査と承認条件を置きます。

### 2. ローカルで再現できる入口を1つ作る

GitHub Actions専用の処理をYAMLへ大量に書くと、失敗時の再現が難しくなります。業務ロジックはPythonやShellへ置き、workflowから同じ入口を呼びます。

```yaml
- name: Run business automation
  run: python scripts/run_daily.py
```

ローカルでも `python scripts/run_daily.py` で動けば、GitHub Actionsの実行時間を消費せずに検証できます。OS差がある場合は、ファイルパス、文字コード、改行コード、タイムゾーンを明示してください。

入口を増やしすぎないことも重要です。手動実行、CI、本番実行で別々のスクリプトを使うと、「テストした処理と公開した処理が違う」という事故が起こります。

### 3. CIで「実行前に止める条件」を作る

最低限、静的検査、単体テスト、出力形式の検証を行います。

```yaml
- name: Static check
  run: ruff check .

- name: Unit tests
  run: pytest

- name: Validate output
  run: python scripts/validate_output.py
```

売上やポイントに影響する処理では、「正常終了したか」だけでは不足します。件数が0、合計金額が負数、公開URLが空欄といった異常値も失敗として扱います。

例えば、検証スクリプトには次のような業務条件を持たせます。

```python
from pathlib import Path
import json

output_path = Path("output/result.json")

if not output_path.exists():
    raise RuntimeError("result.json was not generated")

data = json.loads(output_path.read_text(encoding="utf-8"))
items = data.get("items", [])

if not items:
    raise RuntimeError("No publishable items were generated")

if len(items) > 100:
    raise RuntimeError("Item count exceeded the safety limit")

if any(not item.get("url") for item in items):
    raise RuntimeError("An item is missing its URL")
```

`100`という上限値は例です。実運用では、過去の件数、API料金、処理時間から決めてください。

### 4. 権限を最小化する

検証だけなら、書き込み権限は通常必要ありません。

```yaml
permissions:
  contents: read
```

デプロイが必要なら、書き込み権限をworkflow全体へ広げるのではなく、必要なjobにだけ付けます。

```yaml
jobs:
  test:
    permissions:
      contents: read

  deploy:
    needs: test
    permissions:
      contents: read
      deployments: write
```

GitHub公式ドキュメントでも、`permissions`をworkflowまたはjob単位で指定でき、利用可能な権限に`read`、`write`、`none`を設定できます。[Workflow syntax for GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax?apiVersion=2022-11-28)

外部クラウドが対応している場合は、固定された長期APIキーではなくOIDCも候補になります。OIDCを利用すると、workflow実行時に短期間だけ有効な認証情報を取得できるため、長期資格情報をGitHubへ保存せずに済む場合があります。[OpenID Connectの概要](https://docs.github.com/en/actions/concepts/security/openid-connect)

### 5. Secretsをコードから分離する

APIキーをYAMLやPythonへ直接書いてはいけません。Repository SecretsまたはEnvironment Secretsへ保存します。

```yaml
env:
  SERVICE_API_TOKEN: ${{ secrets.SERVICE_API_TOKEN }}
```

スクリプト側では存在確認だけを行います。

```python
import os

token = os.environ.get("SERVICE_API_TOKEN")
if not token:
    raise RuntimeError("SERVICE_API_TOKEN is not configured")
```

秘密値そのものはログへ出力しないでください。GitHubには登録された秘密情報をログ上で伏せる仕組みがありますが、秘密情報として登録していない値や変形された値まで、常に完全に隠せるとは限りません。[Secrets reference](https://docs.github.com/en/actions/reference/security/secrets)

本番用Secretsを扱うjobには、GitHub Environmentsによる承認ルールを設定する方法もあります。特に初期導入時は、テスト合格後に人間がデプロイを承認する構成が有効です。

### 6. dry-runで副作用を止める

dry-runとは、取得、計算、検証までは行うものの、公開や送信を実行しないモードです。

```yaml
on:
  workflow_dispatch:
    inputs:
      dry_run:
        description: "Skip external writes"
        type: boolean
        required: true
        default: true
```

実行stepでは、入力値を明示的に渡します。

```yaml
- name: Run automation
  env:
    DRY_RUN: ${{ inputs.dry_run }}
  run: python scripts/run_daily.py
```

初回導入、API変更後、権限変更後はdry-runから始めます。生成予定の記事、対象件数、推定API利用量をartifactへ保存し、人間が確認してから本番へ切り替えます。

完全自動化を目指す場合も、最初から監視なしで公開するのは危険です。dry-runの履歴が安定し、異常値の検査条件が固まった処理から段階的に無人化します。

### 7. 二重実行と暴走を防止する

定期処理と手動実行が重なると、同じ記事の二重公開やAPIの重複課金につながります。

```yaml
concurrency:
  group: daily-business-automation
  cancel-in-progress: false

jobs:
  run:
    timeout-minutes: 30
```

`cancel-in-progress: false`は、実行中の処理を途中で破棄したくない集計や公開処理に向きます。古い実行を中断しても安全な検査処理なら、`true`も選べます。

同じconcurrency groupに属する実行は、同時実行数が制御されます。group名は、意図しない別workflowとの競合を避けられる名前にしてください。[GitHub Actionsのconcurrency](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)

スクリプト側にも冪等性を持たせます。冪等性とは、同じ処理を複数回実行しても結果が重複しない性質です。例えば「日付＋商品ID」を一意キーにして、公開済みならスキップします。

```python
run_key = f"{target_date}-{product_id}"

if run_key in published_keys:
    print(f"skip: already published: {run_key}")
    return
```

GitHub Actions側の二重実行防止だけに依存してはいけません。手動再実行、通信タイムアウト後の再送、外部API側の遅延でも重複は起こり得ます。

### 8. 出力検証後に公開する

「Pythonが終了コード0を返した」と「正しい成果物ができた」は別です。公開前に、次を確認します。

- 必須ファイルが存在する
- 件数が想定範囲内に収まっている
- 更新時刻が今回の実行時刻と一致する
- 空文字、重複、異常値がない
- dry-runでは外部更新が発生していない
- 公開後のURLがHTTP成功を返す

収益導線を含む記事なら、商品リンク、CTA、計測パラメーターも検査対象です。リンクが壊れたまま自動投稿を続けると、処理は成功していても収益機会を失います。

公開前検査と公開後検査は分けてください。

- 公開前検査：ファイル内容、リンク形式、必須項目、重複
- 公開後検査：HTTPステータス、ページタイトル、計測タグ、反映時刻

公開後検査に失敗した場合に、再デプロイするのか、直前の版へ戻すのか、手動対応へ切り替えるのかも事前に決めます。

### 9. ログとartifactを残す

ログには秘密情報を含めず、判断に必要な項目を構造化して出します。

```json
{
  "status": "success",
  "input_count": 120,
  "published_count": 3,
  "skipped_count": 117,
  "estimated_cost_yen": 42,
  "external_write_performed": true,
  "run_key": "2026-07-23-daily"
}
```

上記の数字は形式例であり、実測値ではありません。実運用ではAPI料金表と実行ログから算出してください。

レポートや生成物はartifactとして保存します。

```yaml
- name: Upload validation report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: validation-report-${{ github.run_id }}
    path: |
      output/run_summary.json
      output/validation_report.json
    retention-days: 30
```

`if: always()`を付けると、前段が失敗した場合にも、生成済みの診断情報を保存できます。ただし、存在しないファイルを指定した場合の挙動も確認してください。

保存期間には上限があります。GitHub公式情報では、artifactとログの既定保持期間は90日ですが、リポジトリ種別や組織設定によって変更可能な範囲が異なります。[artifactとログの保持期間](https://docs.github.com/en/organizations/managing-organization-settings/configuring-the-retention-period-for-github-actions-artifacts-and-logs-in-your-organization)

![GitHub Actionsの安全な自動化フロー図](https://image.pollinations.ai/prompt/step%20by%20step%20secure%20CI%20pipeline%20trigger%20validation%20dry%20run%20business%20script%20deployment%20artifact%20monitoring%20clean%20Japanese%20infographic?width=800&height=400&nologo=true)

## 専門家目線のチェックポイント

### 外部送信の直前に境界を置く

テストと本処理を同じ関数へ混在させると、テスト中にメールや投稿が送信される事故が起こります。取得・変換・判定は副作用のない関数にし、公開・送信だけを別関数へ分離します。

```python
data = fetch_data()
result = transform_and_validate(data)

if dry_run:
    save_preview(result)
else:
    publish(result)
```

この境界が明確なら、テストでは`transform_and_validate()`までを検証し、本番の外部送信だけを差し替えられます。

### actionの参照方法を確認する

`uses: owner/action@v4`は更新しやすい一方、参照先が将来変更される可能性があります。厳格な供給網対策が必要な環境では、外部actionを完全なcommit SHAで固定する方法を検討します。

```yaml
uses: actions/checkout@<full-length-commit-sha>
```

SHA固定には、更新作業が増えるというトレードオフがあります。Dependabotなどを利用し、更新差分をレビューできる運用と組み合わせてください。

### Secretsをpull requestへ渡さない

外部forkからのpull requestで、信頼できないコードと本番Secretsを同じjobに置く設計は避けます。検証jobとデプロイjobを分離し、デプロイは信頼済みブランチや承認済みEnvironmentからだけ実行してください。

特に`pull_request_target`は権限の扱いを誤ると危険です。外部から変更されたコードをcheckoutして本番資格情報と一緒に実行しないよう、イベントごとの信頼境界を確認します。

### 「失敗時に人間が何をするか」まで決める

完全無人化は、誰も見ないことではありません。通常系は無人で流し、例外だけを人間へ送ります。

通知には、最低限次の情報を含めます。

- workflow runのURL
- 失敗したjobとstep
- 入力件数と処理済み件数
- 外部更新を実行したか
- 推定費用
- 安全に再実行できる条件
- ロールバックが必要か

「失敗しました」だけでは、担当者がログを最初から読み直す必要があります。復旧に必要な判断材料まで通知へ含めることで、平均復旧時間を短縮できます。

## 一次情報と視覚的証拠の残し方

自動化の品質を説明するとき、生成画像だけを実行証拠として扱ってはいけません。次の証拠を残します。

1. GitHub Actionsのrun summary
2. 実行対象のcommit SHA
3. 各stepの成功・失敗
4. テスト件数と終了コード
5. artifactの内容
6. 公開後URLの疎通結果
7. 外部更新の有無
8. API利用量または推定費用

記事へ実画面を掲載できる場合は、**GitHub Actionsのrun summary画面**を撮影し、起動時刻、commit SHA、`ruff check`、`pytest`、デプロイstep、所要時間が見える状態にします。Secrets、個人情報、非公開のリポジトリ名はマスキングしてください。

掲載できない場合は、証拠がないことを隠さず、次のように範囲を明記します。

> ローカルテストの成功は確認済み。ただし、GitHub-hosted runnerでの実行結果と本番デプロイ結果はこの記事では確認していない。

「確認済み」「推測」「未確認」を分けることが、一般論だけの記事との差になります。

## よくある失敗と対策

### ローカルでは動くのにCIで失敗する

**原因：** Python、Node.js、Hugo、依存パッケージのバージョン差です。

**対策：** workflowでバージョンを明示し、依存関係を固定します。確認した稼働用workflowでは、Python `3.12`、Node.js `22`、Hugo `0.163.3`を指定しています。

### cronの時刻を日本時間だと思い込む

**原因：** GitHub ActionsのcronはUTC基準です。

**対策：** YAMLの横にJST換算をコメントで残します。例えばUTCの`0 0 * * *`は、日本標準時では午前9時です。祝日や営業時間に依存する処理は、スクリプト内でも営業日判定を行います。

### 成功扱いだが成果物が空になる

**原因：** 例外を握りつぶし、終了コード0で終わっています。

**対策：** 取得件数0や必須ファイル欠損を明示的にエラーへ変換します。「処理できなかった」と「条件に合う対象がなかった」をログ上でも分けます。

### API利用料が増え続ける

**原因：** 再試行回数、対象件数、トークン量に上限がありません。

**対策：** 1回あたりの対象件数、再試行回数、推定コストの上限を設定します。上限値は料金表と自分の実測ログから決め、超過時は公開せず終了させます。

予算判定は、本処理の後ではなく有料APIを呼ぶ直前に置いてください。

### 自動公開後に内容の誤りが発覚する

**原因：** 生成成功を品質合格とみなしています。

**対策：** 禁止表現、引用元、リンク、日付、金額、重複をCIで検査します。法務、医療、投資判断、人事評価など、誤りの影響が大きい用途は完全無人公開に向きません。

### 再実行したら同じ投稿が増える

**原因：** workflowの成功・失敗だけを見て、外部サービス側で処理済みか確認していません。

**対策：** 実行キーを保存し、公開前に重複を確認します。通信タイムアウトが発生した場合も、「失敗したから未投稿」と決めつけず、外部側の状態を照合してください。

## GitHub Actionsが使えないケースと限界

ブラウザ操作を長時間続ける処理、固定IPが必須の処理、特殊な社内ネットワークへ接続する処理、大容量データを恒常的に保持する処理は、GitHub-hosted runnerと相性がよくありません。クラウドVMやself-hosted runnerの方が適する場合があります。

ただし、self-hosted runnerには、OS更新、ネットワーク制御、資格情報の保護、ジョブ間のデータ残存など、GitHub-hosted runnerとは異なる運用責任が生じます。「自由度が高いから安全」というわけではありません。

また、利用先サービスが自動アクセスを禁止している場合、技術的に実行できても運用してはいけません。ポイントサイト、ECサイト、SNS、広告サービスでは、API規約、自動操作規約、アカウント共有条件を確認してください。

GitHub Actionsは収益を直接生み出す装置ではありません。市場に需要がない商品、検索されない記事、成約しない導線を高速で量産しても成果にはつながりません。CIで守れるのは処理の再現性や安全性であり、需要判断や事業倫理までは自動判定できません。

## 成果を測るKPI

KPIは「何回動いたか」だけでなく、運用、品質、コスト、収益の4層で見ます。

| 層 | KPI | 改善判断 |
|---|---|---|
| 運用 | workflow成功率 | 失敗step別に原因を分類する |
| 運用 | 平均復旧時間 | 通知から正常化までを測る |
| 品質 | 出力検証合格率 | 欠損、重複、異常値を分ける |
| 品質 | 公開後の修正率 | 自動検査へ追加すべき条件を探す |
| コスト | 1回あたりのAPI費用 | 上限値と再試行条件を調整する |
| 収益 | 自動生成物経由のCV数 | 記事・商品・導線別に計測する |
| 効率 | 人間の介在時間 | 例外対応に費やした分数を記録する |
| 資産性 | 無人継続日数 | 手動操作なしで正常稼働した期間を見る |

目標値を他社の数字から借りるのではなく、最初の運用期間を基準値にします。例えば、最初の実行ログから成功率、修正回数、API費用を集計し、その後の変更が改善につながったか比較します。

収益額だけを見ると、偶然の成約と自動化の効果を区別できません。

**自動生成物が公開された → 検索やSNSから流入した → 商品ページへ移動した → 成約した**

この経路を段階に分けて計測してください。公開数だけ増えて流入や成約が増えない場合、問題はGitHub Actionsではなく、企画、検索意図、訴求、商品導線にある可能性があります。

## 初心者が今日作れる最小workflow

最初から自動公開まで実装する必要はありません。まず、手動でテストだけを実行する `.github/workflows/manual-check.yml` を作ります。

```yaml
name: Manual Safety Check

on:
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: manual-safety-check
  cancel-in-progress: false

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Static check
        run: ruff check .

      - name: Unit tests
        run: pytest
```

導入手順は次のとおりです。

1. このファイルをリポジトリへ追加する
2. GitHubの「Actions」画面から手動実行する
3. 失敗したstepをローカルで再現する
4. 3回以上安定してからdry-runを追加する
5. dry-runの成果物をartifactへ保存する
6. 外部公開は最後に追加する
7. 安定後にscheduleを設定する

この順序なら、事故範囲を限定したまま自動化を広げられます。

## 読了後すぐに取るアクション

今日できる作業は、現在の業務スクリプトについて次の5項目を1枚に書くことです。

- 入力データ
- 外部へ書き込む処理
- 失敗を判定する条件
- 1回あたりの費用上限
- dry-runで確認する出力

次に、次の3条件を決めてください。

- **成功条件：** 何が生成されれば成功か
- **停止条件：** どの異常値で公開を止めるか
- **復旧条件：** どの状態なら安全に再実行できるか

その後、前述の `.github/workflows/manual-check.yml` を作り、最初は`workflow_dispatch`による手動起動とテストだけを設定します。テストが安定してから、dry-run、定期実行、外部公開の順に広げてください。

## まとめ：時間を使わずに育つ自動化資産へ

GitHub Actionsによる業務自動化は、cronでスクリプトを起動した時点では完成していません。

- 業務ロジックをローカルでも再現できる入口へ集約する
- CIで異常な入力と出力を止める
- Secretsと権限を最小化する
- dry-runで外部更新を分離する
- `concurrency`、timeout、冪等性で暴走を防ぐ
- ログ、artifact、通知で復旧可能にする
- コスト、品質、収益、人間の介在時間をKPIで追う
- 確認済みの事実と未確認の範囲を分けて記録する

この積み重ねによって、担当者が毎日ボタンを押さなくても、集客、情報更新、商品導線を継続できる基盤が育ちます。人間の仕事を定型処理から、例外対応、需要判断、改善へ移せるようになります。

## 本気で自動化・ストック型収益を構築したい方へ

「GitHub Actionsの設定は分かった。でも、何を自動化すれば収益につながるのか」「API、AI、ブログ、商品導線をどう接続すればよいのか」と迷っているなら、個別の技術を学ぶだけでは時間がかかります。

必要なのは、**収益候補の選定、無人実行、失敗防止、計測、改善**を一本の流れにした実践手順です。

Hiroが実際の自動化環境で検証したマニュアルを、目的別にまとめています。手作業を増やす副業ではなく、稼働するほどログとコンテンツが蓄積される自動化資産を作りたい方は、次のページから自分に合う仕組みを選んでください。

**→ [本気で自動化・ストック型収益を構築したい方向けの実践マニュアルを見る](/products/)**
