from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from datetime import time as clock_time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

A8_BASE_URL = "https://ecsales-api.a8.net/v3"
A8_SUCCESS_CODE = 10000
JST = ZoneInfo("Asia/Tokyo")
DATE_PATTERN = re.compile(r"^\d{8}$")
REASON_CODES = {1, 2, 3, 4, 5, 6}


class A8ConfigurationError(ValueError):
    """Raised when required A8 configuration is missing or malformed."""


class A8MutationBlocked(RuntimeError):
    """Raised when a write operation is not explicitly enabled and confirmed."""


class A8ApiError(RuntimeError):
    """Raised when the HTTP request or A8 response reports a failure."""

    def __init__(self, status_code: int | None, message: str) -> None:
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True)
class A8EcSalesConfig:
    program_id: str
    api_key: str
    advertiser_id: str | None = None
    base_url: str = A8_BASE_URL
    timeout_seconds: float = 20.0
    calls_per_minute: int = 240
    allow_mutations: bool = False
    block_maintenance_window: bool = True

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> A8EcSalesConfig:
        values = environ or os.environ
        program_id = values.get("A8_EC_PROGRAM_ID", "").strip()
        api_key = values.get("A8_EC_API_KEY", "").strip()
        advertiser_id = values.get("A8_EC_ADVERTISER_ID", "").strip() or None
        if not program_id:
            raise A8ConfigurationError("A8_EC_PROGRAM_ID is required")
        if not api_key:
            raise A8ConfigurationError("A8_EC_API_KEY is required")
        _validate_identifier("program_id", program_id, 15)
        if advertiser_id is not None:
            _validate_identifier("advertiser_id", advertiser_id, 12)
        return cls(
            program_id=program_id,
            api_key=api_key,
            advertiser_id=advertiser_id,
            base_url=values.get("A8_EC_BASE_URL", A8_BASE_URL).rstrip("/"),
            timeout_seconds=float(values.get("A8_EC_TIMEOUT_SECONDS", "20")),
            calls_per_minute=int(values.get("A8_EC_CALLS_PER_MINUTE", "240")),
            allow_mutations=_as_bool(values.get("A8_EC_MUTATIONS_ENABLED", "false")),
            block_maintenance_window=_as_bool(values.get("A8_EC_BLOCK_MAINTENANCE_WINDOW", "true")),
        )


@dataclass(frozen=True)
class A8Response:
    status_code: int
    message: str
    results: tuple[Mapping[str, Any], ...]


class JsonTransport(Protocol):
    def request(
        self,
        *,
        method: str,
        url: str,
        query: Mapping[str, Any] | None,
        body: Mapping[str, Any] | None,
        timeout_seconds: float,
    ) -> Mapping[str, Any]: ...


class StdlibJsonTransport:
    def request(
        self,
        *,
        method: str,
        url: str,
        query: Mapping[str, Any] | None,
        body: Mapping[str, Any] | None,
        timeout_seconds: float,
    ) -> Mapping[str, Any]:
        target = url
        query_values = _drop_empty(query or {})
        if query_values:
            target = f"{target}?{urlencode(query_values)}"
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            target,
            data=payload,
            method=method,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "auto-ai-blog-a8-client/1.0",
            },
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(response_body)
            except json.JSONDecodeError as parse_error:
                raise A8ApiError(error.code, "A8 HTTP request failed") from parse_error
            if isinstance(parsed, dict):
                return parsed
            raise A8ApiError(error.code, "A8 HTTP response was not a JSON object") from error
        except URLError as error:
            raise A8ApiError(None, "A8 network request failed") from error

        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError as error:
            raise A8ApiError(None, "A8 response was not valid JSON") from error
        if not isinstance(parsed, dict):
            raise A8ApiError(None, "A8 response was not a JSON object")
        return parsed


class RateLimiter:
    def __init__(self, calls_per_minute: int) -> None:
        if calls_per_minute < 1:
            raise A8ConfigurationError("calls_per_minute must be at least 1")
        self._minimum_interval = 60.0 / calls_per_minute
        self._last_call = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._minimum_interval:
            time.sleep(self._minimum_interval - elapsed)
        self._last_call = time.monotonic()


