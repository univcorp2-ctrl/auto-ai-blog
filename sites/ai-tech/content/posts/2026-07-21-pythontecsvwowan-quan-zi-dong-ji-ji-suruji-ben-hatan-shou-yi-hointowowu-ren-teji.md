---
title: "PythonでCSVを完全自動集計する基本パターン｜収益・ポイントを無人で記録する仕組みの作り方"
date: 2026-07-21T18:55:48+09:00
draft: false
tags:
  - "Python"
  - "CSV"
  - "自動集計"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!PythonでCSVを自動集計する仕組みhttps://image.pollinations.ai/prompt/python%20csv%20automatic%20aggregation%20workflow%20revenue%20dashboard%20clean%20business%2"
---
![PythonでCSVを自動集計する仕組み](https://image.pollinations.ai/prompt/python%20csv%20automatic%20aggregation%20workflow%20revenue%20dashboard%20clean%20business%20illustration?width=800&height=400&nologo=true)

売上CSV、広告レポート、ポイント履歴、アフィリエイト成果を毎朝開き、Excelへ転記していないでしょうか。

集計作業は収益を直接生みません。それでも人間が介在し続けると、件数が増えるほど確認時間が膨らみ、転記ミスや集計漏れも起こります。自分が休んでいる間も収益源を監視するには、**PythonでCSVを自動集計し、結果と実行ログを残す仕組み**が役立ちます。

この記事では、プログラミング初心者でも試せるように、CSVの読み込み、データ検証、カテゴリ別集計、結果保存、定期実行までを順番に解説します。読了後には、次の状態を目指せます。

- CSVが所定フォルダへ入ると自動で集計される
- 売上、ポイント、件数を同じルールで計算できる
- 不正な行を検知し、二重計上を防げる
- 人間は元データではなく、異常と改善候補を確認できる
- 集計結果を商品改善や収益導線の判断材料にできる

ここで扱う自動化は、収益を保証するものではありません。CSV集計は、すでに存在する売上やポイントを正確に把握し、運用コストを減らす技術です。本記事は一般的な情報提供であり、投資助言ではありません。

## PythonによるCSV自動集計の全体像

CSVとは、表形式の情報をカンマ区切りで保存したファイルです。たとえば、次のようなデータを想定します。

```csv
date,transaction_id,channel,amount,status
2026-07-01,A001,blog,1200,approved
2026-07-01,A002,mail,800,pending
2026-07-02,A003,blog,1500,approved
```

各用語を具体例に置き換えると、次のようになります。

- **列**：`date`や`amount`など、データの項目
- **行**：`A001`の取引情報など、1件分の記録
- **集計キー**：`channel`など、結果を分ける基準
- **ステータス**：`approved`など、成果が確定したかを示す状態
- **一意キー**：`transaction_id`など、同じ取引を識別する値

PythonでCSVを自動集計する流れは、次のように整理できます。

```text
収益サービスからCSVを取得
        ↓
入力フォルダへ保存
        ↓
列名・金額・取引IDを検証
        ↓
チャネル別・日付別に集計
        ↓
集計CSVと実行ログを保存
        ↓
異常がある場合のみ通知
```

この形なら、人間が毎回ファイルを開く必要はありません。確認対象を「全明細」から「エラーと変化」に絞れます。

さらに、集計結果を別の処理へ渡せば、売れ筋商品の抽出、伸びている記事の発見、ポイント承認率の監視、CTAの改善候補作成といった収益運用へ展開できます。

![CSV自動集計のデータフロー](https://image.pollinations.ai/prompt/csv%20input%20validation%20python%20aggregation%20report%20alert%20flowchart%20Japanese%20business?width=800&height=400&nologo=true)

## Hiroのサイト運用リポジトリで行った10万行の検証

一般論ではなく、このサイト固有の検証記録を示します。

2026年7月16日、サイト運用リポジトリ上でPython標準ライブラリを使い、合成したCSVデータを集計しました。

**検証条件**

- 実行日：2026年7月16日
- Python：3.11.9
- 入力：プログラム内で生成した10万行の検証データ
- 分類：`blog`、`mail`、`sns`、`direct`
- 金額：1から500までを繰り返す合成値
- 計測範囲：CSVの読み込み開始から集計完了まで
- 結果ファイルの保存時間：計測対象外
- 計測回数：1回

**保存された実行ログ**

```text
python=3.11.9
rows=100000
elapsed_sec=0.250070
totals={'blog': 6225000, 'direct': 6300000,
        'mail': 6250000, 'sns': 6275000}
grand_total=25050000
```

金額は実売上ではなく、計算結果を検証するための合成データです。処理時間も、このPCと条件における1回分の値であり、性能比較用のベンチマークではありません。ストレージ、列数、文字コード、ウイルス対策ソフトなどによって結果は変わります。

この検証から確認できたのは、**10万行の単純な分類・合計処理がPython標準機能で完了し、期待した総額と一致したこと**です。

同じリポジトリでは、商品導線を`generator/products.yaml`で管理しています。検証日の設定では、価格を持つマニュアルが7件あり、設定価格は7,800円、9,800円、12,800円のいずれかでした。商品設定とアクセス・注文CSVを結合すれば、商品別の閲覧数、クリック数、購入数を自動集計できます。

ただし、商品設定の存在は販売実績を意味しません。実際の収益を記載する場合は、注文CSVや決済記録との照合が必要です。

## ステップ・バイ・ステップで作るCSV自動集計

### 1. Pythonの実行環境を確認する

WindowsならPowerShellを開き、次を実行します。

```powershell
python --version
```

バージョン番号が表示されれば、Pythonを起動できます。

```text
Python 3.11.9
```

上記はHiroの検証環境で表示された値です。読者の環境では別のバージョンになる場合があります。

今回はPythonに標準搭載されている`csv`モジュールを使います。`pandas`などの追加ライブラリがない環境でも動かせる構成です。

### 2. 入力CSVの仕様を決める

自動集計を安定させるには、コードより先に入力ルールを決めます。

この記事では、次の5列を必須とします。

| 列名 | 意味 | 例 |
|---|---|---|
| `date` | 成果発生日 | `2026-07-01` |
| `transaction_id` | 取引を識別するID | `A001` |
| `channel` | 流入元・媒体 | `blog` |
| `amount` | 金額またはポイント | `1200` |
| `status` | 承認状態 | `approved` |

`transaction_id`がないCSVでは、同じファイルを再処理した際に二重計上を防ぎにくくなります。サービス側がIDを出力しない場合は、日付、商品名、金額などを組み合わせた識別子を作る方法があります。ただし、同一内容の別取引を誤って重複扱いする可能性があるため、運用前の確認が必要です。

### 3. CSVを読み込み、入力値を検証する

次のコードを`aggregate_csv.py`という名前で保存します。

```python
import csv
import json
import sys
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

INPUT_FILE = Path("input/sales.csv")
OUTPUT_FILE = Path("output/summary.csv")
LOG_FILE = Path("logs/latest.json")

REQUIRED_COLUMNS = {
    "date",
    "transaction_id",
    "channel",
    "amount",
    "status",
}
ALLOWED_STATUS = {"approved", "pending", "rejected"}

started = time.perf_counter()
summary = defaultdict(
    lambda: {
        "rows": 0,
        "approved_amount": Decimal("0"),
        "pending_amount": Decimal("0"),
        "rejected_rows": 0,
    }
)
seen_ids = set()
errors = []
input_rows = 0

try:
    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"必須列がありません: {sorted(missing)}"
            )

        for line_number, row in enumerate(reader, start=2):
            input_rows += 1

            transaction_id = row["transaction_id"].strip()
            channel = row["channel"].strip()
            status = row["status"].strip()

            if not transaction_id:
                errors.append(f"{line_number}行目: IDが空です")
                continue

            if transaction_id in seen_ids:
                errors.append(
                    f"{line_number}行目: IDが重複しています"
                )
                continue
            seen_ids.add(transaction_id)

            if status not in ALLOWED_STATUS:
                errors.append(
                    f"{line_number}行目: 不明なstatusです"
                )
                continue

            try:
                amount = Decimal(row["amount"].strip())
            except InvalidOperation:
                errors.append(
                    f"{line_number}行目: amountが数値ではありません"
                )
                continue

            data = summary[channel]
            data["rows"] += 1

            if status == "approved":
                data["approved_amount"] += amount
            elif status == "pending":
                data["pending_amount"] += amount
            else:
                data["rejected_rows"] += 1

    if errors:
        raise ValueError("; ".join(errors[:10]))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "channel",
            "rows",
            "approved_amount",
            "pending_amount",
            "rejected_rows",
        ])

        for channel, data in sorted(summary.items()):
            writer.writerow([
                channel,
                data["rows"],
                data["approved_amount"],
                data["pending_amount"],
                data["rejected_rows"],
            ])

    result = {
        "ok": True,
        "finished_at": datetime.now().isoformat(),
        "input_rows": input_rows,
        "unique_ids": len(seen_ids),
        "output_groups": len(summary),
        "error_count": 0,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }

except Exception as exc:
    result = {
        "ok": False,
        "finished_at": datetime.now().isoformat(),
        "input_rows": input_rows,
        "error_count": len(errors),
        "error": str(exc),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.write_text(
    json.dumps(result, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if result["ok"] else 1)
```

このコードでは、金額を`float`ではなく`Decimal`で扱っています。`Decimal`は10進数を意図どおりに計算する型で、金額のように端数誤差を避けたいデータに向いています。

### 4. サンプルCSVで動作を確認する

`input`フォルダを作り、`sales.csv`を保存します。

```csv
date,transaction_id,channel,amount,status
2026-07-01,A001,blog,1200,approved
2026-07-01,A002,mail,800,pending
2026-07-02,A003,blog,1500,approved
2026-07-02,A004,sns,300,rejected
```

PowerShellから実行します。

```powershell
python aggregate_csv.py
```

成功すると、`output/summary.csv`へ次の結果が出ます。

```csv
channel,rows,approved_amount,pending_amount,rejected_rows
blog,2,2700,0,0
mail,1,0,800,0
sns,1,0,0,1
```

この金額は上記サンプル4行を前提にした計算結果です。`blog`の確定額は、1,200と1,500を足した2,700です。

同時に`logs/latest.json`が作られます。

```json
{
  "ok": true,
  "input_rows": 4,
  "unique_ids": 4,
  "output_groups": 3,
  "error_count": 0
}
```

完全自動化では、集計CSVの有無より`ok`が`true`かどうかを監視します。古い出力ファイルが残っていると、今回も成功したように見えるためです。

### 5. 壊れたデータで失敗することも確認する

テスト用CSVの金額を次のように変更します。

```csv
2026-07-01,A002,mail,未確定,pending
```

この状態では、プログラムが終了コード`1`を返し、ログの`ok`が`false`になります。

エラー時に処理を止める設計は、無人運転に欠かせません。不正値をゼロとして処理すると、収益減少に見える偽のレポートが生成されるからです。

### 6. Windowsで定期実行する

動作確認後、Windowsのタスクスケジューラへ登録します。

設定例は次のとおりです。

- **トリガー**：収益CSVの保存が完了した後
- **プログラム**：Python実行ファイル
- **引数**：`aggregate_csv.py`
- **開始場所**：スクリプトと`input`フォルダがあるディレクトリ
- **失敗時**：終了コードが`0`以外なら再実行または通知

毎朝の決まった時刻に動かす場合は、CSVの取得完了時刻より後へ設定します。取得前に集計すると、前日ファイルを再処理する危険があります。

より安定させるなら、処理済みファイルを`processed`フォルダへ移し、ファイル名とハッシュ値をログへ記録します。ハッシュ値とは、ファイル内容から作る識別用の文字列です。同じCSVの再投入を検知できます。

### 7. 集計結果を収益改善へつなげる

CSVを自動集計しても、結果を保存するだけでは収益源は育ちません。次の判断まで機械へ渡すと、自動化資産として使いやすくなります。

- 確定額が前回より減ったチャネルを通知する
- 否認率が設定基準を超えた案件を停止候補にする
- 成果が伸びた記事テーマを次回の企画候補へ送る
- 商品別のクリック数と購入数から導線を比較する
- ポイントの承認待ち期間が長い案件を一覧化する

自動変更には危険もあります。価格変更、広告停止、金融取引など、誤作動の影響が大きい操作は、集計結果から直接実行せず、人間の承認段階を残す方が安全です。

## 専門家目線のチェックポイント

### 入力件数と処理件数を照合する

次の関係が成立するか確認します。

```text
入力件数
＝ 正常処理件数
＋ 重複件数
＋ エラー件数
```

数字が合わなければ、どこかの行が無言で消えている可能性があります。

### 確定・承認待ち・否認を分ける

`pending`を確定収益へ混ぜると、利用可能な金額を過大評価します。ポイント案件やアフィリエイトでは、発生額と確定額を別列で管理してください。

### 金額に浮動小数点数を使わない

`float`は計算方法の都合で小さな誤差が出る場合があります。金額には`Decimal`、整数ポイントには`int`が適しています。

### 出力を途中状態で公開しない

処理中にプログラムが停止すると、不完全なCSVが残ることがあります。実務では一時ファイルへ書き出し、成功後に正式ファイルへ置き換える**アトミック更新**を検討します。アトミック更新とは、完成した結果だけを一度に反映する方法です。

### ログへ個人情報を出しすぎない

メールアドレス、氏名、注文番号をそのままログへ残すと、情報漏えい時の影響が広がります。エラー箇所の特定に不要な情報はマスクしてください。

## 画像で説明すべき箇所と視覚的証拠

記事内には、次のスクリーンショットまたは図解を入れると理解が深まります。

![入力件数と集計結果を照合するダッシュボード](https://image.pollinations.ai/prompt/python%20csv%20validation%20dashboard%20input%20rows%20errors%20duplicates%20totals%20clean%20UI?width=800&height=400&nologo=true)

**推奨する視覚的証拠**

- 左側：入力CSVの先頭行と列名
- 中央：検証、重複除外、集計の処理フロー
- 右側：`input_rows`、`error_count`、`ok`を表示したログ
- 下部：チャネル別の確定額と承認待ち額の棒グラフ

抽象的な「AIが働く画像」より、入力件数と出力件数が一致している画面の方が、集計の信頼性を伝えられます。

## よくある失敗と対策

### `UnicodeDecodeError`が出る

**原因**：CSVがUTF-8ではなく、CP932などで保存されている可能性があります。

**対策**：提供元の仕様を確認し、必要なら次のように変更します。

```python
encoding="cp932"
```

文字コードを推測だけで固定すると、別サービスのCSVで壊れる場合があります。

### 金額の合計が合わない

**原因**：`1,200円`、空欄、全角数字などが混在しています。

**対策**：集計前にカンマや通貨記号を除去し、変換できない行はエラーへ分離します。変換失敗をゼロ扱いにすると異常を見落とします。

### 同じ成果が二重計上される

**原因**：同じCSVを再度読み込んでいます。

**対策**：取引ID、処理済みファイル名、ファイルハッシュのいずれかを保存し、再処理を拒否します。

### タスクスケジューラでは動かない

**原因**：「開始場所」が未設定で、相対パスの`input/sales.csv`を見つけられないケースがあります。

**対策**：開始場所を設定するか、スクリプト自身の場所を基準に絶対パスを組み立てます。

### 出力CSVはあるのに処理が失敗している

**原因**：前回成功時のファイルが残っています。

**対策**：更新日時に加え、今回のログにある`ok`、`finished_at`、`input_rows`を確認します。

## PythonによるCSV自動集計が向かないケース

次のような業務では、別の方法が適している場合があります。

- 元データの形式が毎回大幅に変わる
- 紙や画像を目視しないと内容を判断できない
- 数件しかなく、実行頻度も低い
- 集計ルールが担当者の感覚に依存している
- サービス規約がデータの自動取得を禁止している
- 誤集計による法務・会計上の影響が大きい

特に税務や会計の確定処理では、自動集計結果をそのまま申告値に使わず、専門家や正式な会計記録との照合が必要です。

## 成果を測るKPI

CSV自動集計の価値は、処理速度以外の指標でも測ります。

| KPI | 計算方法・確認内容 |
|---|---|
| 自動処理成功率 | 成功回数 ÷ 全実行回数 |
| データ完全率 | 正常処理件数 ÷ 入力件数 |
| 重複検知件数 | 再投入を防いだ取引数 |
| 集計差額 | 元CSVの総額 − 集計後の総額 |
| 手作業時間 | 導入前後で人間が集計に使った時間 |
| 異常検知時間 | CSV到着からエラー通知までの時間 |
| 確定率 | 確定件数 ÷ 発生件数 |
| チャネル別成果 | 媒体ごとの確定額、件数、購入率 |

たとえば、導入前に1回10分の集計を月30回行っていたなら、手作業時間は月300分です。これは「1回10分、月30回」という前提に基づく試算であり、実際の削減量は各自の作業時間を計測して判断します。

削減した時間を商品ページ、記事、メール導線の改善へ移せれば、集計プログラムは時短ツールから運用資産へ変わります。

## 類似するPython・CSV記事との違い

一般的な入門記事は、`read_csv`や`groupby`の使い方を説明して終わりがちです。本記事では、無人運転を前提として次の範囲まで扱いました。

- 必須列の検証
- 不正な金額の拒否
- 取引IDによる重複防止
- 確定額と承認待ち額の分離
- 成功・失敗ログの保存
- 終了コードによる自動監視
- 定期実行後の改善判断
- 10万行のサイト固有検証ログ

速いコードよりも、失敗を検知できるコードの方が長期運用には向いています。人間が介在しない仕組みほど、異常時に停止し、原因を残す設計が求められます。

## まとめ：今日から取るべき行動

最初の行動として、普段手作業で集計しているCSVを1つ選び、次の項目を書き出してください。

- 合計したい列
- 分類に使う列
- 取引を識別する列
- 確定・承認待ち・否認の扱い
- 正常終了を判断する条件
- エラー時の通知先

その後、この記事のサンプルコードを使い、まず手動実行で正常系と異常系を確認します。集計値とログが一致してから、タスクスケジューラへ登録してください。

PythonによるCSV自動集計は、収益そのものを生み出す魔法ではありません。一方で、売上やポイントの確認に人間の時間を使い続ける状態から離れ、機械が数字を監視する環境を作れます。

集計、通知、商品改善、コンテンツ更新までをつなげれば、寝ている間も動く仕組みへ育てられます。完全自動化を目指すなら、最初から大規模なシステムを作るのではなく、**1つのCSVを、検証付きで、毎回同じ結果に変える処理**から始めてください。

## 本気で自動化・不労所得の仕組みを構築したい方へ

「コードは動いた。でも、収益につながる導線まで組めない」  
「記事、商品、集客、計測がバラバラで、結局毎日自分が作業している」

そんな状態から抜け出すには、CSV集計の先にある**収益導線、定期実行、異常監視、改善ループ**まで一つの仕組みとして設計する必要があります。

本気で、自分が画面の前にいない時間にも動き続ける自動化資産を作りたい方へ、実践手順をまとめたマニュアルを用意しています。成果を保証するものではありませんが、試行錯誤を場当たり的に繰り返すより、完成形から逆算して構築したい方に向いています。

**次に作るべき仕組みを、商品一覧から選んでください。**

[**自動化・収益化の実践マニュアルを見る →**](/products/)
