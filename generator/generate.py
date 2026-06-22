from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from slugify import slugify

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.prompts import draft_prompt, final_check_prompt, review_prompt

JST = timezone(timedelta(hours=9))
CLI_COMMANDS = {
    "claude": ["claude", "-p"],
    "gemini": ["gemini", "-p"],
    "codex": ["codex", "-q"],
}


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


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def load_topics(path: Path) -> list[Topic]:
    data = load_yaml(path)
    raw_topics = data.get("topics", [])
    if not isinstance(raw_topics, list) or not raw_topics:
        raise ValueError("topics.yaml must contain a non-empty 'topics' list")

    topics: list[Topic] = []
    for item in raw_topics:
        if not isinstance(item, dict):
            raise ValueError("Each topic entry must be a mapping")
        topic = str(item.get("topic", "")).strip()
        keywords = item.get("keywords", [])
        category = str(item.get("category", "")).strip()
        if not topic or not isinstance(keywords, list) or not category:
            raise ValueError(f"Invalid topic entry: {item}")
        topics.append(Topic(topic=topic, keywords=[str(k) for k in keywords], category=category))
    return topics


def state_path(root: Path) -> Path:
    return root / "generator" / ".state.json"


def load_state(root: Path) -> dict[str, Any]:
    path = state_path(root)
    if not path.exists():
        return {"next_index": 0, "history": []}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return {"next_index": 0, "history": []}
    return data


def save_state(root: Path, state: dict[str, Any]) -> None:
    path = state_path(root)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def select_topic(topics: list[Topic], state: dict[str, Any]) -> tuple[int, Topic]:
    raw_index = state.get("next_index", 0)
    try:
        index = int(raw_index) % len(topics)
    except (TypeError, ValueError):
        index = 0
    return index, topics[index]


def cloud_mode_enabled(explicit_cloud: bool = False) -> bool:
    return explicit_cloud or os.getenv("BLOG_EXECUTION_MODE", "").lower() == "cloud" or os.getenv("GITHUB_ACTIONS") == "true"


def get_push_branch(git_config: dict[str, Any] | None = None) -> str:
    git_config = git_config or {}
    return str(os.getenv("BLOG_GIT_BRANCH") or git_config.get("branch") or "main")


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


def run_ai_cli(cli_name: str, prompt: str, timeout: int) -> CliResult:
    if cli_name not in CLI_COMMANDS:
        return CliResult(False, cli_name, "", f"Unsupported CLI: {cli_name}")

    command = [*CLI_COMMANDS[cli_name], prompt]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        return CliResult(False, cli_name, "", f"CLI not found: {exc}")
    except subprocess.TimeoutExpired as exc:
        return CliResult(False, cli_name, exc.stdout or "", f"CLI timeout after {timeout}s: {exc}")
    except OSError as exc:
        return CliResult(False, cli_name, "", f"CLI execution error: {exc}")

    output = (completed.stdout or "").strip()
    error = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return CliResult(False, cli_name, output, error or f"returncode={completed.returncode}")
    if not output:
        return CliResult(False, cli_name, "", "CLI returned empty output")
    return CliResult(True, cli_name, output)


def call_with_fallback(cli_names: list[str], prompt: str, timeout: int, stage: str) -> CliResult:
    errors: list[str] = []
    for cli_name in cli_names:
        logging.info("%s: calling %s CLI", stage, cli_name)
        result = run_ai_cli(cli_name, prompt, timeout)
        if result.ok:
            logging.info("%s: %s CLI succeeded", stage, cli_name)
            return result
        errors.append(f"{cli_name}: {result.error}")
        logging.warning("%s: %s CLI failed: %s", stage, cli_name, result.error)
    return CliResult(False, ",".join(cli_names), "", " | ".join(errors))


def strip_front_matter(markdown: str) -> str:
    text = markdown.strip()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text


def clean_title(value: str) -> str:
    value = re.sub(r"^[#\s]+", "", value).strip()
    value = re.sub(r"[*_`]+", "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:90] or "無題の記事"


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return clean_title(stripped)
    return clean_title(fallback)


def remove_first_h1(markdown: str) -> str:
    lines = markdown.strip().splitlines()
    if lines and lines[0].lstrip().startswith("# "):
        return "\n".join(lines[1:]).strip()
    return markdown.strip()


def make_description(markdown: str, fallback: str, max_len: int = 150) -> str:
    for line in markdown.splitlines():
        text = line.strip()
        if not text or text.startswith("#") or text.startswith("-") or text.startswith("|"):
            continue
        text = re.sub(r"[*_`>#\[\]()]+", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            return text[:max_len]
    return fallback[:max_len]


def make_slug(title: str) -> str:
    slug = slugify(title, lowercase=True, max_length=80, word_boundary=True)
    if slug:
        return slug
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
    return f"post-{digest}"


def yaml_quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def build_post_markdown(article: str, topic: Topic, blog_config: dict[str, Any], now: datetime) -> tuple[str, str]:
    body = strip_front_matter(article)
    title = extract_title(body, topic.topic)
    body_without_h1 = remove_first_h1(body)
    description = make_description(body_without_h1, topic.topic)
    tags = list(dict.fromkeys([*topic.keywords, "AI", "不動産"]))
    category = topic.category or str(blog_config.get("default_category", "AI・テック"))

    front_matter = [
        "---",
        f"title: {yaml_quote(title)}",
        f"date: {now.isoformat(timespec='seconds')}",
        "draft: false",
        "tags:",
        *[f"  - {yaml_quote(tag)}" for tag in tags],
        "categories:",
        f"  - {yaml_quote(category)}",
        f"description: {yaml_quote(description)}",
        "---",
        "",
    ]
    return "\n".join(front_matter) + body_without_h1.strip() + "\n", title


def unique_post_path(posts_dir: Path, now: datetime, title: str) -> Path:
    base_name = f"{now:%Y-%m-%d}-{make_slug(title)}"
    candidate = posts_dir / f"{base_name}.md"
    suffix = 2
    while candidate.exists():
        candidate = posts_dir / f"{base_name}-{suffix}.md"
        suffix += 1
    return candidate


def save_post(root: Path, post_markdown: str, title: str, now: datetime) -> Path:
    posts_dir = root / "hugo-site" / "content" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    path = unique_post_path(posts_dir, now, title)
    path.write_text(post_markdown, encoding="utf-8")
    logging.info("Saved post: %s", path)
    return path


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

    run_git_command(root, ["add", "hugo-site/content/posts/", "generator/.state.json"])

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


def generate_article(root: Path, dry_run: bool = False, cloud: bool = False) -> Path | None:
    setup_logging(root)
    config = load_yaml(root / "generator" / "config.yaml")
    topics = load_topics(root / "generator" / "topics.yaml")
    state = load_state(root)
    index, topic = select_topic(topics, state)
    generation_config = config.get("generation", {})
    blog_config = config.get("blog", {})
    git_config = config.get("git", {})

    if cloud_mode_enabled(cloud):
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
    post_path = save_post(root, post_markdown, title, now)

    history = state.setdefault("history", [])
    if isinstance(history, list):
        history.append(
            {
                "date": now.isoformat(),
                "topic_index": index,
                "topic": topic.topic,
                "title": title,
                "path": str(post_path.relative_to(root)),
                "mode": "cloud" if cloud_mode_enabled(cloud) else "local",
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
