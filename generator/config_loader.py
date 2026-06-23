from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from generator.models import Topic


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
