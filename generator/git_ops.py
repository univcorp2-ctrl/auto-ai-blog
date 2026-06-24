from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any


def get_push_branch(git_config: dict[str, Any] | None = None) -> str:
    git_config = git_config or {}
    return str(os.getenv("BLOG_GIT_BRANCH") or git_config.get("branch") or "main")


def run_git_command(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def git_has_changes(root: Path) -> bool:
    result = run_git_command(root, ["status", "--porcelain"])
    return bool(result.stdout.strip())


def commit_and_push(root: Path, title: str, git_config: dict[str, Any], dry_run: bool = False) -> None:
    if dry_run:
        logging.info("Dry run enabled; skipping git commit and push")
        return

    if not bool(git_config.get("auto_commit", True)):
        logging.info("git.auto_commit=false; skipping git commit")
        return

    add_paths = ["generator/.state.json", "generator/.manual_state.json"]
    sites_root = root / "sites"
    if sites_root.exists():
        add_paths.extend(
            str(path.relative_to(root)).replace("\\", "/")
            for path in sites_root.glob("*/content/posts")
            if path.exists()
        )
    legacy_posts = root / "hugo-site" / "content" / "posts"
    if legacy_posts.exists():
        add_paths.append(str(legacy_posts.relative_to(root)).replace("\\", "/"))

    run_git_command(root, ["add", *add_paths])

    if not git_has_changes(root):
        logging.info("No git changes to commit")
        return

    template = str(git_config.get("commit_message_template", "📝 新記事: {title}"))
    commit = run_git_command(root, ["commit", "-m", template.format(title=title)])
    if commit.returncode != 0:
        raise RuntimeError(f"git commit failed: {commit.stderr.strip()}")

    if not bool(git_config.get("auto_push", True)):
        logging.info("git.auto_push=false; skipping git push")
        return

    branch = get_push_branch(git_config)
    last_error = ""
    for attempt in range(1, 4):
        push = run_git_command(root, ["push", "origin", branch])
        if push.returncode == 0:
            logging.info("git push succeeded to origin/%s", branch)
            return
        last_error = push.stderr.strip() or push.stdout.strip()
        logging.warning("git push failed attempt %s/3: %s", attempt, last_error)
        if attempt < 3:
            time.sleep(5)
    raise RuntimeError(f"git push failed after 3 attempts: {last_error}")
