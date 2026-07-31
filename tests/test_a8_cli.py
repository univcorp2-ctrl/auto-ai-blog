from __future__ import annotations

import json

from affiliate_agent import a8_cli
from affiliate_agent.a8_ecsales import A8Response


class FakeReadClient:
    def get_unsealed_count(self) -> A8Response:
        return A8Response(
            status_code=10000,
            message="ok",
            results=(
                {"ins_id": "s11111111111111", "count": 12},
                {"ins_id": "s22222222222222", "count": 8},
            ),
        )


def test_capabilities_does_not_require_credentials(capsys: object) -> None:
    assert a8_cli.main(["capabilities"]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["audience"] == "A8 advertiser / program owner"
    assert "publisher-side reward report retrieval" in output["not_supported"]


def test_count_command_reports_total_without_identifiers(
    monkeypatch: object,
    capsys: object,
) -> None:
    monkeypatch.setattr(a8_cli, "_load_client", FakeReadClient)  # type: ignore[attr-defined]
    assert a8_cli.main(["unsealed-count"]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["summary"]["count"] == 20
    assert output["summary"]["programs"] == 2
    assert "results" not in output
    assert "s11111111111111" not in json.dumps(output)


def test_count_command_includes_program_ids_only_with_raw(
    monkeypatch: object,
    capsys: object,
) -> None:
    monkeypatch.setattr(a8_cli, "_load_client", FakeReadClient)  # type: ignore[attr-defined]
    assert a8_cli.main(["unsealed-count", "--raw"]) == 0
    output = json.loads(capsys.readouterr().out)  # type: ignore[attr-defined]
    assert output["results"][0]["ins_id"] == "s11111111111111"
