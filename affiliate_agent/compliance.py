from __future__ import annotations

from datetime import date

from affiliate_agent.models import AffiliateProgram, EligibilityResult

ALLOWED_SOCIAL_CHANNELS = {"instagram", "youtube", "tiktok", "pinterest"}
DISALLOWED_DIRECT_SOCIAL_CHANNELS = {"x", "twitter"}
PERMITTED_POLICIES = {"ok", "allowed", "partial_ok"}


def _normalise(value: str) -> str:
    return value.strip().lower()


def evaluate_program(
    program: AffiliateProgram,
    *,
    channel: str = "website",
    traffic_source: str = "organic",
    now: date | None = None,
    verification_ttl_days: int = 30,
    human_approved: bool = False,
) -> EligibilityResult:
    current_date = now or date.today()
    channel_name = _normalise(channel)
    traffic = _normalise(traffic_source)
    reasons: list[str] = []

    if not program.active:
        reasons.append("program_inactive")
    if program.last_verified_at is None:
        reasons.append("verification_missing")
    elif (current_date - program.last_verified_at).days > verification_ttl_days:
        reasons.append("verification_stale")
    if _normalise(program.media_registration_status) != "registered":
        reasons.append("media_not_registered")
    if not program.disclosure_text.strip():
        reasons.append("pr_disclosure_missing")
    if not program.affiliate_url.strip():
        reasons.append("affiliate_url_missing")
    elif "example.invalid" in program.affiliate_url or "replace_me" in _normalise(program.affiliate_url):
        reasons.append("affiliate_url_placeholder")

    if channel_name in DISALLOWED_DIRECT_SOCIAL_CHANNELS:
        reasons.append("channel_not_allowed_for_direct_a8_placement")
    elif channel_name in ALLOWED_SOCIAL_CHANNELS:
        if _normalise(program.sns_policy) not in PERMITTED_POLICIES:
            reasons.append("sns_policy_not_permitted")
    elif channel_name != "website":
        reasons.append("unsupported_channel")

    if traffic == "paid_search":
        if _normalise(program.listing_policy) not in PERMITTED_POLICIES:
            reasons.append("listing_policy_not_permitted")
        if _normalise(program.trademark_bidding_policy) != "excluded":
            reasons.append("trademark_negative_keywords_not_confirmed")
    elif traffic != "organic":
        reasons.append("unsupported_traffic_source")

    if not human_approved:
        reasons.append("human_approval_required")

    return EligibilityResult(eligible=not reasons, reasons=tuple(reasons))
