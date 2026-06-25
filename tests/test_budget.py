from __future__ import annotations

from datetime import date

from generator.budget import BudgetLedger, can_consume, consume


def test_budget_blocks_when_daily_limit_is_exhausted() -> None:
    ledger = BudgetLedger(today=date(2026, 6, 25), articles_today=2, images_today=0, articles_this_week=2, images_this_week=0)

    assert can_consume(ledger, daily_article_limit=2, daily_image_limit=2, weekly_article_limit=10, weekly_image_limit=10, articles=1, images=0) is False


def test_budget_consumes_articles_and_images() -> None:
    ledger = BudgetLedger(today=date(2026, 6, 25), articles_today=0, images_today=0, articles_this_week=0, images_this_week=0)

    updated = consume(ledger, articles=1, images=1)

    assert updated.articles_today == 1
    assert updated.images_today == 1
    assert updated.articles_this_week == 1
    assert updated.images_this_week == 1
