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


def build_product_page(product: Product) -> str:
    paid_items = "\n".join(f"- {item}" for item in product.paid_includes)
    payment_url = product.stripe_payment_link or "/purchase/bank-transfer/"
    payment_note = (
        "Stripe決済ページへ進みます。"
        if product.stripe_payment_link
        else "Stripe決済リンクは準備中です。銀行振込または問い合わせで申し込みできます。"
    )
    return f"""---
title: {yaml_quote(product.title)}
draft: false
description: {yaml_quote(product.free_summary)}
cover:
  image: "/images/category-cover.png"
  relative: false
---

# {product.title}

<section class="carrier-hero">
  <p class="carrier-kicker">無料で概要を確認してから、必要な分だけ購入できます。</p>
  <h2>{product.title}</h2>
  <p>{product.free_summary}</p>
  <p class="carrier-price">税込 {product.price_jpy:,} 円</p>
  <p><a class="carrier-button" href="{payment_url}">Stripeで購入する</a></p>
  <p class="carrier-note">{payment_note}</p>
</section>

## 無料で読める内容

{product.free_summary}

無料部分では、テーマの全体像、向いている人、収益化までの道筋を確認できます。いきなり購入せず、まず自分の事業や副業に合うか判断してください。

## 購入すると手に入る内容

{paid_items}

## こんな人に向いています

- AIや自動化を使って作業時間を減らしたい人
- 記事、動画、配信、販売導線を仕組み化したい人
- 無料情報だけではなく、実装順序までまとまった手順が欲しい人

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
            page_path.write_text(build_product_page(product), encoding="utf-8")
            written.append(page_path)
        success_path = purchase_dir / "success.md"
        success_path.write_text(build_success_page(), encoding="utf-8")
        written.append(success_path)
        bank_path = purchase_dir / "bank-transfer.md"
        bank_path.write_text(build_bank_transfer_page(), encoding="utf-8")
        written.append(bank_path)
    return written
