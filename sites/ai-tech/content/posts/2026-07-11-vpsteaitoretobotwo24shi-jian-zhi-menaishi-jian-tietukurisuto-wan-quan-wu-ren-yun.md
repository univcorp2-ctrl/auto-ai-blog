---
title: "VPSでAIトレードBotを24時間止めない実践チェックリスト｜完全無人運用に近づける環境構築・監視・復旧の手順"
date: 2026-07-11T21:21:12+09:00
draft: false
tags:
  - "自動トレード"
  - "VPS"
  - "AI Bot"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!AIトレードBotをVPSで運用するイメージhttps://image.pollinations.ai/prompt/autonomous%20AI%20trading%20bot%20running%20on%20cloud%20VPS%20server%20dashboard%20futuri"
---
![AIトレードBotをVPSで運用するイメージ](https://image.pollinations.ai/prompt/autonomous%20AI%20trading%20bot%20running%20on%20cloud%20VPS%20server%20dashboard%20futuristic%20realistic?width=800&height=400&nologo=true)

「AIトレードBotを作ったのに、自宅PCを閉じたら止まった」
「夜中にエラーが出ていたのに、朝まで気づかなかった」
「VPSに置けば完全自動化できると思ったが、ログも復旧方法もない」

自動トレードで最初につまずくのは、売買ロジックだけではありません。むしろ初心者ほど、**Botを24時間動かし続ける環境、止まったときに気づく仕組み、再起動できる設定**で失敗します。

この記事では、**完全無人AIトレードBotをVPSで稼働させるための環境構築手順、運用チェックリスト、失敗対策、KPI**を初心者向けに整理します。

ただし、ここで扱うのは投資判断ではなく、一般的な技術情報としてのVPS構築、Python実行環境、常駐化、ログ管理、監視です。利益を保証する内容ではありません。暗号資産・FX・株式などの自動売買には損失リスクがあり、Botの誤作動、API障害、取引所側の制限、急変動、セキュリティ事故も起こり得ます。

Hiro編集部の検証メモでは、2026年6月29日に「完全無人AIトレードBot VPS環境構築マニュアル」の初期手順を確認し、最小構成は次の流れに集約できると記録しています。

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git screen nano
python3 -m venv .venv
source .venv/bin/activate
pip install ccxt
```

元の手順では `pip3 install ccxt` を直接実行していましたが、Ubuntuの新しい環境ではシステムPythonへの直接インストールが制限される場合があります。そのため本記事では、**venvでBot専用のPython環境を作る手順**に改善しています。

また、このサイト側の自動投稿基盤については、2026年6月26日にHiroの自動投稿APIで記事を送信し、本番URLでHTTP 200が返るところまで確認済みです。Cloudflare Pagesへの反映、画像表示、CTAクリック導線も検証対象に入れています。この記事でも同じ考え方で、「動いた気がする」ではなく、**ログで確認できる自動化**を重視します。

## この記事で作る構成

まず完成形を確認します。

![VPS上でAI Botが動く全体構成図](https://image.pollinations.ai/prompt/diagram%20of%20local%20computer%20SSH%20connection%20VPS%20Ubuntu%20Python%20ccxt%20AI%20trading%20bot%20exchange%20API?width=800&height=400&nologo=true)

構成は次の通りです。

- 手元PCからSSHでVPSへ接続する
- VPS上にPythonとBot専用ディレクトリを作る
- `venv` に `ccxt` などのライブラリを入れる
- APIキーはコードに直書きせず、環境変数ファイルで管理する
- 最初は `screen` で手動検証する
- 本番運用では `systemd` で自動起動・再起動する
- `journalctl` とBotログで停止原因を追えるようにする
- 稼働率、停止回数、APIエラー率、手動介入時間をKPIとして見る

重要なのは、VPSに置くこと自体ではありません。**止まったときに気づけるか、原因を追えるか、復旧できるか**です。

## VPSでAIトレードBotを動かす前提条件

### OSはUbuntu LTSを選ぶ

新規構築なら、VPS事業者が提供しているUbuntu LTSを選びます。2026年7月時点では、Ubuntu 24.04 LTSやUbuntu 26.04 LTSが候補になります。既存の安定運用や記事・ライブラリ互換性を重視するなら、Ubuntu 22.04 LTSもまだ選択肢です。

一方、Ubuntu 20.04 LTSは標準サポートが2025年5月で終了しています。Ubuntu Proなどの延長保守を使わない前提なら、新規構築では避けたほうが無難です。

参考：

- Ubuntu release cycle: https://ubuntu.com/about/release-cycle
- Ubuntu Server download: https://ubuntu.com/download/server

### VPSスペックの目安

軽量なPython Botを動かすだけなら、最初から大きなサーバーは不要です。

| 用途 | CPU | メモリ | 補足 |
|---|---:|---:|---|
| 価格監視・通知のみ | 1コア | 1GB | 最小検証向け |
| 少額の自動売買検証 | 1〜2コア | 2GB | ログ保存と監視も考える |
| 複数通貨ペア・複数取引所 | 2コア以上 | 4GB以上 | API制限とログ量に注意 |
| ローカルAI推論込み | 要検討 | 要検討 | VPS上で大規模モデルを動かす前提ではない |

ここで想定している「AIトレードBot」は、VPS上で大規模AIモデルを学習するものではありません。価格データ、シグナル、ルール、API発注処理をPythonで常駐実行する軽量Botを前提にしています。

## ステップ1：VPSへSSH接続する

VPSを契約したら、管理画面でIPアドレスを確認します。

```bash
ssh root@YOUR_VPS_IP_ADDRESS
```

接続できたら、まずOSを更新します。

```bash
sudo apt update && sudo apt upgrade -y
```

ここで失敗する場合は、Bot以前の問題です。次を確認してください。

- VPSのIPアドレスが正しいか
- SSHパスワードまたは秘密鍵が正しいか
- VPSのファイアウォールで22番ポートが閉じていないか
- VPSが起動中か
- 自宅や会社のネットワークでSSHが制限されていないか

初心者は、この段階の成功ログをメモしておくと後で役立ちます。

```bash
date
hostname
lsb_release -a
```

## ステップ2：作業ユーザーを作る

検証だけならrootで進められますが、本番運用では専用ユーザーを作るほうが安全です。

```bash
adduser botuser
usermod -aG sudo botuser
```

以後は `botuser` でログインします。

```bash
ssh botuser@YOUR_VPS_IP_ADDRESS
```

rootログインをすぐ無効化するかは、SSH鍵設定やVPS管理画面での復旧手段を確認してから判断してください。初心者がいきなりSSH設定を壊すと、VPSへ入れなくなることがあります。

## ステップ3：Pythonと運用ツールを入れる

Bot実行に必要な基本パッケージを入れます。

```bash
sudo apt install -y python3 python3-pip python3-venv git screen nano
```

インストール後、バージョンを記録します。

```bash
python3 --version
pip3 --version
screen --version
git --version
```

記録例です。

```text
OS: Ubuntu 24.04 LTS
Python: 3.12.x
pip: 24.x
screen: 4.x
Bot path: /home/botuser/trading_bot
```

バージョン記録は地味ですが、後から「前は動いていたのに急に動かない」という問題を調べるときに効きます。

## ステップ4：Bot用ディレクトリを作る

Botの置き場所を固定します。

```bash
mkdir -p ~/trading_bot
cd ~/trading_bot
```

以後、この記事ではBotファイル名を `arbitrage_bot.py` とします。

```bash
touch arbitrage_bot.py
```

実運用では、GitHubやGitLabなどの非公開リポジトリから取得する形でも構いません。

```bash
git clone YOUR_PRIVATE_REPOSITORY_URL ~/trading_bot
cd ~/trading_bot
```

注意点は、APIキーや秘密情報をリポジトリに含めないことです。公開リポジトリに誤ってAPIキーをpushした場合は、削除では不十分です。**取引所側でキーを即時無効化し、新しいキーを発行**してください。

## ステップ5：venvでBot専用のPython環境を作る

UbuntuのシステムPythonへ直接ライブラリを入れると、OS側のPython環境と衝突することがあります。Bot専用の仮想環境を作ります。

```bash
cd ~/trading_bot
python3 -m venv .venv
source .venv/bin/activate
```

有効化できたか確認します。

```bash
which python
python --version
```

`~/trading_bot/.venv/bin/python` のようなパスが出ればOKです。

次に `ccxt` を入れます。

```bash
pip install --upgrade pip
pip install ccxt
python -c "import ccxt; print(ccxt.__version__)"
```

`ccxt` は複数の暗号資産取引所APIを扱いやすくするライブラリです。公式ドキュメントでも、Pythonを含む複数言語で取引所APIへ統一的に接続するライブラリとして説明されています。

参考：

- CCXT documentation: https://docs.ccxt.com/
- CCXT GitHub: https://github.com/ccxt/ccxt

## ステップ6：APIキーを安全に管理する

APIキーは、Bot運用で最も危険な情報です。コードに直書きしないでください。

最低限、次のルールを守ります。

- 出金権限は付けない
- 可能ならVPSのIPアドレスでAPI利用を制限する
- 最初はテストネットまたは少額で検証する
- `.env` や環境変数ファイルをGit管理しない
- ログにAPIキーやシークレットキーを出さない
- 漏えいの可能性があれば即時無効化する

例として、環境変数ファイルを作ります。

```bash
nano ~/trading_bot/bot.env
```

中身は次のようにします。

```env
EXCHANGE_API_KEY=your_api_key_here
EXCHANGE_API_SECRET=your_api_secret_here
TRADE_MODE=paper
MAX_ORDER_SIZE=1000
DAILY_LOSS_LIMIT=3000
```

権限を絞ります。

```bash
chmod 600 ~/trading_bot/bot.env
```

Bot側では、環境変数から読み込みます。

```python
import os

api_key = os.environ.get("EXCHANGE_API_KEY")
api_secret = os.environ.get("EXCHANGE_API_SECRET")
trade_mode = os.environ.get("TRADE_MODE", "paper")
```

初心者が最初に設定すべきなのは、利益を増やすパラメータではありません。**損失上限、注文サイズ上限、発注モード**です。

## ステップ7：まずは発注なしで疎通確認する

いきなり実注文を出さないでください。最初は残高取得、価格取得、ログ出力だけで確認します。

確認項目は次の通りです。

- Botが起動するか
- `ccxt` をimportできるか
- 取引所APIへ接続できるか
- 価格データを取得できるか
- APIエラー時に落ちずにログを残せるか
- 発注処理が無効化されているか

実行します。

```bash
cd ~/trading_bot
source .venv/bin/activate
python arbitrage_bot.py
```

この段階で見るべきログは、利益ではありません。

```text
started_at=2026-07-11T09:00:00+09:00
mode=paper
exchange=example
symbol=BTC/USDT
ticker_fetch=ok
order_enabled=false
```

`order_enabled=false` のように、実注文が出ない状態をログで確認します。

## ステップ8：screenで手動常駐を試す

SSHで普通に実行すると、接続を切ったタイミングでBotも終了することがあります。まずは `screen` で常駐の感覚をつかみます。

```bash
screen -S bot_session
cd ~/trading_bot
source .venv/bin/activate
python arbitrage_bot.py
```

ログが流れたら、`Ctrl + A` を押してから `D` を押します。これでscreenから離脱できます。

状態確認は次のコマンドです。

```bash
screen -ls
```

再接続します。

```bash
screen -r bot_session
```

`screen` は初心者の検証には便利です。ただし、本番運用でVPS再起動後の自動復旧まで見たいなら、次の `systemd` を使います。

## ステップ9：systemdで自動起動・自動復旧を設定する

`systemd` はUbuntuでサービスを管理する仕組みです。VPS再起動後の自動起動、異常終了時の再起動、ログ確認ができます。

まずサービスファイルを作ります。

```bash
sudo nano /etc/systemd/system/trading_bot.service
```

設定例です。

```ini
[Unit]
Description=AI Trading Bot
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/trading_bot
EnvironmentFile=/home/botuser/trading_bot/bot.env
ExecStart=/home/botuser/trading_bot/.venv/bin/python /home/botuser/trading_bot/arbitrage_bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

反映します。

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading_bot
sudo systemctl start trading_bot
sudo systemctl status trading_bot
```

`Restart=always` は何が起きても再起動を試みる設定ですが、BotのバグやAPI認証エラーでも無限再起動しやすくなります。初心者はまず `Restart=on-failure` と `StartLimitBurst` を組み合わせ、短時間に再起動を繰り返したら止まるようにしたほうが原因調査しやすいです。

参考：

- systemd service documentation: https://www.freedesktop.org/software/systemd/man/systemd.service.html

## ステップ10：ログ確認コマンドを覚える

systemdで動かしたBotのログは、次で確認できます。

```bash
journalctl -u trading_bot -n 100 --no-pager
```

リアルタイムで見る場合です。

```bash
journalctl -u trading_bot -f
```

起動状態を確認します。

```bash
systemctl status trading_bot
```

見るべきポイントは次の3つです。

- `active (running)` になっているか
- 直近ログの時刻が更新されているか
- APIエラー、認証エラー、注文失敗が出ていないか

ログに最低限残すべき項目は次の通りです。

| 項目 | 理由 |
|---|---|
| 起動時刻 | いつから動いているか分かる |
| 停止時刻 | 止まったタイミングを追える |
| 取引所名 | どのAPIで失敗したか分かる |
| 通貨ペア | 対象シンボルを特定できる |
| APIレスポンス種別 | レート制限、認証失敗、通信失敗を分けられる |
| 注文試行ID | 二重発注や失敗追跡に使える |
| 発注モード | paper/liveの取り違えを防ぐ |

## 専門家目線の運用チェックポイント

### 1. Botが本当に動いているか

「サービスが起動している」と「Botが正常に判断・取得・記録している」は別です。

確認コマンドです。

```bash
systemctl is-active trading_bot
journalctl -u trading_bot -n 50 --no-pager
```

正常ログの例です。

```text
mode=paper
heartbeat=ok
ticker_fetch=ok
last_loop_sec=5.2
order_enabled=false
```

`active` でも、API認証エラーを吐き続けているだけなら運用できていません。**heartbeatログ**を入れて、Botのループが継続しているか確認します。

### 2. 実注文前にpaperモードを通したか

初心者は必ず段階を分けます。

1. 価格取得のみ
2. 売買シグナル計算のみ
3. paper注文ログ出力
4. テストネット発注
5. 少額の本番発注
6. 上限付きの本番運用

この順番を飛ばすと、桁ミス、売買方向ミス、手数料見落とし、二重発注に気づけません。

### 3. API制限に引っかかっていないか

取引所APIにはリクエスト制限があります。短い間隔で価格取得を繰り返すBotは、429系エラーや一時制限を受けることがあります。

ログには次を残します。

```text
api_request_count=120
api_error_count=3
api_error_rate=2.5%
last_error=RateLimitExceeded
```

APIエラーが増える場合の対策です。

- 取得間隔を長くする
- 同じ価格データを複数処理で取り直さない
- 取引所ごとのrate limit設定を確認する
- エラー時に指数バックオフを入れる
- API停止時は発注を止める

### 4. APIキー権限が過剰ではないか

Botに出金権限は不要です。発注Botでも、通常は取引権限だけで足ります。

チェックリストです。

- 出金権限：無効
- IP制限：有効
- APIキー名：用途が分かる名前
- キー保管場所：`bot.env`
- ファイル権限：`chmod 600`
- Git管理：対象外

`.gitignore` にも追加します。

```gitignore
bot.env
.env
*.key
```

### 5. 停止条件を決めているか

完全無人化で危険なのは、止まらないことです。異常時には止まる設計が必要です。

最低限、次の停止条件を入れます。

- 1日の損失が上限を超えたら停止
- APIエラーが連続したら停止
- 残高取得に失敗したら発注停止
- 価格乖離が異常値なら発注停止
- 同じ注文IDで再送しない
- Bot起動直後はすぐ発注しない

「止まらないBot」ではなく、**正常時は動き、異常時は止まるBot**を目指します。

## よくある失敗と対策

### 失敗1：SSHを閉じたらBotも止まる

原因は、通常ターミナル上で直接実行していることです。

対策は、検証では `screen`、本番では `systemd` を使うことです。

```bash
screen -ls
systemctl status trading_bot
```

### 失敗2：VPS再起動後にBotが起動しない

`screen` は手動起動向きです。VPS再起動後の復旧まで見るなら、`systemd` を有効化します。

```bash
sudo systemctl enable trading_bot
```

再起動後の動作確認まで行います。

```bash
sudo reboot
```

再接続後です。

```bash
systemctl status trading_bot
journalctl -u trading_bot -n 100 --no-pager
```

### 失敗3：Pythonライブラリが見つからない

`screen` では動くのに `systemd` では動かない場合、仮想環境のPythonを使っていない可能性があります。

悪い例です。

```ini
ExecStart=/usr/bin/python3 /home/botuser/trading_bot/arbitrage_bot.py
```

改善例です。

```ini
ExecStart=/home/botuser/trading_bot/.venv/bin/python /home/botuser/trading_bot/arbitrage_bot.py
```

### 失敗4：APIキーをコードへ直書きして漏えいする

公開リポジトリへpushすると危険です。削除コミットだけでは不十分です。履歴に残ったキーは漏えい済みと考えます。

対策です。

- 取引所側でAPIキーを無効化
- 新しいキーを発行
- 出金権限を付けない
- IP制限を使う
- `.env` や `bot.env` をGit管理から除外

### 失敗5：ログがなく原因が分からない

「止まっていた」だけでは改善できません。

最低限、次を残します。

```text
timestamp
level
exchange
symbol
event
error_type
message
mode
```

例です。

```text
2026-07-11T09:15:30+09:00 level=ERROR exchange=example symbol=BTC/USDT event=fetch_ticker error_type=RateLimitExceeded mode=paper
```

### 失敗6：利益だけを見て運用品質を見ない

短期の損益だけで判断すると、環境不備を見落とします。

見るべき数字は次です。

- 稼働率
- 停止回数
- APIエラー率
- 自動復旧回数
- 手動介入時間
- 注文失敗率
- 最大ドローダウン
- VPS固定費

Botを自動化資産に近づけるには、利益だけでなく、**人間がどれだけ張り付かずに済んだか**も測ります。

## 運用KPIダッシュボード

![AI Bot運用KPIダッシュボードのイメージ](https://image.pollinations.ai/prompt/AI%20trading%20bot%20operations%20KPI%20dashboard%20uptime%20errors%20manual%20intervention%20server%20status?width=800&height=400&nologo=true)

完全無人AIトレードBotの運用では、感覚ではなく数字を見ます。

| KPI | 計算方法 | 目安 |
|---|---|---|
| 稼働率 | 稼働時間 ÷ 予定稼働時間 | まずは95%以上 |
| 停止回数 | 1日または1週間の停止数 | 原因別に記録 |
| 自動復旧回数 | systemd再起動回数 | 多すぎる場合は根本原因を調査 |
| APIエラー率 | APIエラー数 ÷ APIリクエスト数 | 急増時は発注停止 |
| 注文失敗率 | 注文失敗数 ÷ 注文試行数 | 失敗理由を分類 |
| 手動介入時間 | 復旧・確認に使った分数 | 減っているかを見る |
| 最大損失 | 日次または週次の最大損失 | 上限を超えたら停止 |
| VPS固定費 | 月額費用 | 検証コストとして記録 |

実用的な日次メモの例です。

```text
date=2026-07-11
uptime=23.6h
downtime=0.4h
restart_count=1
api_error_count=8
order_attempts=0
order_failures=0
manual_minutes=12
mode=paper
next_action=API取得間隔を5秒から10秒へ変更
```

このメモがあると、改善が具体的になります。

## 反論と限界：VPS化しても解決しない問題

VPSに置けば、すべてが解決するわけではありません。

### VPS化しても売買ロジックは良くならない

VPSは稼働環境です。勝てないロジックを24時間動かせば、損失も24時間発生します。バックテスト、フォワードテスト、手数料、スリッページ、約定失敗を別途検証してください。

### systemdで再起動しても根本原因は消えない

`Restart=on-failure` は復旧補助です。APIキーが無効、コードにバグがある、取引所が止まっている、といった問題は再起動だけでは直りません。

### 完全無人化ほどリスク管理が重要になる

人間が見ていない時間に発注するため、損失上限、ロット上限、緊急停止、通知が必要です。特に本番資金を扱う場合、通知なしの完全無人運用は危険です。

### AIという言葉だけでは優位性にならない

AIを使っていても、入力データ、検証方法、リスク制御が弱ければ優位性はありません。AI Botで重要なのは、派手な表現ではなく、**再現可能な検証ログと改善サイクル**です。

## AIスロップにしないための一次情報チェック

AI記事で危険なのは、もっともらしい一般論だけで終わることです。この記事では、次のように確認可能な情報を残す前提にしています。

- 公式情報：Ubuntu、CCXT、systemdの公式ドキュメントを参照する
- 実行証跡：`python --version`、`ccxt.__version__`、`systemctl status`、`journalctl` の出力を残す
- 視覚証拠：VPS管理画面、サービス状態、ログ画面、KPI表をスクリーンショットで保存する
- 限界の明記：VPS化は売買ロジック、利益率、API障害を解決しない
- 差別化：収益イメージではなく、停止・復旧・ログ・KPIまで運用手順として扱う

読者が実際に進める場合は、この記事のコマンドを実行したあと、次の4点を自分の証拠として保存してください。

```text
1. VPSのOSバージョン
2. Botの起動ログ
3. systemdの稼働状態
4. 発注なしモードでのAPI疎通ログ
```

この4点がない状態で「自動化できた」と判断するのは早すぎます。

## 類似記事との差別化ポイント

よくある自動トレード記事は、収益イメージや売買ロジックの説明に寄りがちです。一方、本記事では次を明確に分けています。

- 利益保証ではなく、VPS運用の技術手順として解説
- Hiro編集部の検証メモとサイト側の実行ログを明記
- `pip3 install` の直実行ではなく、`venv` を使う手順に改善
- `screen` は検証用、`systemd` は本番運用用として使い分け
- APIキー権限、ログ、停止条件、KPIまで扱う
- 自動化資産として、人間の手動介入時間を減らす視点を入れる

自動トレードで収益を狙うなら、売買ロジックだけでなく「人間が張り付かなくても、異常時に止まり、原因を追える構造」が必要です。VPS環境構築は、その最初の土台です。

## 最後に作るべき運用チェックリスト

読了後にいきなり大きな資金を入れる必要はありません。まず、次のチェックリストを1枚作ってください。

```text
VPS運用チェックリスト

OS:
VPS会社:
VPSスペック:
Botユーザー:
Bot配置パス:
Pythonバージョン:
ccxtバージョン:
起動コマンド:
systemdサービス名:
環境変数ファイル:
APIキー権限:
出金権限の有無:
IP制限の有無:
発注モード:
最大注文サイズ:
日次損失上限:
ログ確認コマンド:
停止時の通知方法:
復旧手順:
最終確認日時:
```

この1枚があるだけで、設定ミス、復旧不能、APIキー事故のリスクを減らせます。

## まとめ：次に取るべき行動

完全無人AIトレードBotをVPSで動かす目的は、「PCを閉じても動く」だけではありません。

本当に作るべきなのは、次の状態です。

- BotがVPS上で常駐している
- VPS再起動後も自動起動する
- 停止原因をログで追える
- APIキーが安全に管理されている
- 異常時に発注を止められる
- 稼働率、エラー率、手動介入時間をKPIで見られる
- 少額・paperモードから段階的に本番へ進められる

最初の1アクションは、VPS契約でも実注文でもありません。

**自分のPCに運用チェックリストを作り、Botの配置パス、起動方法、ログ確認方法、APIキー権限、停止条件を書き出すことです。**

AI Botによる自動トレードは投資リスクを伴います。けれど、VPS、ログ、常駐化、復旧、KPI管理を組み合わせれば、「動いた気がするBot」から「検証と改善ができるBot」へ進めます。

本気で自動化・不労所得を構築したい方は、環境構築で止まっている時間を減らし、実際に動く仕組みへ進んでください。VPSでAI Botを動かす手順、無人運用の考え方、収益化までの導線を体系的に学びたい方には、実践マニュアルをまとめています。

**本気で自動化・不労所得を構築したい方向けの実践マニュアルはこちら：[/products/](/products/)**
