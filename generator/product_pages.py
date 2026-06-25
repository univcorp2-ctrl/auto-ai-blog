from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from generator.markdown_post import make_slug, yaml_quote
from generator.routing import route_category_to_site


@dataclass(frozen=True)
class Product:
    id: str
    title: str
    category: str
    price_jpy: int
    stripe_payment_link: str
    source_manual: str
    free_summary: str
    paid_includes: list[str]

    @property
    def slug(self) -> str:
        return self.id or make_slug(self.title)


def load_products(path: Path) -> list[Product]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    raw_products = data.get("products", [])
    if not isinstance(raw_products, list):
        raise ValueError("products.yaml must contain a products list")
    products: list[Product] = []
    for item in raw_products:
        products.append(
            Product(
                id=str(item["id"]),
                title=str(item["title"]),
                category=str(item["category"]),
                price_jpy=int(item["price_jpy"]),
                stripe_payment_link=str(item.get("stripe_payment_link", "")),
                source_manual=str(item.get("source_manual", "")),
                free_summary=str(item["free_summary"]),
                paid_includes=[str(value) for value in item.get("paid_includes", [])],
            )
        )
    return products


def products_by_site(config: dict[str, Any], products: list[Product]) -> dict[Path, list[Product]]:
    grouped: dict[Path, list[Product]] = {}
    for product in products:
        grouped.setdefault(route_category_to_site(config, product.category), []).append(product)
    return grouped


def build_product_index(products: list[Product]) -> str:
    links = "\n".join(f"- [{product.title}](/manuals/{product.slug}/)" for product in products)
    return "\n".join(
        [
            "---",
            'title: "無料ガイドと有料マニュアル"',
            "draft: false",
            "cover:",
            '  image: "/images/category-cover.png"',
            "  relative: false",
            "---",
            "",
            "# 無料ガイドと有料マニュアル",
            "",
            "まずは無料部分で全体像を確認し、必要なテーマだけ有料マニュアルで深掘りできます。",
            "",
            links,
            "",
        ]
    )


def build_success_page() -> str:
    return """---
title: "決済完了"
draft: false
---

# 決済ありがとうございます

Stripe決済が完了しました。購入内容の確認とマニュアルの受け取り案内を、登録メールアドレス宛にお送りします。

メールが届かない場合は、決済時のメールアドレスと購入マニュアル名を添えてお問い合わせください。
"""


def build_bank_transfer_page() -> str:
    return """---
title: "銀行振込で申し込む"
draft: false
---

# 銀行振込で申し込む

銀行振込を希望する場合は、購入したいマニュアル名、氏名、メールアドレスを添えてお問い合わせください。確認後、振込先と受け取り方法をご案内します。

<p><a class="carrier-button carrier-button-secondary" href="mailto:info@yurui-business.com?subject=銀行振込でのマニュアル購入希望">銀行振込で問い合わせる</a></p>
"""


def strip_markdown_noise(markdown: str) -> str:
    text = markdown.replace("\r\n", "\n")
    text = text.replace("**", "").replace("__", "").replace("`", "")
    return text.strip()


def extract_manual_headings(manual_markdown: str, limit: int = 8) -> list[str]:
    headings: list[str] = []
    for line in manual_markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("##"):
            heading = stripped.lstrip("#").strip()
            if heading:
                headings.append(heading)
        if len(headings) >= limit:
            break
    return headings


def extract_manual_sample(manual_markdown: str, max_chars: int = 950) -> str:
    text = strip_markdown_noise(manual_markdown)
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text[:max_chars].rstrip()


