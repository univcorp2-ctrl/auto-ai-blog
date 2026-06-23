from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    topic: str
    keywords: list[str]
    category: str


@dataclass(frozen=True)
class CliResult:
    ok: bool
    cli_name: str
    output: str
    error: str = ""
