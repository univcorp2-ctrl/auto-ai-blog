"""Compliance-first affiliate growth agent primitives."""

from affiliate_agent.analytics import aggregate_events, events_to_csv, make_event
from affiliate_agent.compliance import evaluate_program
from affiliate_agent.diagnosis import diagnose_costs
from affiliate_agent.experiments import budget_guard, stable_variant
from affiliate_agent.models import AffiliateProgram, DiagnosisInput
from affiliate_agent.scoring import score_program
from affiliate_agent.workflow import run_workflow

__all__ = [
    "AffiliateProgram",
    "DiagnosisInput",
    "aggregate_events",
    "budget_guard",
    "diagnose_costs",
    "evaluate_program",
    "events_to_csv",
    "make_event",
    "run_workflow",
    "score_program",
    "stable_variant",
]
