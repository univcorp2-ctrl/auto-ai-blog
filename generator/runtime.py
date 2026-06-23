from __future__ import annotations

import logging
import sys
from datetime import timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def setup_logging(root: Path) -> None:
    log_dir = root / "generator" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "generate.log", encoding="utf-8"),
        ],
        force=True,
    )
