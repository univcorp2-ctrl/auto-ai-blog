from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from affiliate_agent.a8_ecsales import (
    A8ApiError,
    A8ConfigurationError,
    A8EcSalesClient,
    A8EcSalesConfig,
    A8MutationBlocked,
    is_maintenance_window,
    summarize_sales,
)

JST = ZoneInfo("Asia/Tokyo")
PROGRAM_ID = "s12345678901234"
ADVERTISER_ID = "s12345678901"
ORDER_ID = "123456789012"
API_KEY = "top-secret-a8-key"


class NoopRateLimiter:
    def wait(self) -> None:
        return None


class FakeTransport:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def request(
        self,
        *,
        method: str,
        url: str,
        query: dict[str, Any] | None,
        body: dict[str, Any] | None,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "method": method,
                "url": url,
                "query": query,
                "body": body,
                "timeout_seconds": timeout_seconds,
            }
        )
        return self.response


def make_config(**overrides: object) -> A8EcSalesConfig:
    values: dict[str, object] = {
        "program_id": PROGRAM_ID,
        "api_key": API_KEY,
        "advertiser_id": ADVERTISER_ID,
        "block_maintenance_window": False,
    }
    values.update(overrides)
    return A8EcSalesConfig(**values)  # type: ignore[arg-type]


def make_client(
    response: dict[str, Any],
    **config_overrides: object,
) -> tuple[A8EcSalesClient, FakeTransport]:
    transport = FakeTransport(response)
    client = A8EcSalesClient(
        make_config(**config_overrides),
        transport=transport,
        rate_limiter=NoopRateLimiter(),  # type: ignore[arg-type]
    )
    return client, transport


def test_config_from_env_requires_program_and_secret() -> None:
    with pytest.raises(A8ConfigurationError):
        A8EcSalesConfig.from_env({"A8_EC_PROGRAM_ID": PROGRAM_ID})

    config = A8EcSalesConfig.from_env(
        {
            "A8_EC_PROGRAM_ID": PROGRAM_ID,
            "A8_EC_API_KEY": API_KEY,
            "A8_EC_ADVERTISER_ID": ADVERTISER_ID,
            "A8_EC_MUTATIONS_ENABLED": "false",
        }
    )
    assert config.program_id == PROGRAM_ID
    assert config.api_key == API_KEY
    assert config.allow_mutations is False


def test_read_request_places_key_in_query_but_summary_redacts_identifiers() -> None:
    client, transport = make_client(
        {
            "status_code": 10000,
            "message": "ok",
            "results": [
                {
                    "as_id": "a00000000000",
                    "order_id": ORDER_ID,
                    "website_name": "private media name",
                    "order_count": 2,
                    "order_money": 20_000,
                    "pay_money": 4_000,
                    "decide_flg": 0,
                }
            ],
        }
    )

    response = client.list_unsealed(date="20260731", limit=100)
    call = transport.calls[0]
    assert call["method"] == "GET"
    assert call["query"]["api_key"] == API_KEY
    assert call["query"]["date"] == "20260731"
    assert call["body"] is None

    summary = summarize_sales(response, source="unsealed")
    assert summary["records"] == 1
    assert summary["order_count"] == 2
    assert summary["pay_money_yen"] == 4_000
    serialized = repr(summary)
    assert ORDER_ID not in serialized
    assert "private media name" not in serialized
    assert API_KEY not in serialized


def test_a8_error_never_includes_api_key() -> None:
    client, _transport = make_client(
        {"status_code": 10004, "message": "認証に失敗しました。"}
    )
    with pytest.raises(A8ApiError) as captured:
        client.get_unsealed_count()
    assert captured.value.status_code == 10004
    assert API_KEY not in str(captured.value)


def test_mutation_is_blocked_without_environment_flag() -> None:
    client, transport = make_client({"status_code": 10000, "message": "ok"})
    confirmation = f"decide:{PROGRAM_ID}:{ORDER_ID}"
    with pytest.raises(A8MutationBlocked):
        client.decide(ORDER_ID, confirmation=confirmation)
    assert transport.calls == []


def test_mutation_requires_exact_confirmation_and_sends_key_in_json() -> None:
    client, transport = make_client(
        {"status_code": 10000, "message": "ok"},
        allow_mutations=True,
    )
    with pytest.raises(A8MutationBlocked):
        client.cancel(ORDER_ID, reason_code=2, confirmation="wrong")

    confirmation = f"cancel:{PROGRAM_ID}:{ORDER_ID}"
    response = client.cancel(ORDER_ID, reason_code=2, confirmation=confirmation)
    assert response.status_code == 10000
    call = transport.calls[0]
    assert call["method"] == "POST"
    assert call["query"] is None
    assert call["body"] == {"reason_code": 2, "api_key": API_KEY}


def test_list_validation_prevents_invalid_requests() -> None:
    client, transport = make_client({"status_code": 10000, "message": "ok"})
    with pytest.raises(ValueError):
        client.list_unsealed(date="2026-07-31")
    with pytest.raises(ValueError):
        client.list_unsealed(limit=10_001)
    with pytest.raises(A8ConfigurationError):
        client.list_unsealed(order_id="too-short")
    assert transport.calls == []


def test_documented_maintenance_window_is_detected_in_jst() -> None:
    assert is_maintenance_window(datetime(2026, 7, 31, 23, 45, tzinfo=JST)) is True
    assert is_maintenance_window(datetime(2026, 8, 1, 0, 30, tzinfo=JST)) is True
    assert is_maintenance_window(datetime(2026, 8, 1, 1, 1, tzinfo=JST)) is False
