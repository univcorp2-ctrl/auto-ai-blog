---
title: "Pythonでメルカリ×Yahoo!オークションの価格差を自動判定する方法｜赤字候補を除外する7ステップ"
date: 2026-07-23T03:51:31+09:00
draft: false
tags:
  - "せどり自動化"
  - "Pythonスクリプト"
  - "アービトラージ"
  - "AI"
  - "不動産"
categories:
  - "ビジネス・副業"
description: "「3,000円の価格差を見つけたのに、手数料と送料を引いたら赤字だった」"
---
「3,000円の価格差を見つけたのに、手数料と送料を引いたら赤字だった」

価格差リサーチで本当に怖いのは、商品を見つけられないことではありません。型番違い、状態差、送料、値下げ余地を見落としたまま仕入れることです。

この記事では、メルカリの成約相場とYahoo!オークションの仕入れ候補をCSVに整理し、Pythonで期待利益・ROI・成約数を判定する方法を解説します。

目指すのは自動購入ではなく、**赤字になりやすい候補を機械で除外し、確認価値のある商品だけを人間に回す仕組み**です。

![自動価格差リサーチの全体像](https://image.pollinations.ai/prompt/python%20automation%20mercari%20yahoo%20auction%20arbitrage%20dashboard%20japanese%20ecommerce?width=800&height=400&nologo=true)

## 最初に確認：通常のメルカリアカウントで事業を始めない

コードを書く前に、利用規約と法令を確認してください。

2025年10月22日改定のメルカリ利用規約では、メルカリが指定した法人を除く事業者は、通常のメルカリに登録・利用できず、メルカリShopsへの申込みが案内されています。

家庭の不用品を単発で売る場合と、利益目的で中古品を継続的に仕入れて販売する場合は同じではありません。後者を行うなら、通常アカウントの利用を前提にせず、事業者に該当するか、どのサービスを利用すべきかを先に確認してください。

また、古物を仕入れて営業として販売する場合は、原則として古物商許可が必要です。取り扱う商品や取引方法によって判断が変わる可能性があるため、営業所を管轄する警察署や行政書士などの専門家へ確認しましょう。

記事更新時点で確認した一次情報は次の通りです。

- メルカリの通常の販売手数料は、取引完了時に販売価格の10％です。配送方法、有料機能、売上金の振込などにかかる費用は別途確認してください。[メルカリの手数料](https://help.jp.mercari.com/guide/articles/65/)
- Yahoo!オークションの一般的な落札システム利用料は、落札額の10％です。これは原則として出品者にかかる費用であり、Yahoo!オークションから仕入れるだけなら、そのまま仕入れ手数料として加算する費用ではありません。特定カテゴリなどでは料金体系が異なります。[出品者にかかる利用料](https://support.yahoo-net.jp/PccAuctions/s/article/H000005313)
- Yahoo!オークションでは、同社が特に認めた場合を除き、自動出品ツールや類似プログラムによる出品が禁止されています。[Yahoo!オークションガイドライン細則](https://guide-ec.yahoo.co.jp/notice/rules/auc/detailed_regulations.html)
- メルカリでは、指定法人を除く事業者による通常サービスの登録・利用が制限されています。[メルカリ利用規約](https://static.jp.mercari.com/tos)
- 古物営業の制度と条文は、警察庁およびe-Govの原文で確認できます。[警察庁「古物営業・質屋営業について」](https://www.npa.go.jp/bureau/safetylife/kobutsu/)／[e-Gov「古物営業法」](https://laws.e-gov.go.jp/law/324AC0000000108)
- 個人でも、要件を満たせば特定商取引法上の販売業者に該当します。通信販売では、販売条件や事業者情報などの表示が必要になる場合があります。[消費者庁「通信販売」](https://www.no-trouble.caa.go.jp/what/mailorder/)

本記事では、無許可のスクレイピング、自動出品、自動購入を扱いません。手動で確認した情報、サービスから正規に出力できるデータ、利用許諾のあるAPIなどを入力に使います。

規約、料金、法令は変更される可能性があります。実際に運用する時点で、必ず最新情報を確認してください。

## 今回作る価格差リサーチの仕組み

処理の流れは次の通りです。

```text
許可された方法で候補を収集
  ↓
型番・状態・付属品をCSVへ記録
  ↓
Pythonで手数料・送料・梱包費を計算
  ↓
利益・ROI・成約数・状態一致で絞り込み
  ↓
候補URLを人間が確認
  ↓
予測利益と実利益を記録して条件を改善
```

価格差があっても、別商品を比較していれば判定結果に意味はありません。そこで利益計算とは別に、型番、状態、付属品、成約数を合格条件へ入れます。

## ステップ1：型番で比較できるジャンルを1つ選ぶ

![価格差判定フロー](https://image.pollinations.ai/prompt/flowchart%20python%20script%20mercari%20yahoo%20auction%20price%20difference%20arbitrage%20pipeline?width=800&height=400&nologo=true)

最初は1ジャンル、10商品に限定します。候補は、カメラレンズ、小型家電、ゲーム機、工具、PC周辺機器などです。

例えば、カメラレンズなら次を比較します。

- メーカーと完全な型番
- 対応マウント
- カビ、くもり、傷
- AFなどの動作状況
- フード、キャップ、箱の有無
- ジャンク・部品取り表記

ゲーム機なら、容量、世代、限定色、付属品、動作確認、画面傷、バッテリー状態を分けます。

真贋判定が必要なブランド品、高額時計、トレーディングカード、法規制の強い商品、送料を読みづらい大型商品は、初心者の検証対象に向きません。

## ステップ2：10商品をCSVに記録する

最初から自動取得せず、手動で確認した10商品を `items.csv` に入力します。

以下の3件は、プログラムの動作を確認するためのサンプルです。

```csv
item,description,sale_price,landed_cost,outbound_shipping,packing_cost,fee_rate,sold_count_30d,condition_match,source_url,target_url
Canon EF 50mm F1.8 STM,動作確認済み 箱なし,13200,9200,750,80,0.10,5,yes,https://example.com/source-1,https://example.com/market-1
Nintendo Switch Lite,本体のみ 動作確認済み,18800,15050,850,120,0.10,8,yes,https://example.com/source-2,https://example.com/market-2
Wireless Headphones,動作未確認,7800,6120,520,80,0.10,2,no,https://example.com/source-3,https://example.com/market-3
```

各列の意味は次の通りです。

- `sale_price`：販売中価格ではなく、条件が近い商品の成約価格中央値
- `landed_cost`：落札価格、仕入れ時の送料などを含む取得総額
- `outbound_shipping`：販売後に出品者が負担する送料
- `packing_cost`：箱、緩衝材、ラベルなどの費用
- `fee_rate`：販売先で確認した手数料率
- `sold_count_30d`：直近30日間に成約した類似商品の件数
- `condition_match`：型番・状態・付属品が比較可能なら `yes`
- `source_url`：仕入れ候補を確認できるURL
- `target_url`：成約相場を確認できるURL

`example.com` は入力形式を示す仮URLです。実運用では、後から同じ商品と相場を確認できるURLへ置き換えてください。

販売中価格は売り手の希望額であり、実際に売れた価格ではありません。相場には、可能な限り成約価格の中央値を使います。

成約件数が少ない場合は確認期間を90日まで広げても構いません。ただし、古い価格ほど現在の相場を反映していない可能性が高くなるため、確認日と対象期間も記録してください。

## ステップ3：期待利益とROIの計算式を固定する

基本式は次の通りです。

```text
販売手数料 = 想定販売価格 × 手数料率

期待利益 =
想定販売価格
- 販売手数料
- 仕入れ総額
- 発送費
- 梱包費

ROI =
期待利益 ÷（仕入れ総額 + 発送費 + 梱包費）
```

本記事のROIは、仕入れから発送準備までに投じる金額を分母にしています。仕入れ金額だけを分母にする計算方法もあるため、複数の記録を比較するときは定義を統一してください。

例えば、想定販売価格13,200円、仕入れ総額9,200円、送料750円、梱包費80円、販売手数料10％なら次の結果です。

```text
販売手数料 = 13,200 × 0.10 = 1,320円
期待利益 = 13,200 - 1,320 - 9,200 - 750 - 80 = 1,850円
ROI = 1,850 ÷ 10,030 = 約18.4％
```

さらに安全側へ寄せるなら、想定値下げ額、返品引当、保管費、売上金の振込費用なども控除します。

```text
保守的期待利益 =
期待利益
- 想定値下げ額
- 返品引当
- 保管費
- その他変動費
```

利益額だけでは不十分です。1,000円の利益でも、3,000円の仕入れと30,000円の仕入れでは資金リスクが違うため、ROIも同時に見ます。

## ステップ4：Pythonで利益候補を抽出する

以下は、外部ライブラリを使わない最小構成です。

入力値の欠落、不正な手数料率、負数、NGワード、ゼロ除算を検出します。また、合格候補が0件でも `candidates.csv` を作り直すため、前回実行時の候補が古いファイルとして残りません。

```python
import csv
import json
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

MIN_PROFIT = Decimal("1000")
MIN_ROI = Decimal("0.12")
MIN_SOLD_COUNT = 3

NG_KEYWORDS = {
    "ジャンク",
    "動作未確認",
    "部品取り",
    "破損",
    "模造品",
    "レプリカ",
}

INPUT_COLUMNS = [
    "item",
    "description",
    "sale_price",
    "landed_cost",
    "outbound_shipping",
    "packing_cost",
    "fee_rate",
    "sold_count_30d",
    "condition_match",
    "source_url",
    "target_url",
]

OUTPUT_COLUMNS = INPUT_COLUMNS + [
    "fee",
    "expected_profit",
    "roi",
    "ng_hits",
    "passed",
]


def parse_decimal(row: dict, name: str) -> Decimal:
    raw_value = row.get(name)
    value = raw_value.strip() if isinstance(raw_value, str) else ""

    if not value:
        raise ValueError(f"{name} が空です")

    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} が数値ではありません: {value}") from exc


def parse_integer(row: dict, name: str) -> int:
    raw_value = row.get(name)
    value = raw_value.strip() if isinstance(raw_value, str) else ""

    if not value:
        raise ValueError(f"{name} が空です")

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} が整数ではありません: {value}") from exc


def round_yen(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate(row: dict) -> dict:
    sale_price = parse_decimal(row, "sale_price")
    landed_cost = parse_decimal(row, "landed_cost")
    shipping = parse_decimal(row, "outbound_shipping")
    packing = parse_decimal(row, "packing_cost")
    fee_rate = parse_decimal(row, "fee_rate")
    sold_count = parse_integer(row, "sold_count_30d")

    amounts = {
        "sale_price": sale_price,
        "landed_cost": landed_cost,
        "outbound_shipping": shipping,
        "packing_cost": packing,
    }

    negative_fields = [
        name for name, value in amounts.items() if value < 0
    ]
    if negative_fields:
        raise ValueError(f"負数は入力できません: {negative_fields}")

    if not Decimal("0") <= fee_rate < Decimal("1"):
        raise ValueError("fee_rate は0以上1未満で入力してください")

    if sold_count < 0:
        raise ValueError("sold_count_30d は0以上で入力してください")

    fee = sale_price * fee_rate
    profit = sale_price - fee - landed_cost - shipping - packing
    investment = landed_cost + shipping + packing
    roi = profit / investment if investment > 0 else Decimal("0")

    description = (row.get("description") or "").lower()
    ng_hits = sorted(
        word for word in NG_KEYWORDS
        if word.lower() in description
    )

    condition_match = (
        row.get("condition_match") or ""
    ).strip().lower()

    source_url = (row.get("source_url") or "").strip()
    target_url = (row.get("target_url") or "").strip()

    valid_urls = (
        source_url.startswith(("https://", "http://"))
        and target_url.startswith(("https://", "http://"))
    )

    passed = (
        profit >= MIN_PROFIT
        and roi >= MIN_ROI
        and sold_count >= MIN_SOLD_COUNT
        and condition_match == "yes"
        and not ng_hits
        and valid_urls
    )

    return {
        **{name: row.get(name, "") for name in INPUT_COLUMNS},
        "fee": round_yen(fee),
        "expected_profit": round_yen(profit),
        "roi": f"{roi:.1%}",
        "ng_hits": ",".join(ng_hits),
        "passed": passed,
    }


with open("items.csv", newline="", encoding="utf-8-sig") as src:
    reader = csv.DictReader(src)

    missing = set(INPUT_COLUMNS) - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"不足している列: {sorted(missing)}")

    results = []
    errors = []

    for line_number, row in enumerate(reader, start=2):
        try:
            results.append(calculate(row))
        except (ValueError, TypeError, KeyError) as exc:
            errors.append({
                "line": line_number,
                "item": row.get("item", ""),
                "error": str(exc),
            })

passed_rows = [row for row in results if row["passed"]]

with open(
    "candidates.csv",
    "w",
    newline="",
    encoding="utf-8-sig",
) as dst:
    writer = csv.DictWriter(dst, fieldnames=OUTPUT_COLUMNS)
    writer.writeheader()
    writer.writerows(passed_rows)

summary = {
    "input_count": len(results) + len(errors),
    "evaluated_count": len(results),
    "pass_count": len(passed_rows),
    "error_count": len(errors),
    "errors": errors,
}

print(json.dumps(summary, ensure_ascii=False, indent=2))
```

ファイル名を `price_research.py` として保存し、PowerShellで実行します。

```powershell
python --version
python price_research.py
```

`candidates.csv` には合格候補だけが保存されます。

`error_count` が1件以上なら、その日の結果をそのまま仕入れ判断に使わないでください。エラー行を修正し、`error_count` が0件になるまで再実行します。

## 掲載データでの再現結果

上記の3件を、Windows PowerShellとPython 3.11.9で実行した場合の判定結果は次の通りです。

| 商品 | 期待利益 | ROI | 成約数 | 状態一致 | NGワード | 判定 |
|---|---:|---:|---:|---|---|---|
| Canon EF 50mm F1.8 STM | 1,850円 | 18.4％ | 5件 | yes | なし | 通過 |
| Nintendo Switch Lite | 900円 | 5.6％ | 8件 | yes | なし | 除外 |
| Wireless Headphones | 300円 | 4.5％ | 2件 | no | 動作未確認 | 除外 |

標準出力は次のようになります。

```json
{
  "input_count": 3,
  "evaluated_count": 3,
  "pass_count": 1,
  "error_count": 0,
  "errors": []
}
```

ここで重要なのは、Nintendo Switch Liteに3,750円の表面上の価格差があっても、手数料、送料、梱包費を引くと利益が900円しか残らない点です。

Wireless Headphonesは利益・ROI・成約数の条件を満たさないうえ、「動作未確認」と状態不一致の両方に該当します。

この3件は計算ロジックを再現するための検証用データであり、実際の売買による収益実績ではありません。確認できるのは、掲載した入力値に対して費用計算と条件抽出が再現できることまでです。

## ステップ5：判定条件を小さく始める

初心者向けの初期条件は次の通りです。

- 期待利益：1,000円以上
- ROI：12％以上
- 直近30日成約数：3件以上
- 型番・状態・付属品：比較可能
- NGワード：なし
- 仕入れ候補URLと相場URL：両方あり
- 入力エラー：0件

これは正解値ではなく、検証開始時の仮説です。

通知が1日20件を超えるなら、最低利益、ROI、成約数を引き上げます。候補がほとんど出ない場合は、条件を下げる前に、対象商品の価格帯、送料見積もり、成約データの集め方が適切か確認してください。

除外キーワードもカテゴリ別に管理します。「くもり」はカメラでは重要でも、ゲーム機には関係ありません。一律の巨大なNGワード集を作ると、有望な商品まで除外します。

初期条件を変更したら、実行ログに必ず残してください。条件が異なる結果を同じ基準で比較すると、改善したのか、単に基準を緩めたのか分からなくなります。

## 実運用ログから分かる「生成成功」と「全体成功」の違い

このサイトの `auto-ai-blog` では、`run_daily.bat` から `scripts\run_daily_guarded.py` を起動し、記事生成、保存、Git反映などを段階的に処理しています。

2026年7月11日の実行ログには、次の順序が記録されていました。

```text
manual_draft: codex CLI succeeded
Saved post: ...
git commit failed:
Unable to create '.git/HEAD.lock': File exists.
```

つまり、記事本文の生成と保存には成功していても、Gitへの反映には失敗しています。

**一部工程の成功と、処理全体の成功は別物です。**

価格差リサーチでも、次の状態を分けて記録する必要があります。

```text
データ収集：成功／失敗
CSV保存：成功／失敗
利益計算：成功／失敗
候補抽出：成功／失敗
通知送信：成功／失敗
URL再確認：未確認／確認済み
仕入れ判断：採用／保留／除外
販売結果：販売済み／在庫中／返品
```

「候補が0件」と「プログラムが失敗して候補を出せなかった」は、まったく違う結果です。

## ステップ6：人間がURLを開いて最終確認する

自動判定を通過しても、購入前に次を確認します。

- メーカー、型番、容量、色、世代が完全一致しているか
- 箱、説明書、充電器などの付属品が一致しているか
- ジャンク、欠品、動作未確認の記載がないか
- 写真と説明文に矛盾がないか
- 仕入れ総額に送料が含まれているか
- 相場URLが販売中ではなく成約済み商品を示しているか
- 同一条件の商品が複数件売れているか
- 成約価格の確認日が古すぎないか
- 出品者評価と商品説明に不自然な点がないか
- 値下げしても最低利益を確保できるか
- 規約上利用できるアカウント・サービスか
- 古物商許可など、必要な許可を確認したか

1つでも確認できなければ、`保留` または `除外` にします。「たぶん同じ商品」は仕入れ理由になりません。

判断結果は、少なくとも次の3種類に分けます。

```text
採用：確認項目をすべて満たす
保留：追加質問や現物確認が必要
除外：利益、状態、規約、許可などの条件を満たさない
```

## ステップ7：通知と実績ログを改善へ戻す

![価格差リサーチ画面の例](https://image.pollinations.ai/prompt/japanese%20ecommerce%20arbitrage%20research%20spreadsheet%20dashboard%20profit%20roi%20charts?width=800&height=400&nologo=true)

通知には商品名だけでなく、判断材料を含めます。

```text
商品名：Canon EF 50mm F1.8 STM
想定販売価格：13,200円
仕入れ総額：9,200円
販売手数料：1,320円
発送費：750円
梱包費：80円
期待利益：1,850円
ROI：18.4％
直近30日成約数：5件
状態一致：yes
仕入れ候補URL：...
相場確認URL：...
```

販売後は、元の行に次の列を追加します。

```csv
purchased_at,sold_at,actual_sale_price,actual_shipping,actual_profit,discount_count,return_flag,failure_reason
```

これにより、「候補を見つけた」で終わらず、予測と実績の差から条件を修正できます。

`failure_reason` は自由記述だけでなく、次のような定型値にすると集計しやすくなります。

```text
shipping_overrun
price_drop
condition_mismatch
missing_accessory
return
long_inventory
input_error
rule_violation
```

## 専門家が見るKPIと初期目標

売上だけでは、自動化の品質は測れません。

| KPI | 計算方法 | 初期目標の例 |
|---|---|---:|
| 通知確認率 | 確認した通知数 ÷ 通知数 | 80％以上 |
| 仕入れ採用率 | 仕入れ数 ÷ 確認数 | 10〜30％ |
| 予測誤差率 | `abs(実利益 − 予測利益) ÷ abs(予測利益)` | 20％以内 |
| 平均在庫日数 | 販売日 − 仕入日 | 30日以内 |
| 返品・キャンセル率 | 返品・キャンセル件数 ÷ 販売件数 | 3％未満 |
| 確認時間 | URL確認に使った時間 | 1件3分以内 |
| 通知精度 | 人間が有効と判断した件数 ÷ 通知数 | 50％以上 |
| 入力エラー率 | エラー件数 ÷ 入力件数 | 0％ |
| 保存成功率 | 正常に保存できた回数 ÷ 実行回数 | 100％ |

予測利益が0円の場合、予測誤差率は計算できません。0円の行は別集計にするか、分母を別途定義してください。

目標値はカテゴリと価格帯で変わります。まず20〜30件分を記録し、自分の実績から基準を更新します。

例えば、実利益が予測より低ければ、原因を次のように分類します。

- 送料差：カテゴリ別送料テーブルを修正する
- 値下げ：想定値下げ額を費用へ追加する
- 状態差：状態一致の判定項目を細分化する
- 相場下落：古い成約データの重みを下げる
- 返品：返品引当を追加する
- 長期在庫：最低成約数を引き上げる
- 入力ミス：必須項目と数値範囲の検証を追加する

原因を条件へ戻さなければ、Pythonは同じ失敗候補を出し続けます。

## よくある失敗と対策

### 販売中価格を相場にする

販売中価格は「売れた価格」ではありません。成約価格の中央値を使い、件数、対象期間、確認日も記録します。

### Yahoo!オークションの出品者手数料を仕入れ費用へ加える

Yahoo!オークションの落札システム利用料は、原則として出品者にかかる費用です。仕入れ側では、落札価格、送料、決済時に実際に発生する費用を `landed_cost` へ入れます。

反対に、Yahoo!オークションを販売先として使う場合は、販売側の手数料として計算します。

### 手数料だけ引いて送料を忘れる

仕入れ送料、販売送料、梱包費を別々に記録します。大型商品は、梱包後のサイズと送料を確認できなければ仕入れないルールも有効です。

### 状態の違う商品を比較する

「美品」と「動作未確認」を同じ商品として計算しないでください。型番一致と状態一致は別の判定項目です。

### 合格候補が0件のとき、古いCSVが残る

合格候補があるときだけ `candidates.csv` を書き出す実装では、0件の日に前回の候補ファイルが残ることがあります。

本記事のコードは、0件でもヘッダーだけのファイルへ更新します。出力日時もログへ残せば、古い候補を誤って仕入れる事故を防ぎやすくなります。

### 通知が多すぎて見なくなる

1日5件程度から始めます。上限を超えたら、期待利益、ROI、成約数の順に条件を厳しくします。

### 自動購入まで一気に進める

誤判定1件の損失が大きいため、初期段階では「候補抽出まで自動、購入判断は人間」に限定します。

### 成功・失敗ログを残さない

最低でも、次の項目を保存します。

```text
実行日時
入力件数
正常評価件数
通過件数
入力エラー件数
判定条件
CSV保存結果
通知結果
例外名
エラーメッセージ
```

候補0件、入力エラー、保存失敗、通知失敗を別々に記録してください。

## この方法への反論と限界

この仕組みを作っても、完全放置にはなりません。

相場は変動し、成約数の少ない商品では中央値も安定しません。真贋や細かな状態差は、CSVだけでは判断できません。送料改定や販売手数料の変更によって、昨日の黒字条件が今日も有効とは限りません。

成約データにも偏りがあります。確認できた商品だけで中央値を計算すると、検索条件から漏れた商品や、削除された取引を反映できない場合があります。

期待利益は確定利益ではありません。値下げ、返品、故障、付属品不足、配送サイズの変更、保管期間、資金拘束によって実利益は下がります。

さらに、継続的な仕入れ販売が事業に該当する場合、通常のメルカリアカウントを利用できない可能性があります。古物商許可、税務、特定商取引法上の表示なども、利益計算とは別に確認が必要です。

したがって、この方法の差別化は「自動で大量取得すること」ではありません。

- 許可されたデータだけを使う
- 比較条件をCSVで再現できるようにする
- 費用を漏れなく計算する
- エラーと候補0件を区別する
- 最終判断を人間に残す
- 実利益から判定条件を更新する

この6点を一つの改善ループにすることです。

## 今日から始めるチェックリスト

1. 利用規約、事業者該当性、古物商許可の要否を確認する
2. 型番で比較しやすいジャンルを1つ選ぶ
3. 掲載した3件のサンプルでPythonコードを実行する
4. `pass_count: 1`、`error_count: 0`になることを確認する
5. 実在する10商品を手動でCSVへ入力する
6. 成約価格、仕入れ総額、送料、梱包費、手数料を分ける
7. 通過候補だけURLを開いて確認する
8. 採用・保留・除外の理由を記録する
9. 販売後に予測利益と実利益の差を測る
10. 差が生じた原因を判定条件へ戻す

最初の目標は、全自動売買ではありません。

**10商品の中から赤字になりやすい候補を正しく除外し、確認価値のある商品だけを抽出できること**です。

それが安定してから、通知、送料テーブル、カテゴリ別NGワード、実績ダッシュボードを追加してください。

検索件数を増やすより、失敗を次の判定へ反映できる仕組みを作る方が、長期的な資産になります。

[自動化の設計・検証・改善を体系的に学べる実践マニュアルを見る](/products/)
