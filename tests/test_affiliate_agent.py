from datetime import date, datetime, timezone

import pytest

from affiliate_agent.analytics import aggregate_events, events_to_csv, make_event
from affiliate_agent.compliance import evaluate_program
from affiliate_agent.diagnosis import diagnose_costs
from affiliate_agent.experiments import budget_guard, stable_variant
from affiliate_agent.models import AffiliateProgram, DiagnosisInput
from affiliate_agent.scoring import score_program
from affiliate_agent.workflow import run_workflow


def make_program(**overrides: object) -> AffiliateProgram:
    values: dict[str, object] = {
        "program_id": "P-1",
        "name": "Verified demo",
        "category": "mobile",
        "reward_yen": 10_000,
        "epc_yen": 200,
        "approval_rate": 0.5,
        "approval_days": 30,
        "listing_policy": "ok",
        "sns_policy": "ok",
        "trademark_bidding_policy": "excluded",
        "media_registration_status": "registered",
        "affiliate_url": "https://partner.example/offer",
        "disclosure_text": "PR: 広告を含みます。",
        "last_verified_at": date(2026, 7, 20),
        "active": True,
    }
    values.update(overrides)
    return AffiliateProgram(**values)  # type: ignore[arg-type]


def test_program_scoring_uses_approval_rate_and_margin() -> None:
    score = score_program(make_program(), margin=0.55)
    assert score.expected_approved_reward_yen == 5_000
    assert score.expected_click_value_yen == 100
    assert score.recommended_max_cpc_yen == 55


def test_compliance_is_fail_closed_and_rejects_x() -> None:
    stale = make_program(last_verified_at=date(2026, 1, 1))
    stale_result = evaluate_program(stale, now=date(2026, 7, 31), human_approved=True)
    assert stale_result.eligible is False
    assert "verification_stale" in stale_result.reasons

    x_result = evaluate_program(
        make_program(), channel="x", now=date(2026, 7, 31), human_approved=True
    )
    assert x_result.eligible is False
    assert "channel_not_allowed_for_direct_a8_placement" in x_result.reasons


def test_compliance_allows_verified_website_only_after_human_approval() -> None:
    pending = evaluate_program(make_program(), now=date(2026, 7, 31))
    approved = evaluate_program(make_program(), now=date(2026, 7, 31), human_approved=True)
    assert pending.eligible is False
    assert approved.eligible is True


def test_diagnosis_branches_to_mobile_internet_and_electricity() -> None:
    result = diagnose_costs(
        DiagnosisInput(
            mobile_monthly_yen=16_000,
            mobile_lines=2,
            internet_monthly_yen=6_500,
            internet_type="fiber",
            electricity_monthly_yen=18_000,
            household_size=3,
            willing_to_switch=True,
        )
    )
    assert set(result.categories) == {"mobile", "internet", "electricity"}
    assert result.monthly_saving_high_yen >= result.monthly_saving_low_yen > 0


def test_anonymous_events_aggregate_and_export() -> None:
    occurred_at = datetime(2026, 7, 31, tzinfo=timezone.utc)
    events = [
        make_event("diagnosis_start", session_id="s1", variant_id="a", occurred_at=occurred_at),
        make_event("diagnosis_complete", session_id="s1", variant_id="a", occurred_at=occurred_at),
        make_event("offer_impression", session_id="s1", variant_id="a", occurred_at=occurred_at),
        make_event(
            "affiliate_click",
            session_id="s1",
            variant_id="a",
            payload={"expected_approved_reward_yen": 5_000},
            occurred_at=occurred_at,
        ),
    ]
    summary = aggregate_events(events)
    assert summary["diagnosis_completion_rate"] == 1
    assert summary["offer_ctr"] == 1
    assert summary["simulated_expected_approved_revenue_yen"] == 5_000
    assert "affiliate_click" in events_to_csv(events)

    with pytest.raises(ValueError):
        make_event("page_view", session_id="s1", variant_id="a", payload={"email": "x@y.z"})


def test_variant_and_budget_guards_are_deterministic_and_fail_closed() -> None:
    first = stable_variant("visitor-1", "headline", ["a", "b"])
    assert first == stable_variant("visitor-1", "headline", ["a", "b"])
    allowed, reasons = budget_guard(
        daily_spend_yen=0,
        cumulative_loss_yen=0,
        daily_budget_yen=3_000,
        cumulative_loss_cap_yen=10_000,
        dry_run=True,
        human_approved=False,
    )
    assert allowed is False
    assert set(reasons) == {"dry_run_enabled", "human_approval_required"}


def test_workflow_never_auto_publishes() -> None:
    diagnosis = diagnose_costs(
        DiagnosisInput(
            mobile_monthly_yen=10_000,
            mobile_lines=1,
            internet_monthly_yen=4_000,
            internet_type="fiber",
            electricity_monthly_yen=7_000,
            household_size=1,
        )
    )
    result = run_workflow(
        [make_program()], diagnosis, now=date(2026, 7, 31), human_approved=True
    )
    assert result["status"] == "draft"
    assert result["publish_allowed"] is False
    assert len(result["stages"]) == 5
