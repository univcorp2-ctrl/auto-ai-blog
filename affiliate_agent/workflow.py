from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from affiliate_agent.compliance import evaluate_program
from affiliate_agent.models import AffiliateProgram, DiagnosisResult
from affiliate_agent.scoring import score_program


def run_workflow(
    programs: Sequence[AffiliateProgram],
    diagnosis: DiagnosisResult,
    *,
    channel: str = "website",
    traffic_source: str = "organic",
    now: date | None = None,
    human_approved: bool = False,
) -> dict[str, Any]:
    opportunities = []
    audits = []
    for program in programs:
        score = score_program(program)
        audit = evaluate_program(
            program,
            channel=channel,
            traffic_source=traffic_source,
            now=now,
            human_approved=human_approved,
        )
        opportunities.append(
            {
                "program_id": program.program_id,
                "category": program.category,
                "expected_click_value_yen": score.expected_click_value_yen,
                "eligible": audit.eligible,
            }
        )
        audits.append(
            {
                "program_id": program.program_id,
                "eligible": audit.eligible,
                "reasons": list(audit.reasons),
            }
        )

    opportunities.sort(key=lambda item: float(item["expected_click_value_yen"]), reverse=True)
    stages = [
        {"agent": "Opportunity Scout", "status": "draft", "output": opportunities},
        {"agent": "Compliance Auditor", "status": "draft", "output": audits},
        {
            "agent": "Diagnosis Builder",
            "status": "draft",
            "output": {"categories": list(diagnosis.categories)},
        },
        {
            "agent": "Content Repurposer",
            "status": "draft",
            "output": {"formats": ["seo_article", "youtube_script", "short_video", "pinterest_pin"]},
        },
        {
            "agent": "Analytics Optimizer",
            "status": "draft",
            "output": {"next_action": "collect_more_first_party_events"},
        },
    ]
    return {
        "status": "draft",
        "publish_allowed": False,
        "human_approval_received": human_approved,
        "stages": stages,
    }
