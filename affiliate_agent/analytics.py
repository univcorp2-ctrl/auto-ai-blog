from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from affiliate_agent.models import Event

ALLOWED_EVENTS = {
    "page_view",
    "diagnosis_start",
    "diagnosis_complete",
    "offer_impression",
    "affiliate_click",
}
FORBIDDEN_PAYLOAD_KEYS = {
    "address",
    "email",
    "full_name",
    "name",
    "phone",
    "postal_code",
}


def make_event(
    event_name: str,
    *,
    session_id: str,
    variant_id: str,
    payload: Mapping[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> Event:
    if event_name not in ALLOWED_EVENTS:
        raise ValueError(f"unsupported event: {event_name}")
    if not session_id.strip() or not variant_id.strip():
        raise ValueError("session_id and variant_id are required")
    event_payload = dict(payload or {})
    payload_keys = {str(key).lower() for key in event_payload}
    if payload_keys & FORBIDDEN_PAYLOAD_KEYS:
        raise ValueError("payload contains personal information fields")
    return Event(
        event_name=event_name,
        occurred_at=occurred_at or datetime.now(timezone.utc),
        session_id=session_id,
        variant_id=variant_id,
        payload=event_payload,
    )


def aggregate_events(events: Sequence[Event]) -> dict[str, float | int]:
    counts = {event_name: 0 for event_name in ALLOWED_EVENTS}
    expected_revenue = 0.0
    for event in events:
        counts[event.event_name] += 1
        if event.event_name == "affiliate_click":
            expected_revenue += float(event.payload.get("expected_approved_reward_yen", 0))

    starts = counts["diagnosis_start"]
    completions = counts["diagnosis_complete"]
    impressions = counts["offer_impression"]
    clicks = counts["affiliate_click"]
    return {
        **counts,
        "diagnosis_completion_rate": round(completions / starts, 4) if starts else 0.0,
        "offer_ctr": round(clicks / impressions, 4) if impressions else 0.0,
        "simulated_expected_approved_revenue_yen": round(expected_revenue, 2),
    }


def events_to_csv(events: Sequence[Event]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["event_name", "occurred_at", "session_id", "variant_id", "payload_json"],
    )
    writer.writeheader()
    for event in events:
        writer.writerow(
            {
                "event_name": event.event_name,
                "occurred_at": event.occurred_at.isoformat(),
                "session_id": event.session_id,
                "variant_id": event.variant_id,
                "payload_json": json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
            }
        )
    return output.getvalue()
