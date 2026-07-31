from __future__ import annotations

from affiliate_agent.models import AffiliateProgram, ProgramScore

DEFAULT_MARGIN = 0.55


def score_program(program: AffiliateProgram, margin: float = DEFAULT_MARGIN) -> ProgramScore:
    if not 0 <= program.approval_rate <= 1:
        raise ValueError("approval_rate must be between 0 and 1")
    if not 0 < margin <= 1:
        raise ValueError("margin must be greater than 0 and at most 1")
    if program.reward_yen < 0 or program.epc_yen < 0:
        raise ValueError("reward_yen and epc_yen must be non-negative")

    expected_reward = program.reward_yen * program.approval_rate
    expected_click_value = program.epc_yen * program.approval_rate
    recommended_cpc = expected_click_value * margin
    return ProgramScore(
        expected_approved_reward_yen=round(expected_reward, 2),
        expected_click_value_yen=round(expected_click_value, 2),
        recommended_max_cpc_yen=round(recommended_cpc, 2),
        margin=margin,
    )