def build_beginner_steps(product: Product) -> str:
    return "\n".join(
        [
            "1. **目的を1つに絞る**: まず、このマニュアルで作る仕組みを「集客」「販売」「配信」「運用削減」のどれに使うか決めます。目的が曖昧なままツールを増やすと、途中で設定だけが増えて成果が見えなくなります。",
            "2. **最小構成を書き出す**: 必要なアカウント、入力データ、公開先、決済または問い合わせ導線を1枚に整理します。初心者は完璧な全自動化より、最初に1回だけ人間が確認できる形を作る方が失敗しにくいです。",
            f"3. **{product.category}向けの導線を作る**: 読者が最初に見る無料情報、信頼を作る比較・事例・注意点、最後に申し込む有料導線を分けて配置します。無料部分で納得できない読者は購入しないため、販売前の説明量を削らないことが重要です。",
            "4. **1件だけ実行して記録する**: 投稿、配信、販売ページ、問い合わせ、決済のどれかを1件だけ最後まで通します。成功したかどうかだけでなく、どこで迷ったか、どの文章が弱かったか、どの画像が内容を説明していなかったかを記録します。",
            "5. **テンプレート化する**: 成功した文章構成、画像プロンプト、CTA、チェック項目をテンプレートにします。毎回ゼロから作らず、テーマだけ差し替えられる状態にすると、外部AIや自動投稿APIへ渡しやすくなります。",
            "6. **小さく公開して改善する**: 最初から大量投稿せず、公開後のクリック、滞在、問い合わせ、購入率を確認します。反応のあるテーマだけを伸ばし、反応の薄いテーマは見出し・画像・導線を見直します。",
        ]
    )


def build_expert_checklist(product: Product) -> str:
    paid_checks = "\n".join(f"- {item}が、読者の次の行動にどうつながるかを説明できるか。" for item in product.paid_includes)
    return "\n".join(
        [
            "- **収益導線**: 無料情報から有料マニュアル、問い合わせ、決済までの流れが1クリック単位で確認できるか。",
            "- **初心者の迷い**: 専門用語を使う場合、直後に何をすればよいかを書いているか。",
            "- **画像の役割**: 画像が飾りではなく、手順・構造・成果物・比較のどれかを説明しているか。",
            "- **自動化の境界**: AIに任せる部分、人間が確認する部分、公開してよい基準を分けているか。",
            "- **リスク表記**: 投資、収益、広告、アフィリエイト、決済、権利関係など、誤解されやすい部分に注意書きがあるか。",
            paid_checks,
        ]
    )


def build_failure_countermeasures() -> str:
    return "\n".join(
        [
            "- **ツール設定で止まる**: まず有料導線なしのテスト投稿で、記事公開と画像表示だけを確認します。決済や外部連携は最後に足す方が原因を切り分けやすくなります。",
            "- **文章が薄くなる**: 見出しごとに「目的」「手順」「判断基準」「失敗例」「確認方法」を入れます。感想や一般論だけで終わる記事は、購入判断につながりません。",
            "- **画像が内容と合わない**: 画像プロンプトに、記事タイトル、読者の状況、画面や資料などの具体物、説明したい工程を入れます。抽象的なAI風画像は避けます。",
            "- **自動投稿が暴走する**: 1日の投稿数、画像生成数、週次上限を決め、ログを残します。特に画像は高品質設定ほど消費が大きいため、優先度の高い記事だけに使います。",
            "- **売れない理由が分からない**: クリック率、本文到達、CTAクリック、問い合わせ、決済完了を分けて見ます。売上だけを見ると、どこを直すべきか分からなくなります。",
        ]
    )


def build_kpi_section() -> str:
    return "\n".join(
        [
            "- 公開本数: まず週1から始め、品質を落とさず継続できるかを見る。",
            "- 画像一致率: 記事内容を説明している画像が、公開記事の中で何割あるかを確認する。",
            "- CTAクリック率: 無料部分を読んだ人が、詳細ページや申し込みへ進んでいるかを見る。",
            "- 問い合わせ率: 読者が自分の状況に置き換えられる説明になっているかを測る。",
            "- 購入率: 価格に対して、得られる成果物・手順・テンプレートの価値が伝わっているかを確認する。",
            "- 改善サイクル: 公開後に見出し、画像、CTA、価格、無料範囲を見直した回数を記録する。",
        ]
    )


def build_first_session_plan(product: Product) -> str:
    return "\n".join(
        [
            f"- **0分から15分**: {product.title}で扱うテーマを、自分の事業・副業・メディアのどこに接続するか決めます。読者像、提供する無料情報、最後に案内する有料導線を1行ずつ書きます。",
            "- **15分から35分**: 最初の記事または販売ページの見出しを作ります。見出しは「問題」「原因」「手順」「注意点」「次の行動」の順に並べ、初心者が迷う場所を先回りして説明します。",
            "- **35分から55分**: 画像で説明する箇所を決めます。仕組み、手順、比較、成果物のどれを画像にするかを選び、抽象的な雰囲気画像ではなく、本文理解を助ける画像プロンプトを書きます。",
            "- **55分から75分**: CTAと申し込み導線を確認します。無料部分を読んだ人が、なぜ次に有料マニュアルや問い合わせへ進むのかを、1文で説明できる状態にします。",
            "- **75分から90分**: 公開前チェックを行います。タイトル、説明文、画像、本文、CTA、免責、スマホ表示を確認し、次回から同じ手順で作れるようにテンプレート化します。",
        ]
    )


