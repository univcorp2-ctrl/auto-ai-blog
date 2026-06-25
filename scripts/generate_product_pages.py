from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.config_loader import load_yaml
from generator.product_pages import load_products, write_product_pages
from generator.runtime import repo_root


def main() -> int:
    root = repo_root()
    config = load_yaml(root / "generator" / "config.yaml")
    products = load_products(root / "generator" / "products.yaml")
    written = write_product_pages(root, config, products)
    for path in written:
        print(path.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
