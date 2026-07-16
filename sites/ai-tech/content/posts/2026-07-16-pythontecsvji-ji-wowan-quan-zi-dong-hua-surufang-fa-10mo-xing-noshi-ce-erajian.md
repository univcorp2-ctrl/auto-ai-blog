---
title: "PythonでCSV集計を完全自動化する方法｜10万行の実測・エラー検知・定期実行まで"
date: 2026-07-16T15:10:51+09:00
draft: false
tags:
  - "Python"
  - "CSV"
  - "自動集計"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!PythonでCSVを自動集計するワークフローhttps://image.pollinations.ai/prompt/python%20csv%20automatic%20aggregation%20workflow%20dashboard%20clean%20business%20illust"
---
![PythonでCSVを自動集計するワークフロー](https://image.pollinations.ai/prompt/python%20csv%20automatic%20aggregation%20workflow%20dashboard%20clean%20business%20illustration?width=800&height=400&nologo=true)

毎週届く売上CSVをExcelで開き、列を並べ替え、商品別の合計を計算する。広告、アフィリエイト、ポイント案件の成果を別々の管理画面から転記する。月末になると、同じ集計をまた繰り返す――。

一つひとつは小さな作業でも、手作業を続ける限り、取引件数が増えるほど自分の時間が削られます。そこで役立つのが、**PythonによるCSVの自動集計**です。

この記事では、プログラミング初心者でも再現できるように、CSVの読み込み、分類、合計、結果の書き出しまでを段階的に解説します。さらに、壊れたデータの検知、ログ保存、二重計上の防止、Windowsでの定期実行まで扱います。

読了後には、次のことができるようになります。

- PythonでCSVを読み込む
- 商品、流入経路、日付などの項目別に集計する
- 欠損値や不正な金額を検知する
- 入力件数と集計結果の整合性を確認する
- 処理結果をCSVとログへ保存する
- Windowsのタスクスケジューラで定期実行する
- 集計結果を商品や集客導線の改善に活用する

ここでいう「自動化資産」とは、準備なしに収益が発生する仕組みではありません。最初にデータ形式、計算ルール、監視方法を設計し、その後の作業時間を減らしながら、収益につながる判断を継続できる仕組みを指します。

なお、この記事は一般的な情報提供を目的としています。売上、ポイント、アフィリエイト報酬などの成果を保証するものではなく、投資判断を勧める内容でもありません。

## PythonによるCSV自動集計の全体像

CSVとは、表形式のデータを文字列として保存したファイルです。たとえば、次のように1行目に列名、2行目以降にデータが並びます。

```csv
date,channel,amount
2026-07-01,blog,1200
2026-07-01,mail,800
2026-07-02,blog,1500
```

このCSVをPythonで処理するときは、作業を次の5段階に分けます。

```text
CSVを受け取る
  ↓
列名と各行を検証する
  ↓
金額や日付を変換する
  ↓
商品・経路・日付ごとに集計する
  ↓
結果CSVと実行ログを保存する
```

たとえば、ブログ、メール、SNSから発生した成果を毎日CSVへ追記している場合、Pythonを使えば流入経路ごとの金額を自動計算できます。

集計後のデータを次の処理へ渡せば、単なる時短を超えた自動化になります。

- 成果が伸びた流入経路を検出する
- 成約率が落ちた商品を通知する
- ポイント承認状況を週次レポートにする
- 売れ筋テーマから次の記事案を作る
- 販売実績に応じてCTAや掲載順を改善する

目指すのは、人間が数字を集め続ける状態ではありません。**集計済みの数字を確認し、次の判断を下す側へ移ること**です。

## 実際に行った10万行の再現テスト

一般論だけで終わらせないため、記事作成時に筆者のサイト運用リポジトリ上で、Python標準ライブラリを使った集計テストを実行しました。

テスト条件は次のとおりです。

- 実行日：2026年7月16日
- Python：3.11.9
- データ：プログラム内で生成した検証用CSV
- 行数：100,000行
- 分類：`blog`、`mail`、`sns`、`direct`の4種類
- 金額：1〜500を繰り返す合成データ
- 計測範囲：CSVの読み込み開始から集計完了まで
- ディスクへの結果ファイル保存時間：計測対象外
- 計測回数：1回

実行ログは次の結果になりました。

```text
python=3.11.9
rows=100000
elapsed_sec=0.250070
totals={'blog': 6225000, 'direct': 6300000,
        'mail': 6250000, 'sns': 6275000}
grand_total=25050000
```

これは実際の売上や報酬ではなく、**集計コードが10万行を処理し、期待した合計値を返すか確認するための合成データ**です。

また、0.250070秒という値は、今回のPCと実行条件における1回分の計測結果です。CPU、ストレージ、ウイルス対策ソフト、文字コード、列数などによって処理時間は変わります。複数回の平均や中央値も取っていないため、性能比較用のベンチマークではありません。

筆者のサイト運用では、商品導線を`generator/products.yaml`で管理しています。2026年7月16日のローカル確認時点では、価格設定のあるマニュアルが7件あり、設定価格は7,800円、9,800円、12,800円のいずれかでした。

このような商品設定とアクセス・販売CSVを組み合わせれば、商品別の閲覧数、クリック数、購入数、売上を自動集計する土台になります。ただし、商品設定が存在することと、実際に売上が発生したことは別です。販売実績を示す場合は、注文データや決済記録など、対応する一次データが必要です。

## ステップ・バイ・ステップで作るCSV自動集計

### 1. Pythonが使えるか確認する

PowerShellまたはコマンドプロンプトを開き、次を実行します。

```powershell
python --version
```

次のようにバージョンが表示されれば準備できています。

```text
Python 3.11.9
```

`python`が見つからない場合は、Python公式サイトからインストールします。Windowsでは、インストール画面に表示される「Add Python to PATH」を有効にしてください。

PATHとは、どのフォルダからでも`python`コマンドを呼び出せるようにする設定です。

今回の基本パターンでは、Pythonに最初から含まれる`csv`モジュールを使います。外部ライブラリのインストールは不要です。

### 2. 作業フォルダを用意する

次の構成でフォルダとファイルを用意します。

```text
csv-report/
├─ aggregate_sales.py
├─ input/
│  └─ sales.csv
├─ output/
└─ logs/
```

PowerShellから作成する場合は、次を実行します。

```powershell
mkdir csv-report
cd csv-report
mkdir input, output, logs
```

### 3. 入力CSVを用意する

`input`フォルダに、`sales.csv`という名前で次のデータを保存します。

```csv
date,channel,product,amount
2026-07-01,blog,manual_a,9800
2026-07-01,mail,manual_b,7800
2026-07-02,blog,manual_a,9800
2026-07-02,sns,manual_c,12800
2026-07-03,mail,manual_a,9800
```

各列の意味は次のとおりです。

| 列名 | 意味 | 具体例 |
|---|---|---|
| `date` | 成果が発生した日 | `2026-07-01` |
| `channel` | 流入経路 | `blog`、`mail` |
| `product` | 商品識別子 | `manual_a` |
| `amount` | 金額 | `9800` |

列名は途中で変えないようにします。`amount`と`price`が混在すると、コードが必要な列を見つけられません。

実際の売上データを使う場合は、氏名、メールアドレス、住所、カード情報など、集計に不要な個人情報をコピーしないでください。元データの利用目的や保存期間も確認しましょう。

### 4. 基本の集計コードを書く

`aggregate_sales.py`を作り、次のコードを記述します。

```python
import csv
from collections import defaultdict
from pathlib import Path

base_dir = Path(__file__).resolve().parent
input_path = base_dir / "input" / "sales.csv"
output_path = base_dir / "output" / "channel_summary.csv"

totals = defaultdict(int)

with input_path.open(
    "r",
    encoding="utf-8-sig",
    newline="",
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        channel = row["channel"].strip()
        amount = int(row["amount"])
        totals[channel] += amount

output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open(
    "w",
    encoding="utf-8-sig",
    newline="",
) as file:
    writer = csv.writer(file)
    writer.writerow(["channel", "total_amount"])

    for channel, total in sorted(totals.items()):
        writer.writerow([channel, total])

print(f"集計完了: {output_path}")
```

`defaultdict(int)`は、まだ登録されていない流入経路を自動的に0から始める辞書です。たとえば`blog`を初めて読み込んだときも、事前登録なしで金額を加算できます。

`utf-8-sig`は、UTF-8のBOM付きCSVを読み書きする指定です。Excelで日本語CSVを扱う際の文字化けを減らせる場合があります。

`Path(__file__).resolve().parent`を基準にしているため、PowerShellで別のフォルダを開いている場合でも、スクリプト自身が置かれた場所を基準に入力ファイルを探します。

### 5. コードを実行する

コードと同じフォルダで、次を実行します。

```powershell
python aggregate_sales.py
```

成功すると、次のようなメッセージが表示されます。

```text
集計完了: C:\automation\csv-report\output\channel_summary.csv
```

出力ファイルの内容は次のとおりです。

```csv
channel,total_amount
blog,19600
mail,17600
sns,12800
```

`blog`の19,600円は、9,800円のデータが2行あるためです。これは入力例に基づく計算結果であり、実際の収益を示すものではありません。

### 6. 商品別・流入経路別に集計する

収益導線を改善するには、流入経路だけでなく、どの商品が選ばれたかも組み合わせて見る必要があります。

集計キーを次のように変更します。

```python
key = (
    row["channel"].strip(),
    row["product"].strip(),
)
totals[key] += int(row["amount"])
```

出力部分は次の形にします。

```python
writer.writerow(["channel", "product", "total_amount"])

for (channel, product), total in sorted(totals.items()):
    writer.writerow([channel, product, total])
```

この集計により、「ブログ経由では商品A、メール経由では商品Bが多く選ばれている」といった傾向を確認できます。

ただし、売上金額だけで導線の良し悪しは判断できません。ページの訪問数が分かるなら、購入件数や売上と組み合わせてCVRも確認します。

```text
商品別CVR ＝ 購入件数 ÷ 商品ページ訪問数
```

![CSVの入力から商品別・流入経路別レポートを作る図解](https://image.pollinations.ai/prompt/csv%20input%20python%20validation%20grouping%20revenue%20report%20flowchart%20japanese%20labels%20style?width=800&height=400&nologo=true)

### 7. 壊れた行を検知する

実運用では、金額が空欄だったり、数字の代わりに文字が入ったりします。エラーを無視すると、収益レポートの数字を信用できなくなります。

まず、必要な列が存在するか確認します。

```python
required_columns = {"date", "channel", "product", "amount"}

if not reader.fieldnames:
    raise ValueError("CSVに見出し行がありません")

actual_columns = {
    column.strip()
    for column in reader.fieldnames
    if column is not None
}

missing_columns = required_columns - actual_columns

if missing_columns:
    raise ValueError(
        f"必要な列がありません: {sorted(missing_columns)}"
    )
```

各行の値も確認します。

```python
for line_number, row in enumerate(reader, start=2):
    try:
        channel = row["channel"].strip()
        product = row["product"].strip()
        amount = int(row["amount"])
    except (AttributeError, TypeError, ValueError) as error:
        print(f"{line_number}行目を処理できません: {error}")
        continue

    if not channel or not product:
        print(f"{line_number}行目は分類項目が空です")
        continue

    totals[(channel, product)] += amount
```

`start=2`としているのは、CSVの1行目が見出しだからです。エラーを「何となく失敗した」で終わらせず、該当する行番号まで残せます。

金額に小数が含まれる場合は、`float`ではなく`Decimal`の使用を検討してください。`Decimal`は、二進浮動小数点数に由来する丸め誤差を避けたい金額計算に適しています。

```python
from decimal import Decimal, InvalidOperation

try:
    amount = Decimal(row["amount"])
except (InvalidOperation, TypeError):
    print(f"{line_number}行目の金額が不正です")
    continue
```

### 8. 実行ログを保存する

完全自動化では、成功時よりも失敗時の設計が重要です。画面を見ていない時間に処理が停止しても、原因を追跡できるようにします。

最低限、次の項目を記録してください。

- 実行日時
- 入力ファイルの絶対パス
- 読み込んだ行数
- 正常行数
- エラー行数
- 集計グループ数
- 入力総額
- 出力総額
- 出力先
- エラー内容

筆者の既存運用ログには、`HEAD.lock`や`The command line is too long`といった失敗記録も残っていました。成功件数だけでなく例外名とエラーメッセージを保存すると、実行環境の問題なのか、CSVの問題なのかを次回の調査で切り分けやすくなります。

## 検証とログを含む実運用版コード

ここまでの処理を一つにまとめたコードが次の実運用版です。

```python
import csv
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_PATH = BASE_DIR / "input" / "sales.csv"
OUTPUT_PATH = BASE_DIR / "output" / "channel_product_summary.csv"
TEMP_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".tmp")
LOG_PATH = BASE_DIR / "logs" / "aggregate_sales.log"

REQUIRED_COLUMNS = {"date", "channel", "product", "amount"}


def configure_logging():
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        encoding="utf-8",
        format="%(asctime)s %(levelname)s %(message)s",
    )


def parse_amount(raw_amount):
    if raw_amount is None:
        raise ValueError("金額がありません")

    normalized = (
        raw_amount
        .strip()
        .replace(",", "")
        .replace("円", "")
    )

    if not normalized:
        raise ValueError("金額が空です")

    amount = int(normalized)

    if amount < 0:
        raise ValueError("金額が負数です")

    return amount


def aggregate_csv(input_path):
    totals = defaultdict(int)
    input_rows = 0
    processed_rows = 0
    error_rows = 0
    input_total = 0

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("CSVに見出し行がありません")

        actual_columns = {
            column.strip()
            for column in reader.fieldnames
            if column is not None
        }

        missing_columns = REQUIRED_COLUMNS - actual_columns

        if missing_columns:
            raise ValueError(
                f"必要な列がありません: {sorted(missing_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            input_rows += 1

            try:
                channel = row["channel"].strip()
                product = row["product"].strip()
                amount = parse_amount(row["amount"])

                if not channel:
                    raise ValueError("channelが空です")

                if not product:
                    raise ValueError("productが空です")

            except (AttributeError, TypeError, ValueError) as error:
                error_rows += 1
                logging.warning(
                    "不正な行 line=%d error=%s",
                    line_number,
                    error,
                )
                continue

            totals[(channel, product)] += amount
            input_total += amount
            processed_rows += 1

    return {
        "totals": totals,
        "input_rows": input_rows,
        "processed_rows": processed_rows,
        "error_rows": error_rows,
        "input_total": input_total,
    }


def write_summary(totals, output_path, temp_output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with temp_output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            ["channel", "product", "total_amount"]
        )

        for (channel, product), total in sorted(totals.items()):
            writer.writerow([channel, product, total])

        file.flush()
        os.fsync(file.fileno())

    temp_output_path.replace(output_path)


def main():
    configure_logging()
    started_at = datetime.now()

    logging.info(
        "集計開始 input=%s output=%s",
        INPUT_PATH,
        OUTPUT_PATH,
    )

    try:
        result = aggregate_csv(INPUT_PATH)

        output_total = sum(result["totals"].values())

        if result["input_rows"] != (
            result["processed_rows"] + result["error_rows"]
        ):
            raise RuntimeError("行数の整合性チェックに失敗しました")

        if result["input_total"] != output_total:
            raise RuntimeError("金額の整合性チェックに失敗しました")

        write_summary(
            result["totals"],
            OUTPUT_PATH,
            TEMP_OUTPUT_PATH,
        )

        elapsed_seconds = (
            datetime.now() - started_at
        ).total_seconds()

        logging.info(
            "集計完了 input_rows=%d processed_rows=%d "
            "error_rows=%d groups=%d input_total=%d "
            "output_total=%d elapsed_sec=%.3f output=%s",
            result["input_rows"],
            result["processed_rows"],
            result["error_rows"],
            len(result["totals"]),
            result["input_total"],
            output_total,
            elapsed_seconds,
            OUTPUT_PATH,
        )

        print(
            "集計完了: "
            f"正常={result['processed_rows']}件 "
            f"エラー={result['error_rows']}件 "
            f"出力={OUTPUT_PATH}"
        )

    except Exception:
        logging.exception("集計失敗")
        print(
            f"集計に失敗しました。ログを確認してください: {LOG_PATH}",
            file=sys.stderr,
        )
        raise


if __name__ == "__main__":
    main()
```

このコードでは、次の事故を防ぐ設計を加えています。

- スクリプトの場所を基準にファイルを探す
- 必須列がなければ処理を中止する
- 不正な行の番号と理由をログへ残す
- 正常行数とエラー行数を数える
- 入力総額と出力総額を照合する
- 一時ファイルへの書き込み完了後に正式名へ置き換える
- 予期しない例外のスタックトレースをログへ残す
- エラー発生時に終了コードを0以外にする

今回のコードは、不正な行をログへ記録して処理を続ける方針です。ただし、会計や請求など、1行でも欠損すると困る用途では、エラー行を検出した時点で処理全体を失敗させる方が安全です。

## Windowsで定期実行する

Windowsでは「タスクスケジューラ」を使い、毎朝や毎週月曜日など、指定した時刻にPythonを起動できます。

設定例は次のとおりです。

```text
プログラム:
C:\Python311\python.exe

引数の追加:
C:\automation\csv-report\aggregate_sales.py

開始:
C:\automation\csv-report
```

Python本体の場所は、次のコマンドで確認できます。

```powershell
where.exe python
```

仮想環境を使っている場合は、システム全体の`python.exe`ではなく、仮想環境内のPythonを指定します。

```text
C:\automation\csv-report\.venv\Scripts\python.exe
```

タスクスケジューラでは、次の点も確認してください。

- 「開始」にはスクリプトのあるフォルダを指定する
- タスクの実行履歴を有効にする
- 失敗時に再実行する設定を入れる
- 実行ユーザーが入力・出力フォルダへアクセスできるか確認する
- PCがスリープ中の場合の動作を決める
- ネットワークドライブを使う場合は、実行ユーザーから見えるか確認する

定期実行を設定した直後から完全放置してはいけません。最低でも数回は、入力CSV、出力CSV、ログの3点を人間が照合してください。

## 専門家目線のチェックポイント

### 入力ファイルを上書きしない

元のCSVへ集計結果を直接書き込むと、途中停止した際に入力データまで壊れる可能性があります。

次のように役割を分けます。

```text
input/   元データ
output/  集計結果
logs/    実行記録
```

出力中のファイルには一時名を使い、書き込み完了後に正式名へ置き換える方法が有効です。半端な状態のCSVを別のシステムが読み込む事故を減らせます。

ただし、置換の安全性はOS、ファイルシステム、同期ソフト、置換元と置換先の保存場所によって異なります。ネットワークドライブやクラウド同期フォルダでは、ローカルディスクと同じ動作を前提にしないでください。

### 件数と合計値を照合する

処理が例外なく終わっても、集計結果が正しいとは限りません。少なくとも次の式を毎回確認します。

```text
入力総額 ＝ 全グループの集計額合計
入力行数 ＝ 正常行数 ＋ エラー行数
```

重複排除を行う場合は、次のように除外件数も記録します。

```text
入力行数 ＝ 正常行数 ＋ エラー行数 ＋ 重複除外行数
```

### 重複を収益として二重計上しない

同じ成果CSVを2回取り込むと、売上が2倍に見えることがあります。注文ID、成果ID、取引IDなどの一意な項目があるなら、処理済みIDを記録してください。

日付と金額だけで重複を判定すると、同日に同額の商品が2件売れた正当なデータまで削除する恐れがあります。

実務では、次のような複合キーも検討します。

```text
提供元 ＋ 取引ID
```

取引IDが提供されない場合は、重複判定の限界をログや仕様書に明記してください。

### 文字コードと区切り文字を確認する

日本語CSVでは、UTF-8、UTF-8 with BOM、Shift_JIS互換のCP932などが混在します。また、カンマではなくタブやセミコロンで区切られたファイルもあります。

ファイルを開けない場合は、コードを何度も書き換える前に、提供元の出力仕様を確認します。

CP932と確認できている場合は、次のように指定できます。

```python
with input_path.open(
    "r",
    encoding="cp932",
    newline="",
) as file:
    reader = csv.DictReader(file)
```

文字コードの自動判定は常に正しいとは限りません。安定運用では、提供元ごとに文字コードと区切り文字を設定として固定する方が安全です。

### 収益額と承認額を分ける

アフィリエイトやポイント案件では、「発生」と「承認」が同じではありません。

```text
発生額
承認待ち額
承認額
否認額
```

これらを別の列やステータスとして管理すると、見かけの成果に引っ張られず、実際に確定した結果を追跡できます。

さらに、発生日と承認日も分けてください。7月に発生した成果が8月に承認される場合、どちらの日付を基準に集計するかで月次レポートの数字が変わります。

### 集計ルールを文章で残す

コードだけでは、なぜその計算をしているのか分からなくなることがあります。最低限、次のルールをREADMEや運用メモに残してください。

- 金額は税込みか税抜きか
- 返金をどのように扱うか
- 負数を許可するか
- 発生日と承認日のどちらを使うか
- キャンセルを除外するか
- 通貨が複数ある場合にどう換算するか
- 重複を何によって判定するか
- エラー行があった場合に続行するか停止するか

この仕様がなければ、コードが正しく動いても、事業上は誤った数字を出す可能性があります。

## 画像で説明すべき箇所と視覚的証拠

記事や運用マニュアルへ画像を追加するなら、効果が高いのは次の3点です。

1. **処理フロー図**  
   `CSV受信 → 検証 → 集計 → 出力 → 通知`の流れを矢印で示します。

2. **入力CSVと出力CSVの比較画面**  
   左側に明細、右側に集計結果を置き、どの数字が合算されたか色で対応させます。

3. **実行ログのスクリーンショット**  
   実行日時、正常行数、エラー行数、入力総額、出力総額、出力パスが見える状態を撮影します。個人情報や認証情報は必ず隠してください。

![Python自動集計の監視ダッシュボード案](https://image.pollinations.ai/prompt/python%20csv%20automation%20monitoring%20dashboard%20processed%20rows%20errors%20revenue%20kpi%20modern%20ui?width=800&height=400&nologo=true)

概念図は仕組みの理解には役立ちますが、処理が実際に動いた証拠にはなりません。公開記事では、可能であれば次の情報も示すと、読者が再現性を判断しやすくなります。

- 実行したコードのバージョン
- Pythonのバージョン
- 入力行数
- 期待値と実測値
- 実行日時
- 匿名化した実行ログ
- 集計前後のスクリーンショット
- テストの回数と計測範囲
- 使用したデータが実データか合成データか

公開前には、ユーザー名、ローカルパス、メールアドレス、注文ID、APIキー、Cookieなどが画像やログに写っていないか確認してください。

## よくある失敗と対策

### `FileNotFoundError`が出る

主な原因は、Pythonが基準にしているフォルダとCSVの保存場所が一致していないことです。

`Path(__file__).resolve().parent`を基準にすると、実行場所によるずれを減らせます。

```python
base_dir = Path(__file__).resolve().parent
input_path = base_dir / "input" / "sales.csv"
```

調査するときは、実際に参照している絶対パスを表示します。

```python
print(input_path.resolve())
print(input_path.exists())
```

### 日本語が文字化けする

Excel由来のCSVなら、まず`utf-8-sig`を試します。Shift_JIS互換形式と確認できた場合は`cp932`を指定します。

文字コードを推測だけで決めず、CSVの提供元や保存設定を確認してください。

### `invalid literal for int()`が出る

金額にカンマ、通貨記号、空白などが含まれている可能性があります。

```python
raw_amount = (
    row["amount"]
    .strip()
    .replace(",", "")
    .replace("円", "")
)
amount = int(raw_amount)
```

ただし、`9,800円`のような書式を許可するのか、入力段階で数字だけに統一するのかを事前に決めます。

`¥9,800`、`9 800`、`9,800.00`なども入力される可能性があるなら、許可する形式を明文化し、テストデータを用意してください。

### CSVの列名が毎月変わる

提供元の仕様変更が原因です。列を位置番号で読む方法は、列の追加や並べ替えにも弱くなります。

必須列を最初に検査し、見つからなければ処理を止めて通知する設計が安全です。

列名の変更を吸収する必要がある場合は、対応表を設定として持たせます。

```python
column_aliases = {
    "売上金額": "amount",
    "報酬額": "amount",
    "流入元": "channel",
}
```

ただし、意味の異なる列を名前だけで同一視しないよう注意してください。

### 自動実行したのにファイルが更新されない

タスクスケジューラでは、手動実行時と作業フォルダ、ユーザー、環境変数が異なることがあります。

次を確認してください。

- Python本体を絶対パスで指定しているか
- スクリプトを絶対パスで指定しているか
- 「開始」フォルダを指定しているか
- 実行ユーザーに読み書き権限があるか
- ログに入力・出力の絶対パスを残しているか
- 仮想環境のPythonを指定しているか
- ネットワークドライブが実行ユーザーから見えるか

### CSVを開いたまま実行すると失敗する

Excelで出力CSVを開いていると、Windowsではファイルの置換に失敗する場合があります。

自動実行用の出力ファイルは開きっぱなしにしないか、実行日時を含む別名で保存します。

```python
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = (
    BASE_DIR
    / "output"
    / f"channel_summary_{timestamp}.csv"
)
```

履歴ファイルを増やす場合は、保存期間や削除ルールも決めてください。

### 自動集計すれば収益も自動で増えると思ってしまう

集計は判断材料を作る仕組みであり、売上を直接発生させる装置ではありません。商品需要、検索順位、読者との適合、価格、サービス規約などの影響を受けます。

集計後に、次のような改善へつなげて初めて収益化に寄与します。

- 成果の低い導線を停止する
- 反応の高いテーマを追加検証する
- クリック率が高く、購入率が低い商品の説明を見直す
- 発生件数は多いが承認率が低い案件を再評価する
- 手作業の削減時間と保守時間を比較する

## 成果を測るKPI

KPIとは、仕組みを改善するために継続観測する指標です。

| KPI | 計算・記録方法 | 改善判断 |
|---|---|---|
| 正常処理率 | 正常行数 ÷ 入力行数 | 低下したらCSV仕様を確認 |
| エラー行数 | 処理できなかった行の件数 | 発生理由を分類して減らす |
| 実行成功率 | 成功回数 ÷ 実行予定回数 | 定期実行の安定性を確認 |
| 集計時間 | 開始時刻から完了時刻 | データ増加による遅延を確認 |
| 手作業削減時間 | 従来時間 − 自動化後の確認時間 | 開発・保守コストと比較 |
| 承認率 | 承認件数 ÷ 発生件数 | 案件や導線の品質を確認 |
| 商品別CVR | 購入件数 ÷ 商品ページ訪問数 | CTAと商品適合を改善 |
| `/products/`クリック率 | 商品一覧クリック数 ÷ 記事閲覧数 | 記事から商品への接続を評価 |

目標値は他人の数字をそのまま採用せず、最初の1〜2週間を基準期間として実測します。

たとえば、手集計が1回20分、自動化後の確認が5分なら、1回あたりの削減時間は15分です。週5回なら75分ですが、これは20分と5分を実際に計測した場合に限って使える数字です。

保守に毎週60分かかるなら、差し引きの削減時間は15分です。さらに、初期開発に6時間かかった場合は、その回収期間も考慮します。

```text
初期開発時間 ÷ 週あたりの純削減時間
＝ 6時間 ÷ 0.25時間
＝ 24週間
```

このように、自動化の価値は「動いたか」だけでなく、開発・確認・保守を含む総時間で評価します。

## 本番運用前のチェックリスト

定期実行を始める前に、次を確認してください。

- [ ] 入力CSVのバックアップがある
- [ ] 必須列を検査している
- [ ] 空欄、文字列、負数の扱いを決めている
- [ ] 正常行数とエラー行数を記録している
- [ ] 入力総額と出力総額を照合している
- [ ] 重複判定に一意なIDを使っている
- [ ] 元のCSVを上書きしていない
- [ ] エラーの詳細をログへ保存している
- [ ] タスク失敗時の確認方法を決めている
- [ ] 実データを使った少量テストを行った
- [ ] 個人情報や認証情報を不要に保存していない
- [ ] サービスの利用規約を確認した
- [ ] 集計ルールを文章で残した

最初から完全無人化を目指す必要はありません。最初の数回は「自動集計した結果を人間が照合する半自動運用」にし、数字が一致することを確認してから監視の頻度を下げます。

## この方法が使えないケースと限界

PythonによるCSV自動集計が常に最適とは限りません。

- 一度しか集計しない小さなCSV
- 毎回、列と計算ルールが大きく変わるデータ
- 数字では判定できない文章中心の資料
- CSVの取得に人間による本人確認が必要なサービス
- 自動アクセスやデータ取得が規約で禁止されているサービス
- リアルタイム更新が必要で、CSVでは間に合わないシステム
- 厳格な監査証跡や権限管理が必要な会計処理
- 複数人が同時に更新するデータ
- 数百万〜数千万行を継続的に処理する用途

数十行を一度だけ合計するなら、Excelのピボットテーブルの方が早い場合があります。複雑な結合や大量データ分析には、`pandas`、DuckDB、SQLiteなどが適することもあります。

また、ポイント獲得操作、広告クリック、申込、アンケート回答などをBot化すると、サービス規約違反や成果否認につながる恐れがあります。

安全に自動化しやすいのは、**正当に取得したCSVの整理、比較、集計、通知、レポート化**です。

この記事のサンプルコードにも、次の限界があります。

- 日付形式の厳密な検証はしていない
- 外貨換算には対応していない
- 返金やキャンセルの業務ルールは含めていない
- 処理済みIDを永続保存する重複防止は実装していない
- エラー通知メールやチャット通知は実装していない
- 複数プロセスからの同時実行は想定していない
- ログの自動削除やローテーションは実装していない

本番導入時は、対象業務に合わせてこれらを追加してください。

## 類似記事との差別化ポイント

一般的なPython・CSV解説は、`csv.reader()`の使い方や合計値の表示で終わることがあります。

この記事では、次の範囲まで扱いました。

- 10万行の合成CSVを使ったローカル環境での再現テスト
- 実測値、計算例、設定値、実売上を区別した記載
- 列不足、文字コード、重複、不正値への対策
- 入力件数と出力合計の整合性チェック
- ログと定期実行を含む無人運用
- 一時ファイルを使った出力途中の事故対策
- 発生額と承認額を分ける収益管理
- 集計結果を商品、記事、CTAの改善へ戻す方法
- 自動化が向かないケースと規約上の限界
- 開発時間と保守時間を含めた費用対効果の計算

CSV集計を単発のプログラミング練習ではなく、繰り返し利用できる運用資産として設計している点が違いです。

## まとめ：今日取るべきアクション

PythonによるCSV自動集計は、次の順序で作れます。

1. 手作業で集計しているCSVを1つ選ぶ
2. 列名と計算ルールを固定する
3. `csv.DictReader`で読み込む
4. 必須列と各行の値を検証する
5. `defaultdict`で項目別に合計する
6. 入力件数、エラー件数、合計値を照合する
7. 結果CSVと実行ログを保存する
8. 数回の手動照合を行う
9. タスクスケジューラで定期実行する
10. 集計結果を収益導線の改善へ戻す

読了後すぐに行うなら、**過去7日分の売上、ポイント、広告、作業記録のいずれかをCSVへまとめ、流入経路別の合計を出してください。**

最初は5行でも構いません。次の4項目をメモしておけば、自動化の効果を後から判断できます。

```text
手作業にかかった時間:
自動処理にかかった時間:
結果確認にかかった時間:
手作業と自動処理の合計値は一致したか:
```

最初の成功条件は、派手なダッシュボードを作ることではありません。

**同じ入力から、毎回同じ正しい結果を出し、失敗したときに原因を追跡できること**です。

## 本気で自動化・収益導線を構築したい方向けの実践マニュアル

CSV集計が完成すると、数字を集める作業から離れやすくなります。しかし、集計結果を眺めるだけでは、自動化資産は収益導線まで到達しません。

次に必要になるのは、データ収集、条件判定、記事生成、通知、商品販売、KPI改善を一つの流れとして接続する設計です。

Hiroの実践マニュアルでは、AIブログ、アフィリエイト、デジタル商品、Pinterest、VPS運用など、目的別の自動化フローを具体的な作業単位に分けて解説しています。

「毎回CSVを開く人」から、**自分が席を離れている間にもデータが集まり、改善候補が届き、商品導線が働く仕組みを所有する人**へ移りたい方は、次のページから自分に合う実践ルートを選んでください。

👉 **[本気で自動化・収益導線を構築するための実践マニュアルを見る](/products/)**
