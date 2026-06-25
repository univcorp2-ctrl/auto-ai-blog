from __future__ import annotations

from pathlib import Path

from generator.config_loader import load_yaml
from generator.product_pages import build_product_page, load_products, products_by_site
from generator.routing import route_category_to_site


def test_route_category_to_site_uses_configured_site_map() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_yaml(root / "generator" / "config.yaml")

    assert route_category_to_site(config, "AI・テック") == Path("sites/ai-tech")
    assert route_category_to_site(config, "ビジネス・副業") == Path("sites/business")
    assert route_category_to_site(config, "不動産投資") == Path("sites/real-estate")
    assert route_category_to_site(config, "未知カテゴリ") == Path("sites/ai-tech")


def test_products_have_free_and_paid_sections() -> None:
    root = Path(__file__).resolve().parents[1]
    products = load_products(root / "generator" / "products.yaml")

    assert products
    for product in products:
        assert product.free_summary
        assert product.paid_includes
        page = build_product_page(product, "# サンプル\n\n## 第1章\n\n本文です。" * 20)
        assert "無料で読める内容" in page
        assert "購入すると手に入る内容" in page
        assert "Stripeで購入する" in page
        assert f"![{product.title}](/images/manuals/{product.id}.png)" in page
        assert "無料サンプル" in page
        assert "実装ロードマップ" in page
        assert len(page) > 2500


def test_products_are_grouped_by_routed_site() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_yaml(root / "generator" / "config.yaml")
    products = load_products(root / "generator" / "products.yaml")

    grouped = products_by_site(config, products)

    assert Path("sites/ai-tech") in grouped
    assert Path("sites/business") in grouped
    assert Path("sites/real-estate") in grouped
