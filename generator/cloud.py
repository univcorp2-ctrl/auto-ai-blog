from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from generator.git_ops import run_git_command


def cloud_mode_enabled(explicit_cloud: bool = False) -> bool:
    return explicit_cloud or os.getenv("BLOG_EXECUTION_MODE", "").lower() == "cloud" or os.getenv("GITHUB_ACTIONS") == "true"


def configure_git_identity_for_cloud(root: Path) -> None:
    name = os.getenv("GIT_AUTHOR_NAME", "github-actions[bot]")
    email = os.getenv("GIT_AUTHOR_EMAIL", "41898282+github-actions[bot]@users.noreply.github.com")
    run_git_command(root, ["config", "user.name", name])
    run_git_command(root, ["config", "user.email", email])
    logging.info("Configured git identity for cloud mode: %s <%s>", name, email)


def log_cloud_environment() -> None:
    safe_env = {
        "BLOG_EXECUTION_MODE": os.getenv("BLOG_EXECUTION_MODE", ""),
        "GITHUB_ACTIONS": os.getenv("GITHUB_ACTIONS", ""),
        "GITHUB_WORKFLOW": os.getenv("GITHUB_WORKFLOW", ""),
        "GITHUB_RUN_ID": os.getenv("GITHUB_RUN_ID", ""),
        "BLOG_GIT_BRANCH": os.getenv("BLOG_GIT_BRANCH", ""),
    }
    logging.info("Cloud environment summary: %s", json.dumps(safe_env, ensure_ascii=False))
