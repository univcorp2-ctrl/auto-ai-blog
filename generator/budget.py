from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class BudgetLedger:
    today: date
    articles_today: int = 0
    images_today: int = 0
    articles_this_week: int = 0
    images_this_week: int = 0


def can_consume(
    ledger: BudgetLedger,
    *,
    daily_article_limit: int,
    daily_image_limit: int,
    weekly_article_limit: int,
    weekly_image_limit: int,
    articles: int,
    images: int,
) -> bool:
    return (
        ledger.articles_today + articles <= daily_article_limit
        and ledger.images_today + images <= daily_image_limit
        and ledger.articles_this_week + articles <= weekly_article_limit
        and ledger.images_this_week + images <= weekly_image_limit
    )


def consume(ledger: BudgetLedger, *, articles: int, images: int) -> BudgetLedger:
    return BudgetLedger(
        today=ledger.today,
        articles_today=ledger.articles_today + articles,
        images_today=ledger.images_today + images,
        articles_this_week=ledger.articles_this_week + articles,
        images_this_week=ledger.images_this_week + images,
    )


def load_budget(path: Path, today: date | None = None) -> BudgetLedger:
    current_day = today or date.today()
    if not path.exists():
        return BudgetLedger(today=current_day)
    data = json.loads(path.read_text(encoding="utf-8"))
    saved_day = date.fromisoformat(str(data.get("today", current_day.isoformat())))
    if saved_day != current_day:
        same_week = saved_day.isocalendar()[:2] == current_day.isocalendar()[:2]
        return BudgetLedger(
            today=current_day,
            articles_this_week=int(data.get("articles_this_week", 0)) if same_week else 0,
            images_this_week=int(data.get("images_this_week", 0)) if same_week else 0,
        )
    return BudgetLedger(
        today=current_day,
        articles_today=int(data.get("articles_today", 0)),
        images_today=int(data.get("images_today", 0)),
        articles_this_week=int(data.get("articles_this_week", 0)),
        images_this_week=int(data.get("images_this_week", 0)),
    )


def save_budget(path: Path, ledger: BudgetLedger) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(ledger)
    data["today"] = ledger.today.isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
