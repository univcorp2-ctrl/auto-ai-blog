# 完全無人AIトレードBot VPS環境構築マニュアル

本マニュアルは、作成した仮想通貨のアービトラージBot（自動取引システム）を、24時間365日安定して稼働させるためのVPS（Virtual Private Server）環境構築手順を解説します。

## 1. VPSの契約
自宅のPCではなく、常にインターネットに接続され稼働し続けるサーバーを借ります。
- **おすすめのVPS**: ConoHa VPS, さくらのVPS, Vultr, Linode, AWS EC2など
- **推奨OS**: Ubuntu 22.04 LTS または Ubuntu 20.04 LTS
- **スペック**: メモリ1GB〜2GB、CPU1〜2コア程度で十分動作します。

## 2. サーバーへのSSH接続
VPSを契約すると、IPアドレスと初期パスワード（またはSSHキー）が発行されます。PCのターミナル（Windowsの場合はPowerShell、Macの場合はターミナル）を開き、接続します。

```bash
# IPアドレスの部分を自分のVPSのものに変更してください
ssh root@YOUR_VPS_IP_ADDRESS
```

## 3. システムのアップデートと必要パッケージのインストール
サーバーに接続したら、まずはセキュリティ確保のためシステムを最新状態にします。

```bash
sudo apt update && sudo apt upgrade -y
```

次に、Python環境やBotをバックグラウンドで動かすためのツールをインストールします。

```bash
sudo apt install -y python3 python3-pip git screen nano
```

## 4. Botスクリプトの配置と設定
Botを動かすためのディレクトリを作成し、移動します。

```bash
mkdir -p ~/trading_bot
cd ~/trading_bot
```

ここで、`arbitrage_bot.py` を作成（またはアップロード）します。
今回は `nano` エディタを使ってファイルを作成します。

```bash
nano arbitrage_bot.py
```
（開いた画面にPythonコードを貼り付けます。貼り付け後、`Ctrl + O` で保存し、`Enter` を押し、`Ctrl + X` で閉じます。）

**※重要※**
コード内の `YOUR_BINANCE_API_KEY` 等の箇所は、事前に各仮想通貨取引所で発行したAPIキーとシークレットキーに必ず書き換えてください。

## 5. Pythonライブラリのインストール
取引所のAPIに簡単にアクセスするためのライブラリ `ccxt` をインストールします。

```bash
pip3 install ccxt
```

## 6. 24時間稼働の設定 (Screenコマンドの使用)
SSH接続を切断してもBotが動き続けるように、仮想端末を作成する `screen` コマンドを使用します。

新しいセッションを作成して入ります：
```bash
screen -S bot_session
```

セッションの中でBotを起動します：
```bash
python3 arbitrage_bot.py
```

ログが画面に出力され始めたら、キーボードで **`Ctrl + A` を押し、次に `D` を押します。**
これでセッションから「デタッチ」され、バックグラウンドでBotが動き続けます。この状態でSSH接続を切断（ターミナルを閉じる）しても問題ありません。

後から動作状況を確認したい場合は、再度SSH接続して以下のコマンドを実行します：
```bash
screen -r bot_session
```

## 7. サーバー再起動時の自動起動設定 (上級者向け)
メンテナンス等でVPSが再起動した際にも、自動的にBotが立ち上がるようにするには `systemd` を利用します。

サービスファイルを作成します：
```bash
sudo nano /etc/systemd/system/trading_bot.service
```

以下の内容を貼り付けて保存します（パスはご自身の環境に合わせてください）：
```ini
[Unit]
Description=Arbitrag

e Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/trading_bot
ExecStart=/usr/bin/python3 /root/trading_bot/arbitrage_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

設定を反映し、自動起動を有効化して起動します：
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading_bot
sudo systemctl start trading_bot
```

稼働状況の確認：
```bash
sudo systemctl status trading_bot
```

---
> **免責事項**
> 本コードおよびマニュアルは学習および検証を目的としており、利益を保証するものではありません。APIキーの取り扱いには細心の注意を払い、少額でのテスト運用（あるいはテストネットでの運用）から始めることを強く推奨します。投資は自己責任で行ってください。


