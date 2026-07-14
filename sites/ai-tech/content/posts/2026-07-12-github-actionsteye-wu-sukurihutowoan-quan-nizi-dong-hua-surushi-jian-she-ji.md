---
title: "GitHub Actionsで業務スクリプトを安全に自動化する実践設計：CI・Secrets・ログ・KPIまで"
date: 2026-07-12T08:22:32+09:00
draft: false
tags:
  - "GitHub Actions"
  - "業務自動化"
  - "CI"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!GitHub Actions automation pipeline dashboardhttps://image.pollinations.ai/prompt/GitHub%20Actions%20automation%20pipeline%20dashboard%20secure%20busi"
---
![GitHub Actions automation pipeline dashboard](https://image.pollinations.ai/prompt/GitHub%20Actions%20automation%20pipeline%20dashboard%20secure%20business%20workflow?width=800&height=400&nologo=true)

毎朝のCSV集計、記事生成、価格調査、レポート送信、デプロイ確認。こうした業務スクリプトは、最初は便利でも、運用が雑だとすぐに「失敗していないか毎日見る仕事」に変わります。

GitHub Actionsを使えば、定時実行、手動実行、テスト、ビルド、デプロイを自動化できます。ただし、Secretsの扱い、失敗時の止め方、ログの残し方、二重実行の防止を決めないまま本番運用すると、手作業より危ない仕組みになります。

この記事では、**GitHub Actionsで業務スクリプトを安全に運用し、自動化資産として育てる方法**を、初心者でも実装順に追える形で整理します。単なるYAMLの書き方ではなく、ブログ生成、レポート作成、商品ページ更新、通知、Cloudflare Pagesデプロイのような「収益導線に近い業務」を安全に回す設計に絞ります。

なお、この記事は投資助言や収益保証ではありません。扱うのは、業務自動化、CI、Web運用、ログ設計の実践方法です。

## GitHub Actionsとは：業務スクリプトを安全に動かす実行基盤

GitHub Actionsは、GitHub上でコマンドを自動実行する仕組みです。たとえば、次のような処理をYAMLファイルで定義できます。

- `main` ブランチにpushされたらテストする
- 手動ボタンで記事生成を試す
- 毎朝9時にレポート生成を走らせる
- テストが通ったときだけCloudflare Pagesへデプロイする
- 失敗したらログを残し、通知する

初心者が最初に押さえるべき用語は次の通りです。

| 用語 | 意味 | 例 |
|---|---|---|
| workflow | 自動化の設計書 | `.github/workflows/daily-post.yml` |
| trigger | 起動条件 | `push`、`schedule`、`workflow_dispatch` |
| job | 実行単位 | テスト、ビルド、デプロイ |
| step | job内の1作業 | Pythonセットアップ、`pytest` 実行 |
| Secrets | APIキーやトークンを隠して保存する機能 | `CLOUDFLARE_API_TOKEN` |
| CI | 変更ごとにテストや静的解析を走らせる仕組み | `ruff check .`、`pytest` |

重要なのは、GitHub Actionsを「ただの定時実行ツール」と考えないことです。業務スクリプトを安全に資産化するには、次の4つをセットで設計します。

1. 実行条件
2. 品質チェック
3. 失敗時の停止条件
4. ログとKPI

「動く」だけでは不十分です。「壊れたときに、正しい場所で止まり、原因を追える」状態にして初めて業務運用に使えます。

## 実例：Hiroのauto-ai-blogで確認できる構成

この記事では、Hiroの `auto-ai-blog` リポジトリで確認できる構成を実例にします。2026年7月12日 JST時点で、主に次のファイルが確認できます。

- `.github/workflows/daily-post.yml`
- `docs/workflows/cloud-daily-post.yml`
- `docs/cloud-mode.md`
- `scripts/cloud_prepare_ai_cli.sh`
- `scripts/cloud_generate.sh`
- `generator/generate.py`
- `scripts/deploy_cloudflare_pages.py`

`.github/workflows/daily-post.yml` は、`main` へのpushと手動実行で動くCI兼デプロイworkflowです。処理の流れは次の通りです。

1. リポジトリをcheckoutする
2. Python 3.12をセットアップする
3. `requirements.txt` と `requirements-dev.txt` を入れる
4. `ruff check .` を実行する
5. `pytest` を実行する
6. Hugo Extendedをセットアップする
7. Node.js 22をセットアップする
8. `python scripts/deploy_cloudflare_pages.py` でCloudflare Pagesへデプロイする

一方、`docs/workflows/cloud-daily-post.yml` は、クラウド側で記事生成まで行うworkflowテンプレートです。毎日UTC 0:00、つまりJST 9:00相当で動く `schedule` が定義されています。ただし、このファイルは現時点では `.github/workflows/` ではなく `docs/workflows/` に置かれているテンプレートです。実際にGitHub Actionsとして動かすには、GitHub側でworkflow書き込み権限のある環境で `.github/workflows/cloud-daily-post.yml` に配置する必要があります。

この差分は重要です。記事で「毎朝9時に実行される」と書く場合、実運用中のworkflowなのか、配置待ちのテンプレートなのかを分けて書かないと事実誤認になります。

## この構成の特徴：AI APIを直接呼ばず、AI CLIをsubprocessで呼ぶ

HiroのCloud Mode設計では、PythonからAI APIを直接呼びません。`docs/cloud-mode.md` には、次の方針が明記されています。

- AI SDKを追加しない
- AI API endpointへ直接HTTPリクエストしない
- `claude -p`、`gemini -p`、`codex -q` のようなCLIを `subprocess` で呼ぶ
- 認証情報はGitHub Secretsやrunner secretsから渡す

この設計のメリットは、AI APIの認証情報をPythonコードに埋め込みにくくできることです。CLIの認証方式に寄せることで、ローカル実行とクラウド実行の入口も揃えやすくなります。

ただし、注意点もあります。リポジトリ内には、Notion連携系スクリプトに認証情報らしき文字列がコード内に残っている箇所が確認できます。これは改善対象です。GitHub Actionsで安全運用するなら、AI CLIだけでなく、Notion、Cloudflare、外部APIのトークンもすべてSecretsへ移す必要があります。

## ステップ1：自動化する業務を「収益導線」から逆算する

![Secure CI workflow diagram](https://image.pollinations.ai/prompt/secure%20CI%20workflow%20diagram%20with%20tests%20secrets%20logs%20deployment?width=800&height=400&nologo=true)

最初に決めるべきことは、「何を自動化するか」ではありません。「何が事業成果に近いか」です。

ブログ運用なら、次のような導線になります。

1. 検索流入を狙うテーマを選ぶ
2. AI CLIで下書きを生成する
3. 品質チェックを通す
4. Hugoでサイトをビルドする
5. Cloudflare Pagesへ公開する
6. Search Consoleやアクセス解析で成果を見る
7. 成果の良いテーマを次回生成に反映する

GitHub Actionsが担当すべきなのは、このうち「毎回同じ確認が必要な作業」です。人間は、テーマ選定、商品設計、法務確認、読者価値の判断、改善方針の決定に集中します。

自動化対象を選ぶときは、次の3つで優先順位を付けます。

| 優先度 | 自動化対象 | 理由 |
|---|---|---|
| 高 | テスト、ビルド、リンク確認、デプロイ前チェック | 失敗すると公開品質に直結する |
| 中 | 記事生成、レポート作成、商品ページ更新 | 成果に近いが品質チェックが必要 |
| 低 | 判断が必要な作業、規約確認、法務確認 | 完全自動化より承認フロー向き |

収益導線に近いほど、いきなり全自動にしないことが重要です。最初は「生成するが公開しない」「dry-runでログだけ残す」「手動承認後にdeployする」など、段階を分けます。

## ステップ2：ローカルで成功する最小コマンドを決める

GitHub Actionsに載せる前に、ローカルで成功条件を固定します。Hiroのリポジトリでは、記事生成の入口として次のようなコマンドが使われます。

```bash
python generator/generate.py
python generator/generate.py --cloud
python generator/generate.py --cloud --dry-run
```

このように入口を明確にしておくと、GitHub Actionsで失敗したときに原因を切り分けやすくなります。

逆に、次の状態は避けるべきです。

- ローカルでは `script_a.py`、GitHub Actionsでは `script_b.py` を使う
- 手元では環境変数なし、クラウドでは大量の環境変数が必要
- 成功条件が「なんとなくファイルが増えている」だけ
- エラー時にどこまで進んだか分からない

おすすめは、共通の入口を1つ決め、環境差だけを環境変数で切り替える方法です。

```bash
BLOG_EXECUTION_MODE=cloud python generator/generate.py --cloud
```

最低限、次の成功条件を決めてからActions化します。

- コマンドが終了コード0で終わる
- 生成ファイル数が想定通り
- 出力先ディレクトリが固定されている
- dry-runでは本番書き込みをしない
- ログに実行日時と結果が残る

## ステップ3：生成より先にCIを置く

業務自動化で最も危ないのは、生成物を確認せずに公開することです。記事生成、商品ページ生成、価格更新、通知送信は、必ず検証の後に置きます。

Hiroの `.github/workflows/daily-post.yml` では、デプロイ前に次の品質ゲートがあります。

```yaml
- name: Python static check
  run: ruff check .

- name: Python tests
  run: pytest
```

2026年7月12日 JSTにこの作業環境で確認した結果は次の通りです。

```text
pytest: 30 passed in 34.75s
ruff check .: 16 errors
```

ここから分かる重要な点は、**テストが通ることと、CI全体が安全であることは別**ということです。`pytest` は通っていますが、`ruff` は失敗しています。つまり、現在の品質ゲート上は「デプロイ前に止まるべき状態」です。

`ruff` の指摘には、次のようなものが含まれていました。

- `generator/cli_runner.py` の不要なmode指定
- `generator/cli_runner.py` の `try/except/pass` を `contextlib.suppress` に置き換え可能
- `scripts/generate_affiliate_lp.py` のimport順
- `scripts/publish_research.py` の未使用import
- `scripts/save_to_notion.py` の未使用変数
- `scripts/setup_notion_db.py` の未使用import

これは悪いことではありません。むしろ、CIが公開前に問題を検知しているという意味では健全です。問題は、失敗を無視してデプロイすることです。

## ステップ4：GitHub Actionsの権限を最小化する

GitHub Actionsでは、`permissions` を明示します。デフォルト権限に任せるのではなく、workflowごとに必要な権限だけを渡します。

Hiroの `.github/workflows/daily-post.yml` では、次のように設定されています。

```yaml
permissions:
  contents: read
  deployments: write
```

これは、リポジトリ内容を読み、デプロイ状態を書き込む用途に合っています。記事生成してcommit & pushするworkflowでは、別途 `contents: write` が必要です。

`docs/workflows/cloud-daily-post.yml` では、次の設定があります。

```yaml
permissions:
  contents: write
  actions: read
```

判断基準はシンプルです。

| やりたいこと | 必要な権限 |
|---|---|
| コードを読むだけ | `contents: read` |
| リポジトリへcommitする | `contents: write` |
| デプロイ状態を作る | `deployments: write` |
| Actionsの情報を見る | `actions: read` |

最初から広い権限を渡すと、スクリプトのバグや外部依存の問題が起きたときに被害範囲が広がります。必要になった権限だけ足すのが基本です。

## ステップ5：Secretsをコードに書かない

APIキー、Deploy Hook URL、AI CLI認証情報、外部サービスのトークンは、GitHub Secretsに置きます。HiroのCloud Modeテンプレートでは、次のSecretsが想定されています。

- `CLOUD_AI_CLI_INSTALL_COMMANDS`
- `CLOUDFLARE_PAGES_DEPLOY_HOOK_URL`
- `CLAUDE_CONFIG`
- `GEMINI_API_KEY`
- `CODEX_AUTH_JSON`

ただし、Secret名を定義するだけでは安全運用になりません。次のルールまでセットで決めます。

- Secretの値をログに出さない
- PRからの実行にSecretを渡さない
- 外部コマンドへ渡す環境変数を最小限にする
- Secretの有無はログに残しても、値は残さない
- 不要になったSecretは削除する
- コード内に残ったトークンは即時ローテーションする

特に注意したいのは、「一度コミットした認証情報は、削除しても漏えい済みとして扱う」ことです。Git履歴に残るため、値を消すだけでは足りません。対象サービス側でトークンを無効化し、新しいSecretに差し替えます。

## ステップ6：dry-runを本番前の安全弁にする

`dry-run` は、実際には投稿、購入、送信、デプロイをせず、直前までの処理を確認するモードです。

Hiroの `docs/workflows/cloud-daily-post.yml` には、手動実行時の `dry_run` 入力があります。`true` の場合は次を実行します。

```bash
python generator/generate.py --cloud --dry-run
```

初心者が業務自動化で失敗しやすいのは、いきなり本番に書き込むことです。dry-runを作ると、次の確認ができます。

- CLI認証が通るか
- 入力データを読めるか
- 生成予定のファイル名が正しいか
- 投稿先やデプロイ先が想定通りか
- Secretsが足りているか
- 本番書き込みなしでログが残るか

広告投稿、アフィリエイトリンク生成、価格更新、請求処理、メール送信では、dry-runは必須です。「開発用のおまけ」ではなく、本番前の安全弁として扱います。

## ステップ7：concurrencyで二重実行を防ぐ

同じworkflowが同時に走ると、二重投稿、二重請求、古いデータによる上書きが起きます。GitHub Actionsでは `concurrency` を使って同時実行を制御できます。

HiroのCloud Modeテンプレートには、次の設定があります。

```yaml
concurrency:
  group: cloud-daily-ai-post
  cancel-in-progress: false
```

この設定では、同じgroupのworkflowが重なりにくくなります。`cancel-in-progress: false` にしているため、進行中の処理を途中でキャンセルしません。

記事生成やデプロイのように、途中停止で中途半端な状態が残る処理では、この判断が合います。一方、テストだけのworkflowなら、古い実行をキャンセルして新しい実行を優先する設計もあります。

使い分けは次の通りです。

| 処理 | 推奨 |
|---|---|
| 記事生成、デプロイ、外部投稿 | `cancel-in-progress: false` |
| PRのテスト、lint | `cancel-in-progress: true` も検討 |
| 請求、購入、在庫更新 | concurrencyに加えて状態ファイルやDBロックも必要 |

## ステップ8：失敗時に「止まる場所」を決める

業務自動化では、最後まで無理に進むより、正しい場所で止まる方が価値があります。

記事生成workflowなら、停止条件を次のように分けます。

| 状態 | 止め方 |
|---|---|
| AI CLIが見つからない | 生成をスキップし、ログに残す |
| 記事は生成できたが品質チェックで落ちた | 保存または公開しない |
| `ruff` が落ちた | デプロイしない |
| `pytest` が落ちた | デプロイしない |
| Hugo buildが落ちた | 公開しない |
| Deploy Hook URLが未設定 | push検知に任せる |
| git pushが失敗 | リトライ後にログへ残す |

Hiroの `docs/cloud-mode.md` では、次の安全設計が説明されています。

- CLIが1つも使えない場合は記事生成をスキップする
- commit & pushは記事生成に成功した場合だけ実行する
- pushは最大3回リトライする
- `generator/.state.json` に実行modeを記録する

これは、失敗しても人間の時間を奪い続けないための設計です。自動化で一番避けるべきなのは、失敗したまま進み、壊れた成果物を公開することです。

## ステップ9：ログを「改善資産」として残す

自動化のログは、障害記録だけではありません。改善のための一次情報です。

最低限、次の項目を残します。

- 実行日時
- workflow名
- commit SHA
- 起動条件
- 入力パラメータ
- 成功・失敗
- 失敗step
- 生成ファイル数
- 公開URL
- Secret名の有無。ただし値は残さない
- 次に人間が見るべきファイル
- 復旧に必要なコマンド

ログがない自動化は、失敗した瞬間に手作業より面倒になります。逆にログが整っていると、次回の改善が速くなります。

たとえば今回の実測なら、次のように記録できます。

```text
date_jst: 2026-07-12
repo: auto-ai-blog
pytest: 30 passed in 34.75s
ruff: failed, 16 errors
quality_gate: not ready for deploy
next_action: fix lint issues before relying on deployment workflow
```

このようなログが積み上がると、「どのworkflowがよく落ちるか」「どの種類のエラーが多いか」「公開前品質ゲートが機能しているか」を判断できます。

## 画像で説明すべき箇所：業務スクリプトが収益導線に変わる流れ

![Automation asset revenue pipeline](https://image.pollinations.ai/prompt/automation%20asset%20revenue%20pipeline%20from%20GitHub%20Actions%20to%20content%20publishing%20analytics%20and%20sales?width=800&height=400&nologo=true)

この記事に図解を入れるなら、**「業務スクリプトが収益導線に変わる流れ」**を見せるのが効果的です。

図には次を入れます。

- 左：起動条件。`push`、`schedule`、`workflow_dispatch`
- 中央：lint、test、dry-run、記事生成、Hugo build
- 右：Cloudflare Pages公開、広告、アフィリエイト、商品ページ、問い合わせ
- 下：ログ、KPI、Search Console、改善テーマのフィードバック

実際の記事では、次のスクリーンショットを並べると、一般論ではなくなります。

- GitHub Actionsの実行画面
- `pytest 30 passed` のログ
- `ruff 16 errors` のログ
- Cloudflare Pagesのデプロイ履歴
- 生成されたMarkdown記事
- Search Consoleやアクセス解析の改善前後

特に、成功ログだけでなく失敗ログを見せるのが重要です。安全運用の記事では、「どこで止まったか」が読者にとって価値になります。

## よくある失敗と対策

### 失敗1：ローカルPCのログイン状態を前提にする

ローカルPCではCLIにログイン済みでも、GitHub Actionsのrunnerは毎回ほぼ空の環境です。AI CLI、Cloudflare、Notion、外部APIの認証は明示的に渡す必要があります。

**対策**：`scripts/cloud_prepare_ai_cli.sh` のような準備スクリプトを作り、Python、Node、AI CLIの有無を最初に出力します。ただし、Secretの値は絶対に出力しません。

### 失敗2：CIを通さずに公開する

記事生成や商品ページ生成を先に公開すると、壊れたHTML、誤リンク、低品質コンテンツが本番に出ます。

**対策**：公開前に `ruff`、`pytest`、Hugo build、リンク確認を置きます。今回の実測でも、テストは成功しましたが静的解析は失敗しました。複数の品質ゲートを置く理由はここにあります。

### 失敗3：二重実行で同じ投稿が増える

`schedule` と手動実行が重なると、同じ記事や通知が二重に作られる場合があります。

**対策**：`concurrency` を設定します。さらに、生成済みファイル名、日付、トピックIDを状態ファイルで管理します。

### 失敗4：エラー通知がなく、数日後に気づく

自動化は沈黙すると危険です。止まっているのに気づかない状態が、最も損失を広げます。

**対策**：失敗step、ログURL、次に見るファイル、再実行コマンドを通知します。Slack、Discord、メール、GitHub Issueのどれかに集約すると運用しやすくなります。

### 失敗5：Secretsをコードに残したままActions化する

GitHub Actionsに移すとき、既存スクリプト内のトークンを見落とすことがあります。コード内にトークンが残っていると、Secrets管理をしているつもりでも安全ではありません。

**対策**：`rg "API_KEY|TOKEN|SECRET|PASSWORD|ntn_|sk-"` のような検索で、認証情報らしき文字列を棚卸しします。見つかった値は削除するだけでなく、サービス側で無効化して再発行します。

### 失敗6：収益化導線を後回しにする

記事生成だけ自動化しても、CTA、内部リンク、商品ページ、計測、改善サイクルがなければ資産化しにくいです。

**対策**：記事末尾のCTA、関連ページ、商品一覧、クリック計測を最初の設計に入れます。GitHub Actionsは投稿数を増やす道具ではなく、収益導線を毎日整える実行基盤として使います。

## 成果を測るKPI

業務自動化を資産として育てるには、作業時間の削減だけを見てはいけません。安全性、品質、成果への貢献を分けて測ります。

| KPI | 見る理由 |
|---|---|
| 自動実行成功率 | workflowが安定しているか分かる |
| 品質ゲート通過率 | lint、test、buildを通った割合を見る |
| 人間の介入回数 | 運用負荷が下がっているか分かる |
| 復旧時間 | 失敗検知から修正までの速さを見る |
| 生成物の採用率 | AI生成物が実運用に耐えているか分かる |
| 公開後クリック率 | CTAや内部リンクが機能しているか分かる |
| 収益イベント数 | 広告クリック、購入、問い合わせなどを測る |
| CI失敗の内訳 | test、lint、build、auth、deployのどこで落ちるか分かる |

Hiroの実測例では、2026年7月12日 JST時点で `pytest` は30件成功、`ruff` は16件指摘でした。この場合、「テスト成功率」だけを見ると良く見えます。しかし、「公開前品質ゲート」は未達です。

つまり、次にやるべきことは新機能追加ではなく、まずlint指摘の整理です。KPIは、気分ではなく優先順位を決めるために使います。

## 反論：GitHub Actionsだけで全部やるべきではない

ここまでGitHub Actionsの有効性を説明しましたが、何でもActionsに載せればよいわけではありません。

次のケースでは、別手段や承認フローを検討します。

- ブラウザログイン状態が頻繁に切れる業務
- 長時間常駐が必要な処理
- GPUが必要な動画生成
- 規約上、自動アクセスが禁止されているサイト操作
- 金融、法務、医療など、失敗時に即時の人間判断が必要な処理
- 1回の実行時間が長く、runner制限にかかりやすい処理
- 外部サービスのレート制限に強く依存する処理

この場合は、GitHub Actionsだけで完結させず、self-hosted runner、クラウドVM、Queue、承認フロー、監視ツールを組み合わせます。

完全自動化を目指す場合でも、最初から全工程を無人化する必要はありません。危険な箇所だけ承認制にした方が、長く安全に運用できます。

## 初心者向けチェックリスト：最初の1本をActions化する手順

最初の業務スクリプトをGitHub Actionsに載せるなら、次の順番で進めます。

1. ローカルで成功するコマンドを1つ決める
2. `--dry-run` を追加する
3. 出力ファイルとログの保存先を固定する
4. `pytest` または最小の動作確認を用意する
5. `.github/workflows/` に手動実行workflowを作る
6. SecretsをGitHubに登録する
7. Secret値がログに出ないことを確認する
8. `workflow_dispatch` で手動実行する
9. 成功ログと失敗ログを確認する
10. 問題なければ `schedule` を追加する
11. `concurrency` を設定する
12. 通知先を決める
13. KPIを週1回見る

初心者は、いきなり `schedule` から始めない方が安全です。まず手動実行、次にdry-run、最後に定時実行の順に広げます。

## この記事の差別化ポイント

多くのGitHub Actions解説は、YAMLの基本やCIの説明で終わります。この記事では、そこから一歩進めて、業務スクリプトを「人間の時間を消耗しない自動化資産」に変える視点で整理しました。

特に、Hiroの `auto-ai-blog` リポジトリで確認できる次の一次情報を反映しています。

- `.github/workflows/daily-post.yml` のpush・手動実行workflow
- Python 3.12、Node.js 22、Hugo、Cloudflare Pages連携
- `docs/workflows/cloud-daily-post.yml` のJST 9:00相当のscheduleテンプレート
- `scripts/cloud_prepare_ai_cli.sh` によるAI CLI確認
- `scripts/cloud_generate.sh` によるCloud Mode実行
- `docs/cloud-mode.md` の「AI APIを直接呼ばずCLIをsubprocessで呼ぶ」設計
- 2026年7月12日 JST時点の `pytest 30 passed in 34.75s`
- 同時点の `ruff check .` 16件指摘
- コード内に残る認証情報らしき文字列はSecrets移行が必要、という改善ポイント

成功例だけでなく、現在の未解決課題も含めている点が重要です。実運用では「全部きれいに通っている話」より、「どこで止まり、次に何を直すか」が役に立ちます。

## 読了後すぐに取れるアクション

今日やることは3つで十分です。

1. 業務スクリプトに `--dry-run` を追加する
2. 実行日時、成功失敗、出力ファイルをログに残す
3. GitHub Actionsで `pytest` または最小の確認コマンドを走らせる

すでにGitHub Actionsを使っているなら、次の確認をしてください。

```bash
ruff check .
pytest
```

さらに、認証情報らしき文字列がコード内にないか確認します。

```bash
rg "TOKEN|SECRET|API_KEY|PASSWORD|ntn_|sk-"
```

見つかった場合は、値をGitHub Secretsへ移すだけでなく、サービス側で該当トークンを無効化して再発行します。

## まとめ：GitHub Actionsは「放置」ではなく「検証可能な自動化」の土台

GitHub Actionsは、単なるCIツールではありません。業務スクリプトを、定時実行、品質チェック、ログ、デプロイ、改善KPIまで含めた自動化資産に変える土台です。

ただし、安全な運用には順番があります。

1. ローカルで成功条件を固める
2. dry-runを作る
3. CIを置く
4. Secretsを分離する
5. 権限を最小化する
6. concurrencyで二重実行を防ぐ
7. 失敗時に正しい場所で止める
8. ログとKPIで改善する

その先に、記事、商品ページ、広告導線、アフィリエイト導線、問い合わせ導線が、人間の手を離れて安定的に回る状態があります。

自分の時間を削らず、毎日積み上がる仕組みを作りたいなら、最初の一歩は小さくて構いません。まず1本の業務スクリプトにdry-runとGitHub Actionsの検証workflowを付けてください。そこから、自動化は「便利な小道具」ではなく、継続的に改善できる資産へ変わっていきます。

---

## 本気で自動化・不労所得を構築したい方向けの実践マニュアル

GitHub Actions、業務自動化、CIの考え方を理解しても、実際に収益導線まで作り切るには、テーマ選定、記事生成、商品設計、導線配置、検証ログ、改善KPIまでを一気通貫で組む必要があります。

そこで、実装手順、テンプレート、運用チェックリストをまとめた **「本気で自動化・不労所得を構築したい方向けの実践マニュアル」** を用意しています。

毎日手を動かして消耗する側から、仕組みが働き続ける側へ移りたい方は、こちらから次の一手を選んでください。

[実践マニュアルを見る](/products/)
