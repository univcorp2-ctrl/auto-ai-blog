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