def build_quality_gate() -> str:
    return "\n".join(
        [
            "- タイトルだけを見て、誰のどんな問題を解決する記事か分かる。",
            "- 最初の3段落で、無料で読む価値と有料で深掘りする価値が分かれる。",
            "- 各見出しの中に、具体的な作業・判断基準・確認方法のいずれかが入っている。",
            "- 画像は本文の内容を説明しており、汎用的なAI風ビジュアルだけで終わっていない。",
            "- 初心者が次に開くべきツール、入力する情報、確認する画面を想像できる。",
            "- 収益や成果を断定しすぎず、必要な検証・改善・リスク表記が入っている。",
            "- 最後のCTAが唐突ではなく、本文で説明した課題の自然な続きになっている。",
            "- 公開後に見る数字と、次に直す場所が決まっている。直感ではなく、クリック、滞在、問い合わせ、購入のどこで落ちているかを見て改善する。",
        ]
    )


def build_product_page(product: Product, manual_markdown: str = "") -> str:
    paid_items = "\n".join(f"- {item}" for item in product.paid_includes)
    payment_url = product.stripe_payment_link or "/purchase/bank-transfer/"
    payment_note = (
        "Stripe決済ページへ進みます。"
        if product.stripe_payment_link
        else "Stripe決済リンクは準備中です。銀行振込または問い合わせで申し込みできます。"
    )
    manual_sample = extract_manual_sample(manual_markdown) if manual_markdown else product.free_summary
    headings = extract_manual_headings(manual_markdown)
    roadmap_items = "\n".join(f"{index}. {heading}" for index, heading in enumerate(headings, start=1))
    if not roadmap_items:
        roadmap_items = "\n".join(
            [
                "1. 全体像と収益導線を理解する",
                "2. 必要なツールとアカウントを準備する",
                "3. 自動化フローを小さく作って検証する",
                "4. 投稿・販売・改善を継続できる形に整える",
            ]
        )
    image_path = f"/images/manuals/{product.id}.png"
    return f"""---
title: {yaml_quote(product.title)}
draft: false
description: {yaml_quote(product.free_summary)}
cover:
  image: "{image_path}"
  relative: false
---

# {product.title}

<section class="carrier-hero">
  <p class="carrier-kicker">無料で概要を確認し、必要な人だけ実践マニュアルへ進めます。</p>
  <h2>{product.title}</h2>
  <p>{product.free_summary}</p>
  <p class="carrier-price">税込 {product.price_jpy:,} 円</p>
  <p><a class="carrier-button" href="{payment_url}">Stripeで購入する</a></p>
  <p class="carrier-note">{payment_note}</p>
</section>

![{product.title}]({image_path})

## 無料で読める内容

{product.free_summary}

無料部分では、テーマの全体像、向いている人、収益化までの道筋を確認できます。いきなり購入せず、まず自分の事業や副業に合うか判断してください。このページでは、マニュアルの中核アイデア、必要な準備、実装の流れ、購入後に得られる具体的な成果まで見えるようにしています。

## このマニュアルで解決できること

このマニュアルは、単なるアイデア集ではなく、収益化までの作業を順番に進めるための実装ガイドです。何を準備し、どの順番で組み、どこを自動化し、どこを人間が確認すべきかを整理しています。

特に重要なのは、無料情報だけでは曖昧になりがちな「実際に手を動かす順番」です。ツール選定、初期設定、投稿や配信の型、決済や導線、改善ポイントまでをつなげて、あとから外注化・自動化しやすい形に落とし込みます。

## 購入すると手に入る内容

{paid_items}

## 初心者向けステップ・バイ・ステップ

{build_beginner_steps(product)}

## 初回90分の作業プラン

{build_first_session_plan(product)}

## 実装ロードマップ

{roadmap_items}

## 無料サンプル

以下はマニュアル内容の一部をもとにしたサンプルです。購入前に、扱うテーマの深さと方向性を確認できます。

> {manual_sample.replace(chr(10), chr(10) + "> ")}

## 購入後の進め方

1. まず全体像を読み、必要なアカウントやツールを洗い出します。
2. 次に、最小構成で1本の投稿・1件の配信・1つの販売導線を作ります。
3. 動作確認後、テンプレート化して毎日または毎週の運用に乗せます。
4. 反応が出たテーマを伸ばし、不要な作業は自動化または外注化します。

## 購入者が作る成果物

購入者が最終的に作るべきものは、単なるメモやアイデアではありません。公開できる記事、内容に合った画像、販売または問い合わせにつながる導線、更新を続けるためのチェックリスト、そして自動投稿に渡せるテンプレートです。

具体的には、1本の記事につき「読者の悩み」「無料で渡す価値」「有料で深掘りする価値」「画像で説明する部分」「申し込みへ進む理由」をセットにします。この形まで落とし込むと、外部AIに記事を作らせる場合でも、品質の低い文章や内容と合わない画像を弾きやすくなります。

## 専門家目線のチェックポイント

{build_expert_checklist(product)}

## つまずきやすい失敗と対策

{build_failure_countermeasures()}

## 成果を測るKPI

{build_kpi_section()}

## 公開前の品質ゲート

{build_quality_gate()}

## 最終的に目指す成果物

購入後に目指すのは、知識を読んで終わりにすることではありません。自分のテーマに合わせた投稿テンプレート、販売ページ、配信や集客の導線、そして改善のためのチェック項目を持つことです。小さく作って検証し、反応が取れた部分だけを伸ばしていくことで、毎回ゼロから考えずに運用できる状態を目指します。

また、外部AIや自動投稿システムと組み合わせる場合でも、最初に人間が確認すべき品質基準を決めておくことが大切です。このマニュアルでは、どこを自動化し、どこを確認し、どこを収益導線につなげるかを一つの流れとして扱います。

## こんな人に向いています

- AIや自動化を使って作業時間を減らしたい人
- 記事、動画、配信、販売導線を仕組み化したい人
- 無料情報だけではなく、実装順序までまとまった手順が欲しい人
- 何から着手すればよいか迷わず、最初の成果物まで進めたい人
- 将来的に外部AIや自動投稿システムへつなげたい人

## 購入前の注意

このマニュアルは「何もしなくても必ず稼げる」と約束するものではありません。狙う市場を決め、初期設定を行い、公開後の反応を見ながら改善することが前提です。その代わり、ゼロから毎回考え直すのではなく、再現しやすい作業手順に沿って進められるように構成しています。

## 申し込み

<p><a class="carrier-button" href="{payment_url}">Stripeで購入する</a></p>
<p><a class="carrier-button carrier-button-secondary" href="/purchase/bank-transfer/">銀行振込で相談する</a></p>
"""


