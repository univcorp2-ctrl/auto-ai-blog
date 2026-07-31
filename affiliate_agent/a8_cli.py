from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from affiliate_agent.a8_ecsales import (
    A8ApiError,
    A8ConfigurationError,
    A8EcSalesClient,
    A8EcSalesConfig,
    A8MutationBlocked,
    A8Response,
    is_maintenance_window,
    summarize_sales,
)

CAPABILITIES = {
    "audience": "A8 advertiser / program owner",
    "read": [
        "unsealed sales list",
        "unsealed count by program",
        "unsealed counts by advertiser",
        "today sealed or cancelled sales",
        "today sealed count by program or advertiser",
        "sealed or cancelled sales from the previous 91 days",
    ],
    "write_guarded": [
        "modify an unsealed order",
        "decide an unsealed order",
        "cancel an unsealed order",
        "revive a decision or cancellation made today",
    ],
    "not_supported": [
        "affiliate program search",
        "publisher-side reward report retrieval",
        "affiliate link generation",
        "automatic partnership applications",
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m affiliate_agent.a8_cli",
        description="A8.net EC Sales API v3 client. Read-only unless mutations are doubly enabled.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("capabilities")
    subparsers.add_parser("doctor")

    unsealed = subparsers.add_parser("unsealed")
    _add_list_arguments(unsealed, include_date=True, include_click_date=True)

    subparsers.add_parser("unsealed-count")
    subparsers.add_parser("advertiser-unsealed-counts")

    today = subparsers.add_parser("sealed-today")
    _add_list_arguments(today, include_date=False, include_click_date=False)

    subparsers.add_parser("sealed-today-count")
    subparsers.add_parser("advertiser-sealed-today-counts")

    sealed = subparsers.add_parser("sealed")
    _add_list_arguments(sealed, include_date=True, include_click_date=False)

    decide = subparsers.add_parser("decide")
    _add_mutation_arguments(decide)

    cancel = subparsers.add_parser("cancel")
    _add_mutation_arguments(cancel)
    cancel.add_argument("--reason-code", type=int, required=True, choices=range(1, 7))

    revival = subparsers.add_parser("revival")
    _add_mutation_arguments(revival)

    modify = subparsers.add_parser("modify-single")
    _add_mutation_arguments(modify)
    modify.add_argument("--reason-code", type=int, required=True, choices=range(1, 7))
    modify.add_argument("--price", type=int)
    modify.add_argument("--quantity", type=int)

    modify_items = subparsers.add_parser("modify-items")
    _add_mutation_arguments(modify_items)
    modify_items.add_argument("--items-json", type=Path, required=True)
    return parser


def _add_list_arguments(
    parser: argparse.ArgumentParser,
    *,
    include_date: bool,
    include_click_date: bool,
) -> None:
    if include_date:
        parser.add_argument("--date", help="YYYYMMDD")
    parser.add_argument("--order-id")
    parser.add_argument("--order-no")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=1_000)
    if include_click_date:
        parser.add_argument("--include-click-date", action="store_true")
    parser.add_argument("--raw", action="store_true", help="include order and media identifiers")
    parser.add_argument("--output", type=Path)


def _add_mutation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--order-id", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--confirm",
        required=True,
        help="exact token: action:PROGRAM_ID:ORDER_ID",
    )
    parser.add_argument("--output", type=Path)


def _response_payload(response: A8Response, *, source: str, raw: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status_code": response.status_code,
        "message": response.message,
        "summary": summarize_sales(response, source=source),
    }
    if raw:
        payload["results"] = list(response.results)
    return payload


def _write_payload(payload: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if output is None:
        print(text)
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f"{text}\n", encoding="utf-8")
    print(json.dumps({"written": str(output), "contains_secret": False}, ensure_ascii=False))


def _load_client() -> A8EcSalesClient:
    return A8EcSalesClient(A8EcSalesConfig.from_env())


