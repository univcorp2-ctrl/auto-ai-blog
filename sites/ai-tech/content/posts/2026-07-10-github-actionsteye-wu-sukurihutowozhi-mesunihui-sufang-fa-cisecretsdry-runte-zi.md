---
title: "GitHub Actionsで業務スクリプトを止めずに回す方法：CI・Secrets・dry-runで「自動化資産」を作る実践手順"
date: 2026-07-10T09:22:01+09:00
draft: false
tags:
  - "GitHub Actions"
  - "業務自動化"
  - "CI"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!GitHub Actions automation dashboard for business scripts CI pipeline secure workflowhttps://image.pollinations.ai/prompt/GitHub%20Actions%20automatio"
---
![GitHub Actions automation dashboard for business scripts CI pipeline secure workflow](https://image.pollinations.ai/prompt/GitHub%20Actions%20automation%20dashboard%20for%20business%20scripts%20CI%20pipeline%20secure%20workflow?width=800&height=400&nologo=true)

「毎朝スクリプトを実行するのを忘れた」「エラーに気づかず投稿や集計が止まっていた」「担当者のPCが止まると業務も止まる」。

ブログ投稿、レポート生成、在庫チェック、広告データ集計、商品リンク管理などを人間のクリックに頼っていると、自動化しているつもりでも、実態は属人化したままです。

この記事では、**GitHub Actionsで業務スクリプトを安全に運用する手順**を、初心者向けにステップ化して解説します。

単に「Pythonを定期実行する方法」ではありません。CI、Secrets、dry-run、ログ、artifact、KPIを組み合わせて、壊れにくく改善しやすい**自動化資産**に変える考え方です。

この記事で扱うキーワードは次の通りです。

- GitHub Actions
- CI
- 業務自動化
- Python定期実行
- Secrets管理
- dry-run
- artifact
- Hugoビルド
- Cloudflare Pages
- 自動化資産

## この記事の結論

GitHub Actionsは「スクリプトを定期実行する道具」だけではありません。

安全に使うには、次の順番で設計します。

1. 業務を「入力・処理・出力」に分ける
2. ローカルで同じコマンドを成功させる
3. dry-runで本番反映なしの検証を用意する
4. Secretsで認証情報を管理する
5. permissionsを最小化する
6. concurrencyで二重実行を防ぐ
7. テスト、生成、ビルド、デプロイを段階化する
8. ログとartifactを残す
9. 技術KPIと事業KPIを分けて見る

重要なのは「自動で動くこと」ではなく、**失敗した時に止まれること、成功した時に証拠が残ること、改善すべき数字が見えること**です。

## GitHub ActionsとCIの役割

GitHub Actionsは、GitHubリポジトリ内の `.github/workflows/*.yml` に書いた手順を、GitHubのrunner上で実行する仕組みです。

初心者向けに整理すると、役割は次のように分けられます。

| 要素 | 役割 |
|---|---|
| GitHub Actions | 決めた時刻、push、手動ボタンなどをきっかけに処理を実行する |
| CI | テストやビルドを実行し、壊れていないか検査する |
| 業務スクリプト | 記事生成、集計、投稿、通知、データ取得など実際の処理を行う |
| Secrets | APIキー、Webhook URL、認証情報などを安全に渡す |
| Artifacts | ログ、ビルド済みファイル、検証結果などを保存する |

GitHub Actionsが「実行係」だとすれば、CIは「検査係」です。

業務スクリプトを安全に運用するには、この2つを分けて考える必要があります。いきなり本番投稿や本番デプロイを行うのではなく、先にテストとビルドで壊れていないことを確認します。

## 実例：Hiroのauto-ai-blogで確認した設計

この記事は一般論だけではありません。Hiroの `auto-ai-blog` リポジトリで、実際のworkflow定義とテスト結果を確認しています。

確認した環境は次の通りです。

```text
リポジトリ: G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog
確認日: 2026年7月10日
確認対象:
- docs/workflows/cloud-daily-post.yml
- docs/daily-post.yml
- tests/test_cloud_mode.py
- tests/test_deploy_config.py
- tests/test_slop_guard.py
- tests/test_validate_ai_slop.py
```

`docs/workflows/cloud-daily-post.yml` では、Cloud Mode用のworkflowが次のように設計されています。

- workflow名：`Cloud Daily AI Post`
- `schedule`：`cron: '0 0 * * *'`
- 実行時刻：UTC 0:00、日本時間では毎日9:00相当
- 手動実行：`workflow_dispatch`
- dry-run入力：`dry_run`
- runner：`ubuntu-latest`
- timeout：`45`分
- Python：`3.12`
- Node.js：`22`
- `BLOG_EXECUTION_MODE=cloud`
- `BLOG_GIT_BRANCH=main`
- `permissions.contents=write`
- `permissions.actions=read`
- `concurrency.group=cloud-daily-ai-post`
- `cancel-in-progress=false`
- Hugoで3サイトをビルド
  - `sites/ai-tech`
  - `sites/business`
  - `sites/real-estate`
- artifact名：`hugo-public-cloud`
- Cloudflare Pages Deploy Hookが設定されている場合のみPOST実行

この設計で良い点は、記事生成、ビルド、artifact保存、デプロイ通知が1本の流れになっている一方で、`dry_run` によって本番反映なしの確認もできることです。

一方、`docs/daily-post.yml` はビルド検証寄りのworkflowです。

- workflow名：`Daily Hugo Build Check`
- `permissions.contents=read`
- `ruff check .`
- `pytest`
- Hugo 3サイトのビルド
- artifact名：`hugo-public`

つまり、書き込みが必要なCloud Modeでは `contents: write`、検証だけのworkflowでは `contents: read` と、権限を分けています。これは業務自動化では重要です。

## 実測ログ：2026年7月10日のテスト結果

2026年7月10日、Hiroの `auto-ai-blog` リポジトリで次のコマンドを実行しました。

```bash
python -m pytest tests/test_cloud_mode.py tests/test_deploy_config.py tests/test_slop_guard.py tests/test_validate_ai_slop.py -q
```

結果は次の通りです。

```text
.........                                                                [100%]
```

確認できたテスト数は9件です。

対象には、次の検証が含まれています。

- Cloud Modeが引数で有効になるか
- Cloud Modeが環境変数で有効になるか
- push先ブランチが環境変数を優先するか
- configのブランチ設定にフォールバックするか
- Cloudflare Pages用の3サイト設定が存在するか
- Windows環境で `npx.cmd` を解決できるか
- AIスロップ防止の品質チェックが通るか
- 一般論だけの薄いMarkdownを弾けるか
- `_index.md` を投稿対象から除外できるか

この結果から言えるのは、少なくともCloud Mode、デプロイ設定、AIスロップ防止、投稿対象抽出について、ローカルで検査できる状態になっているということです。

業務自動化では、「動く」だけでは足りません。壊れた時に検知できるテストがあることが、継続運用の前提になります。

![Automated CI workflow from schedule to tests to deployment with logs and secrets](https://image.pollinations.ai/prompt/Automated%20CI%20workflow%20from%20schedule%20to%20tests%20to%20deployment%20with%20logs%20and%20secrets?width=800&height=400&nologo=true)

## ステップ1：自動化する業務を「入力・処理・出力」に分ける

最初に、対象業務を4行で書き出します。

```text
入力：
処理：
出力：
失敗時：
```

例として、自動ブログ運用なら次のようになります。

```text
入力：topics.yaml、商品情報、過去記事、キーワード候補
処理：Pythonで記事を生成し、品質チェックを通す
出力：Markdown記事、Hugoのpublicディレクトリ、検証ログ
失敗時：エラー内容、対象topic、生成途中ファイル、スキップ理由をログに残す
```

この4行が書けない処理は、まだ自動化には早いです。

特に収益導線を含む業務では、「出力」が曖昧だと改善できません。記事を作るだけでなく、商品リンク、CTA、比較表、メール登録、販売ページへの導線など、どこが成果につながるのかを明確にします。

## ステップ2：ローカルで同じコマンドを成功させる

GitHub Actionsに載せる前に、ローカルで同じ処理を実行します。

例です。

```bash
python generator/generate.py --cloud --dry-run
python -m pytest
hugo --source sites/business --gc --minify
```

ここで確認するのは、次の4点です。

- 必要な依存関係がインストールできるか
- コマンドが手元で成功するか
- エラー時に原因が読めるログが出るか
- 生成物が想定した場所に出るか

手元で失敗する処理は、GitHub Actions上でも高確率で失敗します。runner特有の問題は後から出ますが、まずはスクリプト単体の不具合を潰します。

## ステップ3：dry-runを必ず用意する

`dry-run` は、本番反映をせずに処理だけ確認するモードです。

記事生成なら、Markdownの生成や品質チェックまでは行い、commit、push、デプロイは行わない状態です。

HiroのCloud Mode workflowでは、`workflow_dispatch` に `dry_run` 入力があります。`dry_run == 'true'` の場合は、次のコマンドが実行される設計です。

```bash
python generator/generate.py --cloud --dry-run
```

dry-runがあると、次のような場面で安全に検証できます。

- 新しい記事テンプレートを試す
- 商品リンクの挿入ロジックを変える
- AI生成のプロンプトを変える
- Hugoテーマや設定を変更する
- デプロイ前に品質チェックだけ通す

本番反映の前にdry-runを通すだけで、事故の多くは防げます。

## ステップ4：Secretsをコードに書かない

APIキー、Webhook URL、ログイン情報、認証JSONはコードに直接書きません。

GitHub Actionsでは、Repository SecretsやEnvironment Secretsに登録して、workflowから環境変数として渡します。

HiroのCloud Mode workflowでは、次のSecrets枠が使われています。

| Secret名 | 用途 |
|---|---|
| `CLOUD_AI_CLI_INSTALL_COMMANDS` | runnerにAI CLIを入れるコマンド |
| `CLOUDFLARE_PAGES_DEPLOY_HOOK_URL` | Cloudflare PagesのDeploy Hook |
| `CLAUDE_CONFIG` | Claude CLI用の設定 |
| `GEMINI_API_KEY` | Gemini CLI用のAPIキー |
| `CODEX_AUTH_JSON` | Codex CLI用の認証情報 |

注意点は、Secretの値をログに出さないことです。

次のようなログは避けます。

```bash
echo "$GEMINI_API_KEY"
```

代わりに、存在確認だけを出します。

```bash
if [ -z "$GEMINI_API_KEY" ]; then
  echo "GEMINI_API_KEY is not configured"
  exit 1
fi
```

これなら、Secret値を漏らさずに設定漏れを検知できます。

## ステップ5：permissionsを最小化する

GitHub Actionsの `permissions` は、workflowごとに必要最小限にします。

検証だけなら、通常は次で足ります。

```yaml
permissions:
  contents: read
```

一方、生成した記事をcommitしたりpushしたりするworkflowでは、次のように書き込み権限が必要です。

```yaml
permissions:
  contents: write
```

Hiroの設計でも、ビルド検証用の `docs/daily-post.yml` は `contents: read`、Cloud Mode用の `docs/workflows/cloud-daily-post.yml` は `contents: write` と分けられています。

業務自動化では、便利だからといって権限を広げすぎると危険です。広告、商品リンク、顧客情報、外部API、デプロイ先を扱う場合、権限の広げすぎは金銭的損失や情報漏えいにつながる可能性があります。

## ステップ6：concurrencyで二重実行を防ぐ

定期実行と手動実行が重なると、同じ記事を二重生成したり、同じ投稿を二重送信したりする可能性があります。

GitHub Actionsでは、`concurrency` で同じグループのworkflowを制御できます。

```yaml
concurrency:
  group: cloud-daily-ai-post
  cancel-in-progress: false
```

`cancel-in-progress: false` は、すでに動いている処理を途中でキャンセルしない設定です。

記事生成、ファイル更新、外部投稿、決済関連の処理では、途中キャンセルによって中途半端な成果物が残る場合があります。そのため、処理内容に応じて `true` と `false` を選びます。

目安は次の通りです。

| 処理内容 | 推奨 |
|---|---|
| テストだけ | `cancel-in-progress: true` でもよい |
| 記事生成とcommit | `false` を検討 |
| 外部サービス投稿 | `false` を検討 |
| デプロイだけ | 状況により判断 |
| 長時間の集計 | 二重実行防止を優先 |

## ステップ7：テスト、生成、ビルド、デプロイを分ける

業務スクリプトを1つの巨大なコマンドにすると、失敗した時に原因が分かりにくくなります。

おすすめの順番は次です。

1. checkoutする
2. PythonやNode.jsをセットアップする
3. 依存関係をインストールする
4. 静的チェックを実行する
5. テストを実行する
6. 業務スクリプトを実行する
7. サイトや成果物をビルドする
8. artifactを保存する
9. 必要な場合だけdeployやpushを行う

Hiroの `docs/daily-post.yml` では、`ruff check .`、`pytest`、Hugoビルド、artifact uploadの順に構成されています。

この順番にする理由は単純です。壊れたコードで記事生成やデプロイを進めないためです。

## ステップ8：ログとartifactを残す

自動化で重要なのは、「実行したかどうか」ではなく「何が起きたかを後から追えるか」です。

最低限、ログには次を残します。

- 実行日時
- workflow名
- 実行モード
- 入力件数
- 成功件数
- 失敗件数
- スキップ件数
- スキップ理由
- 生成ファイル
- ビルド対象
- 外部APIの応答概要
- 次回確認すべき項目

記事生成なら、次のようなログがあると改善しやすくなります。

```text
date: 2026-07-10
mode: cloud
topic: github-actions-business-script
generated: sites/business/content/posts/github-actions-business-script.md
quality_check: passed
hugo_build: passed
deploy_hook: skipped or success
next_check: Search Console indexing and CTA clicks
```

artifactには、ログ、生成ファイル、ビルド成果物、検証レポートを保存します。

収益化や集客を狙うなら、ログは改善材料です。どの記事が生成され、どの商品リンクが入り、どのビルドが成功したかを追えなければ、アクセスや成果との対応を分析できません。

![Terminal showing pytest 100 percent pass and GitHub Actions workflow success for automation asset](https://image.pollinations.ai/prompt/Terminal%20showing%20pytest%20100%20percent%20pass%20and%20GitHub%20Actions%20workflow%20success%20for%20automation%20asset?width=800&height=400&nologo=true)

## よくある失敗と対策

### 失敗1：ローカルでは動くのにGitHub Actionsで落ちる

原因は、OS、Pythonバージョン、Node.jsバージョン、環境変数、認証状態の差です。

対策です。

- `actions/setup-python` でPythonバージョンを固定する
- `actions/setup-node` でNode.jsバージョンを固定する
- `python --version` と `node --version` をログに出す
- 必要な環境変数をworkflowに明示する
- Secretが空の場合は早めに失敗させる

### 失敗2：cronの時刻をJSTだと思い込む

GitHub ActionsのcronはUTC基準です。

```yaml
- cron: '0 0 * * *'
```

これはUTC 0:00です。日本時間では9:00に相当します。

日本向けの記事投稿、レポート配信、広告データ取得などでは、「JSTで何時に動くか」をコメントやドキュメントに書いておくと運用ミスを減らせます。

### 失敗3：APIキーをコードやログに出す

APIキーをGitにcommitすると、削除しても履歴に残ります。

対策です。

- GitHub Secretsを使う
- `.env` は `.gitignore` に入れる
- Secret値を `echo` しない
- 漏えいの可能性があればキーを再発行する
- 外部API側で使用制限やIP制限を設定する

### 失敗4：毎日同じ記事や投稿を作る

自動生成で重複が起きると、SEO評価や読者体験に悪影響が出る可能性があります。

対策です。

- 処理済みIDを状態ファイルに保存する
- 生成前に既存slugを確認する
- 同じキーワードの記事がある場合はスキップする
- 重複時はログに理由を残す
- Search Consoleでインデックス状況を確認する

### 失敗5：エラー通知がない

自動化は、静かに失敗することがあります。

対策です。

- GitHub Actionsの通知を有効にする
- 失敗時にSlack、Discord、メールへ通知する
- 連続失敗回数を記録する
- 3回連続失敗したら人間レビューに切り替える

### 失敗6：人間確認が必要な処理まで無人化する

金融、医療、法務、個人情報、大量DM、規約違反の可能性がある投稿は、完全自動化に向かない場合があります。

自動化してよいのは、ルール化でき、失敗時の影響を制御でき、ログで検証できる範囲です。

専門判断が必要な領域では、最後に人間レビューを残します。

## 専門家目線のチェックポイント

GitHub Actionsで業務スクリプトを運用する前に、次を確認します。

| チェック項目 | 確認方法 |
|---|---|
| 入力が明確か | ファイル、API、DB、フォームなど入力元を書き出す |
| 出力が明確か | 生成ファイル、投稿先、通知先、デプロイ先を確認する |
| dry-runがあるか | 本番反映なしで同じ処理を試せるか確認する |
| Secretを直書きしていないか | `rg "API_KEY|TOKEN|SECRET"` などで検索する |
| 権限が最小か | `permissions` がworkflow目的に合っているか見る |
| 二重実行を防げるか | `concurrency` の有無を確認する |
| テストがあるか | 失敗時に止めるためのpytestやlintがあるか見る |
| artifactがあるか | 成果物やログが保存されるか確認する |
| 通知があるか | 失敗に気づける導線があるか確認する |
| KPIがあるか | 技術KPIと事業KPIを分けているか確認する |

この表を1つずつ埋めるだけでも、運用事故はかなり減らせます。

## 成果を測るKPI

GitHub Actionsの業務自動化では、KPIを2種類に分けます。

### 技術KPI

技術KPIは、自動化が安定して動いているかを見る数字です。

- workflow成功率
- 平均実行時間
- 連続失敗回数
- テスト成功数
- ビルド成功率
- リトライ発生回数
- artifact保存率
- 手動介入回数
- dry-run成功率

今回のHiroの検証では、対象テスト9件が成功しました。

```text
......... [100%]
```

これは小さな数字ですが、Cloud ModeやAIスロップ防止の最低限の安全装置が動いている証拠になります。

### 事業KPI

事業KPIは、自動化が成果につながっているかを見る数字です。

- 自動生成された記事数
- インデックス登録数
- 検索流入数
- 商品リンククリック数
- CTAクリック率
- コンバージョン数
- 1記事あたりの収益
- 自動化で削減した作業時間
- 人間が修正した記事の割合

ここで注意したいのは、収益やポイントの発生は保証できないということです。

成果は、検索需要、テーマ選定、商品単価、読者の信頼、競合状況、広告規約、サービス規約に左右されます。

そのため、「GitHub Actionsを入れれば稼げる」と考えるのではなく、「改善に必要な作業とデータ収集を自動化する」と考える方が現実的です。

## 反論：GitHub Actionsで業務自動化する必要はあるのか

反論として、「自分のPCのタスクスケジューラやcronで十分ではないか」という意見があります。

小さな個人作業なら、それでも十分な場合があります。

ただし、GitHub Actionsには次の利点があります。

- 実行履歴がGitHubに残る
- コード変更と実行手順を同じリポジトリで管理できる
- SecretsをGitHub側で管理できる
- pushやpull requestと連動できる
- artifactを保存できる
- チームで実行結果を共有しやすい
- PCの電源やローカル環境に依存しない

一方で、GitHub Actionsにも限界があります。

- 実行時間や使用量に制限がある
- GUI操作やログイン状態が必要な処理には向かない場合がある
- 外部サービスの規約変更には対応が必要
- Secret設計を間違えると事故につながる
- 完全な監視基盤ではないため通知設計が別途必要

つまり、GitHub Actionsは万能ではありません。向いているのは、入力と出力が明確で、コマンド化でき、ログで検証できる処理です。

## 類似記事との差別化ポイント

多くの記事は、GitHub ActionsのYAMLの書き方だけを説明します。

この記事では、業務スクリプトを安全に動かすために、次の点まで含めています。

- Hiroの `auto-ai-blog` にある実際のCloud Mode設計を確認
- 2026年7月10日のローカル検証ログを記載
- 9件のテスト成功という具体データを提示
- `docs/workflows/cloud-daily-post.yml` と `docs/daily-post.yml` の権限差を説明
- CIを開発者向け機能ではなく、自動化資産の安全装置として説明
- dry-run、Secrets、permissions、concurrency、artifactを運用単位で整理
- 収益化やポイント獲得を狙う場合の限界も明記

AIで一般論を書くだけなら、誰でも似た記事を作れます。

差が出るのは、実際のリポジトリ、実行ログ、テスト結果、失敗対策、KPIまで入っているかです。

## 読了後すぐにやること

今日やるなら、まず1つだけ実行してください。

**いま手元で毎回実行している業務スクリプトを1つ選び、「入力・処理・出力・失敗時」を4行で書き出す。**

例です。

```text
入力：商品リストCSV
処理：価格と在庫を取得して比較記事を生成
出力：Markdown記事と商品リンク一覧
失敗時：失敗URL、HTTP status、スキップ理由をログに残す
```

次に、ローカルで実行するコマンドを1つに絞ります。

```bash
python scripts/run_daily_task.py --dry-run
```

このdry-runが成功したら、GitHub Actions化の準備に進めます。

書けない場合は、まだ自動化するには処理が曖昧です。先に業務フローを分解してください。

## まとめ：GitHub Actionsは「安全に回る自動化資産」の土台になる

GitHub Actionsは、Pythonを定期実行するだけの道具ではありません。

CI、Secrets、dry-run、permissions、concurrency、artifact、ログ、KPIを組み合わせることで、業務スクリプトを安全に運用する基盤になります。

自動化で目指すべき状態は、人間が毎日クリックすることではありません。人間は設計し、検証し、数字を見て改善する。繰り返し作業は、壊れた時に止まれる形で機械に任せる。この状態を作ることです。

一方で、規約違反の可能性がある処理、読者に誤解を与える収益表現、専門判断が必要な内容まで無人化すると、長期的な資産にはなりません。

最初に作るべきなのは、派手なAI機能ではありません。

壊れた時に止まり、成功した時に記録が残り、改善すべき数字が見える仕組みです。

---

## 本気で自動化・不労所得を構築したい方向けの実践マニュアル

「GitHub Actionsで業務自動化を組めるのは分かった。でも、自分のテーマで何を自動化し、どこに収益導線を置き、どの順番で仕組みにすればいいのか分からない」

そう感じた方は、次の段階に進んでください。

自動化で差がつくのは、ツールの知識ではなく、**収益が発生する作業を分解し、人間が触らなくても回る導線に変える設計力**です。

記事生成、SNS投稿、商品導線、アフィリエイト、デジタル商品、ポイント獲得の仕組みは、場当たり的に作るほど管理不能になります。

実践マニュアルでは、初心者が迷いやすい「何を作るか」「どこを自動化するか」「どのKPIを見るか」「どこで人間レビューを残すか」を、具体的な手順に落とし込んでいます。

本気で、自分の時間を切り売りする働き方から抜け出し、GitHub ActionsやAIを使った自動化資産を作りたい方はこちらから確認してください。

[本気で自動化・不労所得を構築したい方向けの実践マニュアルを見る](/products/)