def write_product_pages(root: Path, config: dict[str, Any], products: list[Product]) -> list[Path]:
    written: list[Path] = []
    for site_dir, site_products in products_by_site(config, products).items():
        manuals_dir = root / site_dir / "content" / "manuals"
        purchase_dir = root / site_dir / "content" / "purchase"
        manuals_dir.mkdir(parents=True, exist_ok=True)
        purchase_dir.mkdir(parents=True, exist_ok=True)
        index_path = manuals_dir / "_index.md"
        index_path.write_text(build_product_index(site_products), encoding="utf-8")
        written.append(index_path)
        for product in site_products:
            product_dir = manuals_dir / product.slug
            product_dir.mkdir(parents=True, exist_ok=True)
            page_path = product_dir / "index.md"
            manual_path = root / "generator" / "source_manuals" / product.source_manual
            manual_markdown = manual_path.read_text(encoding="utf-8") if manual_path.exists() else ""
            page_path.write_text(build_product_page(product, manual_markdown), encoding="utf-8")
            written.append(page_path)
        success_path = purchase_dir / "success.md"
        success_path.write_text(build_success_page(), encoding="utf-8")
        written.append(success_path)
        bank_path = purchase_dir / "bank-transfer.md"
        bank_path.write_text(build_bank_transfer_page(), encoding="utf-8")
        written.append(bank_path)
    return written
