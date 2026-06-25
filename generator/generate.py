from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.cli_runner import CLI_COMMANDS, call_with_fallback, run_ai_cli
from generator.cloud import cloud_mode_enabled, configure_git_identity_for_cloud, log_cloud_environment
from generator.config_loader import load_state, load_topics, load_yaml, save_state, select_topic
from generator.git_ops import commit_and_push, get_push_branch, git_has_changes, run_git_command
from generator.markdown_post import (
    build_post_markdown,
    clean_title,
    extract_title,
    make_description,
    make_slug,
    remove_first_h1,
    save_post,
    strip_front_matter,
    unique_post_path,
    yaml_quote,
)
from generator.models import CliResult, Topic
from generator.prompts import draft_prompt, final_check_prompt, review_prompt
from generator.runtime import JST, repo_root, setup_logging
from generator.slop_guard import assert_not_slop, load_guidelines

__all__ = [
    "CLI_COMMANDS",
    "CliResult",
    "Topic",
    "build_post_markdown",
    "call_with_fallback",
    "clean_title",
    "cloud_mode_enabled",
    "commit_and_push",
    "configure_git_identity_for_cloud",
    "extract_title",
    "generate_article",
    "get_push_branch",
    "git_has_changes",
    "load_state",
    "load_topics",
    "load_yaml",
    "log_cloud_environment",
    "make_description",
    "make_slug",
    "remove_first_h1",
    "repo_root",
    "run_ai_cli",
    "run_git_command",
    "save_post",
    "save_state",
    "select_topic",
    "setup_logging",
    "strip_front_matter",
    "unique_post_path",
    "yaml_quote",
]


def generate_article(root: Path, dry_run: bool = False, cloud: bool = False) -> Path | None:
    setup_logging(root)
    config = load_yaml(root / "generator" / "config.yaml")
    topics = load_topics(root / "generator" / "topics.yaml")
    state = load_state(root)
    index, topic = select_topic(topics, state)
    generation_config = config.get("generation", {})
    blog_config = config.get("blog", {})
    git_config = config.get("git", {})

    is_cloud = cloud_mode_enabled(cloud)
    if is_cloud:
        log_cloud_environment()
        configure_git_identity_for_cloud(root)

    timeout = int(generation_config.get("cli_timeout_seconds", 120))
    min_chars = int(generation_config.get("min_chars", 2000))
    max_chars = int(generation_config.get("max_chars", 3000))
    priority = [str(cli) for cli in generation_config.get("cli_priority", ["claude", "gemini", "codex"])]

    logging.info("Selected topic %s/%s: %s", index + 1, len(topics), topic.topic)

    draft = call_with_fallback(
        priority,
        draft_prompt(topic.topic, topic.keywords, min_chars, max_chars),
        timeout,
        "draft",
    )
    if not draft.ok:
        logging.error("All draft CLIs failed; skipping article generation: %s", draft.error)
        return None

    improved_result = call_with_fallback(["gemini", "codex"], review_prompt(draft.output), timeout, "review")
    improved = improved_result.output if improved_result.ok else draft.output
    if not improved_result.ok:
        logging.warning("Review stage failed; using draft: %s", improved_result.error)

    final_result = call_with_fallback(["codex"], final_check_prompt(improved), timeout, "final_check")
    final_article = final_result.output if final_result.ok else improved
    if not final_result.ok:
        logging.warning("Final check failed; using improved article: %s", final_result.error)

    now = datetime.now(JST).replace(microsecond=0)
    post_markdown, title = build_post_markdown(final_article, topic, blog_config, now)
    assert_not_slop(post_markdown, load_guidelines(root))
    post_path = save_post(root, post_markdown, title, now, topic, blog_config)

    history = state.setdefault("history", [])
    if isinstance(history, list):
        history.append(
            {
                "date": now.isoformat(),
                "topic_index": index,
                "topic": topic.topic,
                "title": title,
                "path": str(post_path.relative_to(root)),
                "mode": "cloud" if is_cloud else "local",
            }
        )
        del history[:-90]
    state["next_index"] = (index + 1) % len(topics)
    save_state(root, state)

    commit_and_push(root, title, git_config, dry_run=dry_run)
    return post_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a Hugo blog post using local or cloud AI CLIs only.")
    parser.add_argument("--dry-run", action="store_true", help="Generate a post but skip git commit and push.")
    parser.add_argument("--cloud", action="store_true", help="Enable cloud execution mode defaults for GitHub Actions or cloud runners.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    try:
        result = generate_article(root, dry_run=args.dry_run, cloud=args.cloud)
    except Exception as exc:
        setup_logging(root)
        logging.exception("Article generation failed: %s", exc)
        return 1
    if result is None:
        return 2
    logging.info("Article generation completed: %s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
