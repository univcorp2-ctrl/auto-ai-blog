from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.runtime import repo_root


def stripe_request(secret_key: str, path: str, data: dict[str, Any]) -> dict[str, Any]:
    encoded = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.stripe.com/v1/{path}",
        data=encoded,
        headers={"Authorization": f"Bearer {secret_key}"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    secret_key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not secret_key:
        print("STRIPE_SECRET_KEY is required.", file=sys.stderr)
        return 1

    root = repo_root()
    products_path = root / "generator" / "products.yaml"
    data = yaml.safe_load(products_path.read_text(encoding="utf-8"))
    for product in data.get("products", []):
        if product.get("stripe_payment_link"):
            continue
        stripe_product = stripe_request(secret_key, "products", {"name": product["title"]})
        price = stripe_request(
            secret_key,
            "prices",
            {
                "product": stripe_product["id"],
                "currency": "jpy",
                "unit_amount": int(product["price_jpy"]),
            },
        )
        link = stripe_request(
            secret_key,
            "payment_links",
            {
                "line_items[0][price]": price["id"],
                "line_items[0][quantity]": 1,
                "after_completion[type]": "redirect",
                "after_completion[redirect][url]": "https://yurui-business.com/purchase/success/",
            },
        )
        product["stripe_payment_link"] = link["url"]
        print(f"{product['id']}: {link['url']}")

    products_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
