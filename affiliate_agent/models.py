from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping


@dataclass(frozen=True)
class AffiliateProgram:
    program_id: str
    name: str
    category: str
    reward_yen: float
    epc_yen: float
    approval_rate: float
    approval_days: int
    listing_policy: str
    sns_policy: str
    trademark_bidding_policy: str
    media_registration_status: str
    affiliate_url: str
    disclosure_text: str
    last_verified_at: date | None
    active: bool

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> AffiliateProgram:
        verified = str(data.get("last_verified_at", "")).strip()
        return cls(
            program_id=str(data["program_id"]),
            name=str(data["name"]),
            category=str(data["category"]),
            reward_yen=float(data["reward_yen"]),
            epc_yen=float(data["epc_yen"]),
            approval_rate=float(data["approval_rate"]),
            approval_days=int(data["approval_days"]),
            listing_policy=str(data["listing_policy"]),
            sns_policy=str(data["sns_policy"]),
            trademark_bidding_policy=str(data["trademark_bidding_policy"]),
            media_registration_status=str(data["media_registration_status"]),
            affiliate_url=str(data.get("affiliate_url", "")),
            disclosure_text=str(data.get("disclosure_text", "")),
            last_verified_at=date.fromisoformat(verified) if verified else None,
            active=bool(data.get("active", False)),
        )


@dataclass(frozen=True)
class ProgramScore:
    expected_approved_reward_yen: float
    expected_click_value_yen: float
    recommended_max_cpc_yen: float
    margin: float


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DiagnosisInput:
    mobile_monthly_yen: int
    mobile_lines: int
    internet_monthly_yen: int
    internet_type: str
    electricity_monthly_yen: int
    household_size: int
    contract_concerns: str = ""
    willing_to_switch: bool = False


@dataclass(frozen=True)
class DiagnosisResult:
    categories: tuple[str, ...]
    monthly_saving_low_yen: int
    monthly_saving_high_yen: int
    notes: tuple[str, ...]


@dataclass(frozen=True)
class Event:
    event_name: str
    occurred_at: datetime
    session_id: str
    variant_id: str
    payload: Mapping[str, Any]
