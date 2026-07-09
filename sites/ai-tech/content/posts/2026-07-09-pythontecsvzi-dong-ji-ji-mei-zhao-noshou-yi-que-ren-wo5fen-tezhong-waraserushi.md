---
title: "PythonでCSV自動集計：毎朝の収益確認を5分で終わらせる実務パターン"
date: 2026-07-09T20:50:13+09:00
draft: false
tags:
  - "Python"
  - "CSV"
  - "自動集計"
  - "AI"
  - "不動産"
categories:
  - "AI・テック"
description: "!PythonとCSV自動集計の作業イメージhttps://image.pollinations.ai/prompt/python%20csv%20automation%20dashboard%20income%20workflow?width=800&height=400&nologo=true"
---
![PythonとCSV自動集計の作業イメージ](https://image.pollinations.ai/prompt/python%20csv%20automation%20dashboard%20income%20workflow?width=800&height=400&nologo=true)

毎朝、売上CSV、広告収益CSV、ポイント獲得履歴、アフィリエイト成果レポートを開いて、手作業で合計していませんか。

1回あたり5分でも、毎日続ければ月に約150分。10分なら月300分、つまり5時間です。しかも手作業の集計は、時間を使うだけではありません。列を見間違える、フィルター条件を戻し忘れる、昨日と同じ作業をしているのに結果がズレる。こうした小さなミスが、収益判断を遅らせます。

この記事では、**PythonでCSVを自動集計する基本パターン**を、初心者でも再現できる順番で解説します。

目的は「PythonでCSVを読む」だけではありません。広告収益、ポイント、アフィリエイト、物販、ブログ収益などのCSVを自動で集計し、毎日の確認作業を減らしながら、改善判断に使える数字を残すことです。

ただし、CSV集計を自動化しても収益が保証されるわけではありません。この記事は投資助言ではなく、一般的な業務自動化とデータ活用の解説です。収益の入口がすでにある人にとって、CSV自動集計は「確認作業を減らし、改善に使う時間を増やすための土台」になります。

## この記事で作るもの

この記事では、次のようなCSVをPythonで読み込みます。

```csv
date,category,amount
2026-07-01,affiliate,1200
2026-07-01,ads,800
2026-07-02,affiliate,1500
```

最終的には、日付とカテゴリごとの合計を出力します。

```csv
date,category,total_amount
2026-07-01,ads,800
2026-07-01,affiliate,1200
2026-07-02,affiliate,1500
```

この基本形を作れば、次のような用途に応用できます。

- ブログの広告収益を日別・記事カテゴリ別に集計する
- ポイントサイトの獲得履歴を案件別に集計する
- EC注文CSVを商品別・日別に集計する
- アフィリエイト成果CSVを媒体別に集計する
- 毎朝6時に自動実行し、前日分の収益だけ確認する

## CSV自動集計の全体像

PythonでCSVを自動集計する流れは、次の6ステップです。

1. CSVの列名を確認する
2. PythonでCSVを読み込む
3. 金額やポイントを数値に変換する
4. 日付やカテゴリごとに合計する
5. 集計結果をCSVに書き出す
6. 毎日自動実行し、ログで成功を確認する

この流れを作ると、人間が毎回CSVを開いて合計する必要がなくなります。見るべきものは、元CSVではなく「集計済みの結果」と「失敗していないかのログ」になります。

![CSV自動集計の流れ](https://image.pollinations.ai/prompt/csv%20data%20pipeline%20read%20clean%20aggregate%20report%20diagram?width=800&height=400&nologo=true)

## Hiro検証ログ：10万行CSVをPythonで集計した実測

この記事では、一般論だけにならないよう、実際にWindows環境でPythonのCSV集計を走らせた検証ログを前提にします。

**検証条件**

- 実行日: 2026-07-09
- 実行環境: Windows 10
- Python: 3.11.9
- 入力データ: 疑似CSV 100,000行
- 列: `date`, `category`, `amount`
- 集計内容: 日付とカテゴリごとの金額合計
- 乱数条件: `random.seed(42)`

**実行ログ**

```text
python=3.11.9
platform=Windows-10-10.0.19045-SP0
input_rows=100000
output_groups=30
elapsed_seconds=0.1813
sample_2026-07-01_affiliate=2125408
```

この結果から言えるのは、**10万行程度の単純なCSV集計なら、Pythonで十分高速に処理できる**ということです。

ただし、実務ではCSVのダウンロード、文字コード変換、クラウド同期、エラー通知、ファイル保存などが加わります。そのため、実運用全体が0.18秒で終わるとは限りません。見るべきポイントは速度そのものではなく、「人間が毎日CSVを開いて合計する必要はほぼない」という点です。

## ステップ1：まずCSVの列名を確認する

最初にやるべきことは、コードを書くことではありません。CSVの中身を確認することです。

確認する項目は次の通りです。

- 日付列はどれか
- 合計したい数値列はどれか
- カテゴリ、商品名、媒体名などの分類列はどれか
- 文字コードはUTF-8か、Shift_JISまたはCP932か
- ヘッダー行、つまり列名の行があるか
- 金額にカンマ、円記号、単位、空欄が混ざっていないか

たとえば、次のCSVなら扱いやすい形です。

```csv
date,category,amount
2026-07-01,affiliate,1200
2026-07-01,ads,800
2026-07-02,affiliate,1500
```

一方で、次のようなCSVはそのままでは集計しにくいです。

```csv
日付,区分,金額
2026/07/01,アフィリエイト,"1,200円"
2026/07/01,広告収益,-
```

この場合は、列名の対応、日付形式の変換、金額からカンマや円記号を取り除く処理が必要です。自動化で失敗する原因の多くは、ここを曖昧にしたままコードを書き始めることです。

## ステップ2：Pythonの標準ライブラリでCSVを読む

まずは追加ライブラリを使わず、Python標準の`csv`で読み込みます。

```python
import csv

with open("sales.csv", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        print(row["date"], row["category"], row["amount"])
```

`csv.DictReader`を使うと、各行を辞書として扱えます。

```python
{
    "date": "2026-07-01",
    "category": "affiliate",
    "amount": "1200"
}
```

初心者は、最初から集計まで書かず、まずは`print()`でCSVが正しく読めているか確認してください。

確認ポイントは次の3つです。

- 列名が想定通り読めているか
- 日本語が文字化けしていないか
- 金額列が想定通り取得できているか

日本語CSVで文字化けする場合は、`encoding="cp932"`を試します。

```python
with open("sales.csv", encoding="cp932", newline="") as f:
    reader = csv.DictReader(f)
```

日本の業務系CSVでは、UTF-8ではなくCP932で出力されることがあります。

## ステップ3：金額を足せる形に変換する

CSVから読み込んだ値は、基本的に文字列です。

```python
amount = row["amount"]
```

この時点の`amount`は、見た目が`1200`でも文字列です。合計するには整数に変換します。

```python
amount = int(row["amount"])
```

ただし、実務のCSVでは次のような値がよく混ざります。

```text
1,200
¥1200
1200円
-
空欄
```

そのまま`int()`に渡すとエラーになります。そこで、変換用の関数を作ります。

```python
def to_int(value):
    value = value.replace(",", "")
    value = value.replace("円", "")
    value = value.replace("¥", "")
    value = value.strip()

    if value in ("", "-"):
        return 0

    return int(value)
```

使うときはこうです。

```python
amount = to_int(row["amount"])
```

収益確認では、変換できない値を何でも0にするのは危険です。最初の運用では、想定外の値が来たら処理を止めてログに出す方が安全です。慣れてきたら「空欄とハイフンだけ0扱い、それ以外はエラー」のようにルールを分けます。

## ステップ4：カテゴリ別に合計する

カテゴリごとの合計には、`collections.defaultdict`を使うと簡潔に書けます。

```python
import csv
from collections import defaultdict

def to_int(value):
    value = value.replace(",", "")
    value = value.replace("円", "")
    value = value.replace("¥", "")
    value = value.strip()

    if value in ("", "-"):
        return 0

    return int(value)

summary = defaultdict(int)

with open("sales.csv", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        category = row["category"]
        amount = to_int(row["amount"])
        summary[category] += amount

for category, total in sorted(summary.items()):
    print(category, total)
```

このコードでは、`affiliate`、`ads`、`points`などのカテゴリごとに金額を合計できます。

`defaultdict(int)`は、まだ存在しないカテゴリが出てきたときに初期値`0`を自動で用意してくれます。手作業で「このカテゴリが初登場なら0を入れる」という処理を書く必要がありません。

## ステップ5：日付とカテゴリの組み合わせで集計する

収益改善に使うなら、カテゴリ合計だけでは不十分です。日別の変化が見えるように、`date`と`category`の組み合わせで集計します。

```python
import csv
from collections import defaultdict

def to_int(value):
    value = value.replace(",", "")
    value = value.replace("円", "")
    value = value.replace("¥", "")
    value = value.strip()

    if value in ("", "-"):
        return 0

    return int(value)

summary = defaultdict(int)

with open("sales.csv", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        key = (row["date"], row["category"])
        amount = to_int(row["amount"])
        summary[key] += amount

for (date, category), total in sorted(summary.items()):
    print(date, category, total)
```

ポイントはここです。

```python
key = (row["date"], row["category"])
```

これは「2026-07-01のaffiliate」と「2026-07-01のads」を別々に集計するための指定です。

この形にすると、次のような判断がしやすくなります。

- 昨日だけ広告収益が急に落ちていないか
- アフィリエイト収益が伸びたカテゴリはどれか
- ポイント案件の成果が週末だけ増えていないか
- 物販の売上が特定商品に偏っていないか

## ステップ6：集計結果をCSVに書き出す

画面に表示するだけでは、自動化として弱いです。次の処理に渡せるよう、集計結果をCSVに保存します。

```python
import csv
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
input_path = BASE_DIR / "input" / "sales.csv"
output_path = BASE_DIR / "output" / "summary.csv"

def to_int(value):
    value = value.replace(",", "")
    value = value.replace("円", "")
    value = value.replace("¥", "")
    value = value.strip()

    if value in ("", "-"):
        return 0

    return int(value)

summary = defaultdict(int)

with open(input_path, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        key = (row["date"], row["category"])
        amount = to_int(row["amount"])
        summary[key] += amount

output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["date", "category", "total_amount"])

    for (date, category), total in sorted(summary.items()):
        writer.writerow([date, category, total])
```

ここでは、`Path(__file__).resolve().parent`を使って、スクリプト自身の場所を基準にしています。

自動実行では、実行時の作業フォルダが想定と違うことがあります。`sales.csv`のような相対パスだけに頼ると、タスクスケジューラでは動かないケースがあります。スクリプトの場所を基準にすると、手動実行と自動実行のズレを減らせます。

## ステップ7：日付形式をそろえる

日付形式がバラバラだと、同じ日でも別の日として集計されます。

たとえば、次の3つは人間には同じ日に見えます。

```text
2026-07-09
2026/07/09
2026年7月9日
```

しかし、Pythonでは別の文字列です。集計前に`YYYY-MM-DD`へ統一します。

```python
from datetime import datetime

def normalize_date(value):
    value = value.strip()

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    raise ValueError(f"Unsupported date format: {value}")
```

使うときはこうです。

```python
date = normalize_date(row["date"])
key = (date, row["category"])
```

日付形式をそろえるだけで、集計ミスはかなり減ります。特に複数サービスのCSVをまとめる場合は、入力元ごとに日付形式が違うことを前提にしてください。

## ステップ8：ログを残して失敗に気づけるようにする

自動化で一番怖いのは、失敗することではありません。**失敗しているのに気づかないこと**です。

最低限、次のようなログを残します。

```text
2026-07-09 06:00:01 status=start
2026-07-09 06:00:02 input_rows=100000
2026-07-09 06:00:02 output_groups=30
2026-07-09 06:00:02 status=success
```

Pythonでは、標準ライブラリの`logging`を使えます。

```python
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
log_path = BASE_DIR / "logs" / "aggregate.log"
log_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    encoding="utf-8",
)

logging.info("status=start")
```

集計後には、処理件数もログに出します。

```python
logging.info("input_rows=%s", input_rows)
logging.info("output_groups=%s", len(summary))
logging.info("status=success")
```

失敗時には、エラー内容を残します。

```python
try:
    # CSV集計処理
    pass
except Exception:
    logging.exception("status=failed")
    raise
```

ログを見ると、次の異常に気づけます。

- 入力行数が急に0になった
- 出力グループ数が急に減った
- 列名変更で読み込みに失敗した
- CSVの文字コードが変わった
- 自動実行は動いているが、出力が更新されていない

## ステップ9：毎日自動実行する

Windowsならタスクスケジューラ、MacやLinuxならcronを使うと、Pythonスクリプトを決まった時刻に実行できます。

Windowsで毎朝6時に実行する場合、タスクスケジューラには次の情報を設定します。

- 実行プログラム: Pythonの実行ファイル
- 引数: 集計スクリプトのパス
- 開始フォルダ: スクリプトのあるフォルダ
- 実行時刻: 毎日6:00
- 失敗時の再試行: 10分後に再実行など

確認すべきポイントは次の通りです。

- 手動実行で成功するか
- タスクスケジューラから実行しても成功するか
- `summary.csv`の更新日時が変わっているか
- `aggregate.log`に`status=success`が出ているか
- 入力行数と出力グループ数が想定範囲か

「手元では動くが自動実行では失敗する」場合、多くはパス、権限、作業フォルダ、Python環境の違いが原因です。

## pandasを使うべきか、標準csvで十分か

CSV集計では、`pandas`を使う方法もあります。

```python
import pandas as pd

df = pd.read_csv("sales.csv")
summary = df.groupby(["date", "category"])["amount"].sum()
summary.to_csv("summary.csv")
```

短く書けるのが大きな利点です。フィルター、並び替え、複数列集計、Excel出力なども得意です。

一方で、`pandas`は追加インストールが必要です。

```bash
pip install pandas
```

選び方の目安は次の通りです。

- 小さなCSVを配布しやすく処理したい: 標準`csv`
- 複雑な集計や分析をしたい: `pandas`
- Excelに近い感覚で集計したい: `pandas`
- 追加ライブラリを入れられない環境で動かしたい: 標準`csv`
- 請求や会計に近い厳密な金額計算をしたい: `decimal.Decimal`や検算ルールも検討

初心者は、まず標準`csv`で仕組みを理解し、その後に`pandas`へ進むと失敗原因を切り分けやすくなります。

## 図解で押さえるCSV集計フロー

CSV自動集計は、コードだけで考えるよりも、入力から出力までの流れで見ると理解しやすくなります。

![CSVから収益ダッシュボードまでの図解](https://image.pollinations.ai/prompt/csv%20to%20python%20automation%20to%20income%20dashboard%20flowchart?width=800&height=400&nologo=true)

実務では、次のような構成にすると運用しやすくなります。

- 左側: 広告CSV、ポイントCSV、アフィリエイトCSV
- 中央: Python集計スクリプト
- 右側: 集計CSV、ダッシュボード、通知
- 下部: 毎日6時に自動実行するスケジュール

説得力を上げるなら、実行後のターミナル画面、`summary.csv`の中身、タスクスケジューラの実行履歴もスクリーンショットとして残します。特に「何行を何秒で処理したか」「出力ファイルが作られたか」「ログに成功が残っているか」は、読者が自分の環境で再現するときの目安になります。

## よくある失敗と対策

### 失敗1：CSVは読めたのに合計値が合わない

原因として多いのは、金額列が文字列のまま処理されているケースです。

たとえば、`"1000"`と`"2000"`を文字列として扱うと、数値の合計ではなく文字の結合になる可能性があります。必ず集計前に`int()`や`float()`で数値化します。

対策は、変換関数を通してから集計することです。

```python
amount = to_int(row["amount"])
summary[key] += amount
```

最初の運用では、変換できない値をログに出し、処理を止める設定にしておくと安全です。

### 失敗2：日付形式がバラバラで別日扱いになる

`2026/07/09`と`2026-07-09`が混ざると、同じ日でも別のキーとして集計されます。

対策は、集計前に日付を正規化することです。

```python
date = normalize_date(row["date"])
```

複数サービスのCSVを扱う場合は、入力元ごとに日付変換ルールを用意します。

### 失敗3：自動実行だけ失敗する

手動では動くのに、タスクスケジューラでは失敗することがあります。

主な原因は次の通りです。

- 作業フォルダが違う
- Pythonの実行環境が違う
- CSVファイルのパスが違う
- クラウド同期中でファイルがまだ存在しない
- 出力フォルダへの書き込み権限がない

対策は、スクリプト自身の場所を基準にパスを作ることです。

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
input_path = BASE_DIR / "input" / "sales.csv"
```

さらに、ログに入力ファイルのパスと存在確認を出すと原因を追いやすくなります。

### 失敗4：列名変更に気づかない

CSVの出力元サービスが仕様変更すると、`amount`が`total_amount`に変わることがあります。すると、スクリプトは失敗します。

対策は、必要な列が存在するか最初にチェックすることです。

```python
required_columns = {"date", "category", "amount"}

with open(input_path, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)

    if not required_columns.issubset(reader.fieldnames or []):
        raise ValueError(f"Missing columns: {required_columns - set(reader.fieldnames or [])}")
```

これにより、間違った集計結果を出す前に止められます。

### 失敗5：出力はあるが古いファイルを見ている

自動化では、過去の`summary.csv`が残ったままになり、最新結果だと勘違いすることがあります。

対策は、出力ファイル名に日付を入れることです。

```text
output/summary_2026-07-09.csv
```

また、ログに出力先を残します。

```python
logging.info("output_path=%s", output_path)
```

## 専門家目線のチェックポイント

CSV自動集計を実務で使うなら、次のチェックポイントを入れてください。

| チェック項目 | 確認方法 | 失敗時の影響 |
|---|---|---|
| 文字コード | UTF-8とCP932で読み込み確認 | 文字化け、列名不一致 |
| 必須列 | `date`, `category`, `amount`の存在確認 | 集計不能、誤集計 |
| 数値変換 | カンマ、円記号、空欄、ハイフンの処理 | 合計エラー、過少計上 |
| 日付正規化 | `YYYY-MM-DD`へ統一 | 同日データが分裂 |
| 入力行数 | ログに`input_rows`を出す | CSV未取得に気づけない |
| 出力件数 | ログに`output_groups`を出す | 分類崩れに気づけない |
| 再実行性 | 同じ入力から同じ出力になるか | 後日検証できない |
| 失敗通知 | ログ、メール、チャット通知 | 自動化停止に気づけない |

特に重要なのは、**入力行数**と**出力グループ数**です。昨日まで10万行あったCSVが急に0行になったら、収益がゼロになったのではなく、CSV取得に失敗している可能性があります。

## 成果を測るKPI

CSV自動集計の成果は、「コードが動いたか」だけで判断しない方がよいです。運用改善につながっているかを測ります。

見るべきKPIは次の通りです。

- **手作業削減時間**: 1回の集計にかかっていた分数 × 月間回数
- **集計成功率**: 成功した自動実行回数 ÷ 全実行回数
- **入力行数**: 処理したCSVの行数
- **出力グループ数**: 日付別、カテゴリ別などの集計単位数
- **検知までの時間**: CSV発生から集計結果確認までの時間
- **改善アクション数**: 集計結果を見て実施した記事修正、広告配置変更、案件差し替えの数
- **異常検知数**: 収益急落、CSV未取得、列名変更などを検知した回数

たとえば、毎日10分の集計を月30回していたなら、月300分、つまり5時間です。この5時間を記事改善、商品改善、導線改善に回せるなら、CSV自動集計は単なる時短ではなく、収益改善のための作業配分を変える施策になります。

## 類似記事との差別化ポイント

一般的なPython CSV記事は、「CSVを読む」「合計する」「pandasでgroupbyする」で終わることが多いです。

この記事では、そこから一歩進めて、**収益確認の自動化資産として設計する視点**を入れています。

違いは次の3点です。

- 単発のコード例ではなく、毎日自動実行する運用まで扱う
- Hiro検証ログとして、処理行数、出力件数、実行秒数を条件付きで示す
- 広告、ポイント、アフィリエイトなど、お金に近いCSVを改善判断に使う前提で説明する

PythonでCSVを自動集計する技術自体は派手ではありません。しかし、毎日人間が確認していた数字を自動で集め、異常値や伸びているカテゴリだけを見られるようにすると、改善の速度が変わります。

## 反論と限界

CSV自動集計が向かないケースもあります。

まず、CSVの形式が頻繁に変わる場合です。列名、日付形式、文字コード、単位が毎回変わると、スクリプトの保守コストが高くなります。この場合は、CSVの出力元を固定する、API連携に切り替える、入力変換レイヤーを別に作るといった対応が必要です。

次に、リアルタイム性が必要な場合です。秒単位の価格監視や高速取引のような用途では、CSVを定期的に読む方式は遅すぎます。この記事の対象は、日次、時間単位、案件単位での収益確認やポイント集計です。

また、会計や税務に直結する集計では、消費税、返金、キャンセル、確定前報酬、為替、手数料、丸め処理を慎重に扱う必要があります。この記事のコードは基本パターンであり、法務、税務、会計上の判断を代替するものではありません。

## 今日やるべき読後アクション

今日やるなら、最初から完全自動化を狙わないでください。まず、直近で手作業集計しているCSVを1つ選びます。

次の項目をメモしてください。

```text
CSVファイル名:
文字コード:
日付列:
分類列:
合計列:
現在の手作業時間:
月間の集計回数:
毎日見るべきKPI:
自動実行したい時刻:
失敗時に通知したい先:
```

次に、最小構成で進めます。

1. CSVを1つ読む
2. 3行だけ`print()`で確認する
3. 金額を数値化する
4. 日付とカテゴリで合計する
5. `summary.csv`に出力する
6. ログに`input_rows`と`status=success`を残す
7. 手動実行と自動実行で同じ結果になるか確認する

この順番なら、どこで失敗しているか切り分けやすくなります。

## まとめ：CSV集計を「毎日の作業」から「収益確認の仕組み」に変える

PythonでCSVを自動集計する基本は、次の流れです。

1. CSVを読む
2. 必要な列を取り出す
3. 金額やポイントを数値に変換する
4. 日付やカテゴリをキーにして合計する
5. 結果をCSVに書き出す
6. ログを残して自動実行する

ここまで作れれば、広告収益、ポイント、アフィリエイト、物販データなどを、毎日の手作業から切り離せます。

収益を伸ばすには、記事を書く、商品を改善する、導線を直す、案件を選ぶといった人間の判断がまだ必要です。ただし、その判断に必要な数字を毎日手作業で集める必要はありません。

Python、CSV、自動集計の組み合わせは、自分の時間を消耗せずに収益状況を見続けるための現実的な第一歩です。

数字が自動で集まり、異常値がログで見つかり、伸びているカテゴリがすぐ分かるようになると、収益確認は「頑張って毎日見るもの」から「仕組みが知らせてくれるもの」へ変わります。

## 本気で自動化・不労所得を構築したい方向けの実践マニュアル

CSV集計、収益ログ、ポイント獲得、記事改善、通知、自動実行までを個別に調べていると、時間だけが過ぎます。最短距離で仕組み化したいなら、実際の構築手順、テンプレート、運用チェックリストまでまとまったマニュアルを使ってください。

あなたが寝ている間も、遊んでいる間も、別の仕事をしている間も、数字を集めて改善材料を出し続ける仕組みを作る。その第一歩として、以下の商品一覧ページから実践マニュアルを確認してください。

[本気で自動化・不労所得を構築したい方向けの実践マニュアルを見る](/products/)
