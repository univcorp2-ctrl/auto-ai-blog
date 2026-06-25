from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.budget import can_consume, consume, load_budget, save_budget
from generator.config_loader import load_yaml
from generator.generate import generate_article
from generator.product_pages import load_products, write_product_pages
from generator.runtime import repo_root
from scripts.import_incoming_posts import import_payload, iter_incoming


def run_step(root: Path, args: list[str]) -> None:
    result = subprocess.run(args, cwd=root, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(args)}")


def main() -> int:
    root = repo_root()
    config = load_yaml(root / "generator" / "config.yaml")
    budget_config = config.get("generation_budget", {})
    ledger_path = root / "generator" / ".budget_ledger.json"
    ledger = load_budget(ledger_path, today=date.today())

    imported = []
    for source in iter_incoming(root):
        imported.append(import_payload(root, config, source))

    products = load_products(root / "generator" / "products.yaml")
    write_product_pages(root, config, products)

    daily_articles = int(budget_config.get("daily_article_limit", 1))
    daily_images = int(budget_config.get("daily_image_limit", 1))
    weekly_articles = int(budget_config.get("weekly_article_limit", 7))
    weekly_images = int(budget_config.get("weekly_image_limit", 7))

    if can_consume(
        ledger,
        daily_article_limit=daily_articles,
        daily_image_limit=daily_images,
        weekly_article_limit=weekly_articles,
        weekly_image_limit=weekly_images,
        articles=1,
        images=0,
    ):
        generated = generate_article(root)
        if generated:
            ledger = consume(ledger, articles=1, images=0)
            save_budget(ledger_path, ledger)
            if os.getenv("OPENAI_API_KEY") and can_consume(
                ledger,
                daily_article_limit=daily_articles,
                daily_image_limit=daily_images,
                weekly_article_limit=weekly_articles,
                weekly_image_limit=weekly_images,
                articles=0,
                images=1,
            ):
                run_step(
                    root,
                    [
                        sys.executable,
                        "scripts/generate_page_images.py",
                        "--content-kind",
                        "posts",
                        "--limit",
                        "1",
                        "--prompt-manifest",
                        "tmp/daily-post-image-prompts.json",
                    ],
                )
                ledger = consume(ledger, articles=0, images=1)
                save_budget(ledger_path, ledger)
            elif not os.getenv("OPENAI_API_KEY"):
                print("OPENAI_API_KEY is not set; skipped daily CLI image generation.")
    else:
        print("Generation budget exhausted; skipped Codex article generation.")

    run_step(root, [sys.executable, "scripts/deploy_cloudflare_pages.py"])
    for path in imported:
        print(f"Imported external post: {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
