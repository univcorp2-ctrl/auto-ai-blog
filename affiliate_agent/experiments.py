from __future__ import annotations

import hashlib
from collections.abc import Sequence


def stable_variant(visitor_id: str, experiment: str, variants: Sequence[str]) -> str:
    if not visitor_id.strip() or not experiment.strip():
        raise ValueError("visitor_id and experiment are required")
    if not variants:
        raise ValueError("at least one variant is required")
    digest = hashlib.sha256(f"{experiment}:{visitor_id}".encode()).digest()
    index = int.from_bytes(digest[:8], "big") % len(variants)
    return variants[index]


def budget_guard(
    *,
    daily_spend_yen: float,
    cumulative_loss_yen: float,
    daily_budget_yen: float,
    cumulative_loss_cap_yen: float,
    dry_run: bool,
    human_approved: bool,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if dry_run:
        reasons.append("dry_run_enabled")
    if not human_approved:
        reasons.append("human_approval_required")
    if daily_spend_yen >= daily_budget_yen:
        reasons.append("daily_budget_reached")
    if cumulative_loss_yen >= cumulative_loss_cap_yen:
        reasons.append("cumulative_loss_cap_reached")
    return not reasons, tuple(reasons)