def _require_execute(args: argparse.Namespace) -> None:
    if not args.execute:
        raise A8MutationBlocked("write command requires --execute")


def _run_read(args: argparse.Namespace, client: A8EcSalesClient) -> tuple[A8Response, str]:
    if args.command == "unsealed":
        return (
            client.list_unsealed(
                date=args.date,
                order_id=args.order_id,
                order_no=args.order_no,
                offset=args.offset,
                limit=args.limit,
                include_click_date=args.include_click_date,
            ),
            "unsealed",
        )
    if args.command == "unsealed-count":
        return client.get_unsealed_count(), "unsealed-count"
    if args.command == "advertiser-unsealed-counts":
        return client.get_advertiser_unsealed_counts(), "advertiser-unsealed-counts"
    if args.command == "sealed-today":
        return (
            client.list_today_sealed(
                order_id=args.order_id,
                order_no=args.order_no,
                offset=args.offset,
                limit=args.limit,
            ),
            "sealed-today",
        )
    if args.command == "sealed-today-count":
        return client.get_today_sealed_count(), "sealed-today-count"
    if args.command == "advertiser-sealed-today-counts":
        return client.get_advertiser_today_sealed_counts(), "advertiser-sealed-today-counts"
    if args.command == "sealed":
        return (
            client.list_sealed(
                date=args.date,
                order_id=args.order_id,
                order_no=args.order_no,
                offset=args.offset,
                limit=args.limit,
            ),
            "sealed",
        )
    raise ValueError(f"unsupported read command: {args.command}")


def _run_mutation(args: argparse.Namespace, client: A8EcSalesClient) -> A8Response:
    _require_execute(args)
    if args.command == "decide":
        return client.decide(args.order_id, confirmation=args.confirm)
    if args.command == "cancel":
        return client.cancel(
            args.order_id,
            reason_code=args.reason_code,
            confirmation=args.confirm,
        )
    if args.command == "revival":
        return client.revival(args.order_id, confirmation=args.confirm)
    if args.command == "modify-single":
        return client.modify_single(
            args.order_id,
            reason_code=args.reason_code,
            confirmation=args.confirm,
            price=args.price,
            quantity=args.quantity,
        )
    if args.command == "modify-items":
        items = json.loads(args.items_json.read_text(encoding="utf-8"))
        if not isinstance(items, list):
            raise ValueError("items JSON must be an array")
        return client.modify_items(args.order_id, items=items, confirmation=args.confirm)
    raise ValueError(f"unsupported mutation command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "capabilities":
        _write_payload(CAPABILITIES, None)
        return 0
    if args.command == "doctor":
        try:
            config = A8EcSalesConfig.from_env()
        except A8ConfigurationError as error:
            _write_payload(
                {
                    "configured": False,
                    "error": str(error),
                    "maintenance_window": is_maintenance_window(),
                },
                None,
            )
            return 2
        _write_payload(
            {
                "configured": True,
                "program_id_configured": bool(config.program_id),
                "advertiser_id_configured": config.advertiser_id is not None,
                "api_key_configured": bool(config.api_key),
                "mutations_enabled": config.allow_mutations,
                "maintenance_window": is_maintenance_window(),
                "base_url": config.base_url,
            },
            None,
        )
        return 0

    try:
        client = _load_client()
        mutation_commands = {"decide", "cancel", "revival", "modify-single", "modify-items"}
        if args.command in mutation_commands:
            response = _run_mutation(args, client)
            _write_payload(
                {
                    "status_code": response.status_code,
                    "message": response.message,
                    "action": args.command,
                    "order_id": args.order_id,
                },
                args.output,
            )
        else:
            response, source = _run_read(args, client)
            _write_payload(
                _response_payload(response, source=source, raw=args.raw),
                args.output,
            )
    except (A8ApiError, A8ConfigurationError, A8MutationBlocked, OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