class A8EcSalesClient:
    def __init__(
        self,
        config: A8EcSalesConfig,
        *,
        transport: JsonTransport | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        _validate_identifier("program_id", config.program_id, 15)
        if config.advertiser_id is not None:
            _validate_identifier("advertiser_id", config.advertiser_id, 12)
        if not config.api_key:
            raise A8ConfigurationError("api_key is required")
        self.config = config
        self.transport = transport or StdlibJsonTransport()
        self.rate_limiter = rate_limiter or RateLimiter(config.calls_per_minute)

    def list_unsealed(
        self,
        *,
        date: str | None = None,
        order_id: str | None = None,
        order_no: str | None = None,
        offset: int = 0,
        limit: int = 1_000,
        include_click_date: bool = False,
    ) -> A8Response:
        _validate_list_parameters(date=date, order_id=order_id, offset=offset, limit=limit)
        return self._get_program(
            "unsealed",
            {
                "date": date,
                "order_id": order_id,
                "order_no": order_no,
                "offset": offset,
                "limit": limit,
                "optional_fields": "order_click_date" if include_click_date else None,
            },
        )

    def get_unsealed_count(self) -> A8Response:
        return self._get_program("unsealed/count")

    def get_advertiser_unsealed_counts(self) -> A8Response:
        return self._get_advertiser("unsealed/count")

    def list_today_sealed(
        self,
        *,
        order_id: str | None = None,
        order_no: str | None = None,
        offset: int = 0,
        limit: int = 1_000,
    ) -> A8Response:
        _validate_list_parameters(order_id=order_id, offset=offset, limit=limit)
        return self._get_program(
            "sealed/today",
            {
                "order_id": order_id,
                "order_no": order_no,
                "offset": offset,
                "limit": limit,
            },
        )

    def get_today_sealed_count(self) -> A8Response:
        return self._get_program("sealed/today/count")

    def get_advertiser_today_sealed_counts(self) -> A8Response:
        return self._get_advertiser("sealed/today/count")

    def list_sealed(
        self,
        *,
        date: str | None = None,
        order_id: str | None = None,
        order_no: str | None = None,
        offset: int = 0,
        limit: int = 1_000,
    ) -> A8Response:
        _validate_list_parameters(date=date, order_id=order_id, offset=offset, limit=limit)
        return self._get_program(
            "sealed",
            {
                "date": date,
                "order_id": order_id,
                "order_no": order_no,
                "offset": offset,
                "limit": limit,
            },
        )

    def decide(self, order_id: str, *, confirmation: str) -> A8Response:
        return self._post_order("decide", order_id, {}, confirmation=confirmation)

    def cancel(
        self,
        order_id: str,
        *,
        reason_code: int,
        confirmation: str,
    ) -> A8Response:
        _validate_reason_code(reason_code)
        return self._post_order(
            "cancel",
            order_id,
            {"reason_code": reason_code},
            confirmation=confirmation,
        )

    def revival(self, order_id: str, *, confirmation: str) -> A8Response:
        return self._post_order("revival", order_id, {}, confirmation=confirmation)

    def modify_single(
        self,
        order_id: str,
        *,
        reason_code: int,
        confirmation: str,
        price: int | None = None,
        quantity: int | None = None,
    ) -> A8Response:
        _validate_reason_code(reason_code)
        if price is None and quantity is None:
            raise ValueError("price or quantity is required")
        body: dict[str, Any] = {"reason_code": reason_code}
        if price is not None:
            body["price"] = price
        if quantity is not None:
            body["quantity"] = quantity
        return self._post_order("modify", order_id, body, confirmation=confirmation)

    def modify_items(
        self,
        order_id: str,
        *,
        items: Sequence[Mapping[str, Any]],
        confirmation: str,
    ) -> A8Response:
        if not items:
            raise ValueError("items must not be empty")
        normalized: list[dict[str, Any]] = []
        for item in items:
            code = str(item.get("code", "")).strip()
            reason_code = int(item.get("reason_code", 0))
            _validate_reason_code(reason_code)
            if not code:
                raise ValueError("each item requires code")
            if item.get("price") is None and item.get("quantity") is None:
                raise ValueError("each item requires price or quantity")
            row: dict[str, Any] = {"code": code, "reason_code": reason_code}
            if item.get("price") is not None:
                row["price"] = item["price"]
            if item.get("quantity") is not None:
                row["quantity"] = item["quantity"]
            normalized.append(row)
        return self._post_order(
            "modify",
            order_id,
            {"items": normalized},
            confirmation=confirmation,
        )

    def _get_program(
        self,
        path: str,
        query: Mapping[str, Any] | None = None,
    ) -> A8Response:
        request_query = dict(query or {})
        request_query["api_key"] = self.config.api_key
        return self._request(
            method="GET",
            url=f"{self.config.base_url}/ins/{self.config.program_id}/{path}",
            query=request_query,
            body=None,
        )

    def _get_advertiser(self, path: str) -> A8Response:
        if self.config.advertiser_id is None:
            raise A8ConfigurationError("A8_EC_ADVERTISER_ID is required for advertiser endpoints")
        return self._request(
            method="GET",
            url=f"{self.config.base_url}/sp/{self.config.advertiser_id}/{path}",
            query={"api_key": self.config.api_key},
            body=None,
        )

    def _post_order(
        self,
        action: str,
        order_id: str,
        body: Mapping[str, Any],
        *,
        confirmation: str,
    ) -> A8Response:
        _validate_identifier("order_id", order_id, 12)
        expected = f"{action}:{self.config.program_id}:{order_id}"
        if not self.config.allow_mutations:
            raise A8MutationBlocked("A8_EC_MUTATIONS_ENABLED is false")
        if confirmation != expected:
            raise A8MutationBlocked(f"confirmation must equal {expected}")
        request_body = dict(body)
        request_body["api_key"] = self.config.api_key
        return self._request(
            method="POST",
            url=(f"{self.config.base_url}/ins/{self.config.program_id}/order/{order_id}/{action}"),
            query=None,
            body=request_body,
        )

    def _request(
        self,
        *,
        method: str,
        url: str,
        query: Mapping[str, Any] | None,
        body: Mapping[str, Any] | None,
    ) -> A8Response:
        if self.config.block_maintenance_window and is_maintenance_window():
            raise A8ApiError(None, "A8 maintenance window guard is active")
        self.rate_limiter.wait()
        payload = self.transport.request(
            method=method,
            url=url,
            query=query,
            body=body,
            timeout_seconds=self.config.timeout_seconds,
        )
        status_code = int(payload.get("status_code", 0))
        message = str(payload.get("message", ""))
        if status_code != A8_SUCCESS_CODE:
            raise A8ApiError(status_code, message or "A8 API returned an error")
        raw_results = payload.get("results", [])
        if raw_results is None:
            raw_results = []
        if not isinstance(raw_results, list):
            raise A8ApiError(status_code, "A8 results field was not a list")
        results = tuple(item for item in raw_results if isinstance(item, dict))
        return A8Response(status_code=status_code, message=message, results=results)


def summarize_sales(
    response: A8Response,
    *,
    source: str,
) -> dict[str, int | float | str]:
    records = len(response.results)
    order_count = sum(int(row.get("order_count", 0) or 0) for row in response.results)
    order_money = sum(float(row.get("order_money", 0) or 0) for row in response.results)
    pay_money = sum(float(row.get("pay_money", 0) or 0) for row in response.results)
    approved = sum(1 for row in response.results if int(row.get("decide_flg", 0) or 0) == 1)
    return {
        "source": source,
        "records": records,
        "order_count": order_count,
        "order_money_yen": round(order_money, 2),
        "pay_money_yen": round(pay_money, 2),
        "approved_records": approved,
        "non_approved_records": records - approved,
    }


def is_maintenance_window(now: datetime | None = None) -> bool:
    current = (now or datetime.now(JST)).astimezone(JST).time()
    return current >= clock_time(23, 30) or current < clock_time(1, 0)


def _drop_empty(values: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value not in {None, ""}}


def _as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _validate_identifier(name: str, value: str, length: int) -> None:
    if len(value) != length:
        raise A8ConfigurationError(f"{name} must be {length} characters")


def _validate_date(value: str | None) -> None:
    if value is not None and DATE_PATTERN.fullmatch(value) is None:
        raise ValueError("date must use YYYYMMDD")


def _validate_reason_code(value: int) -> None:
    if value not in REASON_CODES:
        raise ValueError("reason_code must be between 1 and 6")


def _validate_list_parameters(
    *,
    date: str | None = None,
    order_id: str | None = None,
    offset: int = 0,
    limit: int = 1_000,
) -> None:
    _validate_date(date)
    if order_id is not None:
        _validate_identifier("order_id", order_id, 12)
    if offset < 0:
        raise ValueError("offset must be non-negative")
    if not 1 <= limit <= 10_000:
        raise ValueError("limit must be between 1 and 10000")
