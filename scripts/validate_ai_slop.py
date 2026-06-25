from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.slop_guard import evaluate_markdown, load_guidelines


def iter_targets(root: Path, paths: list[Path], *, content_kind: str) -> list[Path]:
    if paths:
        return [path if path.is_absolute() else root / path for path in paths]
    targets: list[Path] = []
    for site in (root / "sites").iterdir():
        content = site / "content"
        if not content.exists():
            continue
        for path in content.rglob("*.md"):
            if path.name == "_index.md":
                continue
            if content_kind == "all" or content_kind in path.parts:
                targets.append(path)
    return sorted(targets)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Markdown content against Notion-derived AI slop rules.")
    parser.add_argument("paths", nargs="*", type=Path, help="Markdown files to validate. Defaults to all posts and manuals.")
    parser.add_argument("--content-kind", default="all", choices=["all", "posts", "manuals"])
    parser.add_argument("--json-report", type=Path, help="Write a JSON report to this path.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    guidelines = load_guidelines(root)
    rows = []
    failed = []
    for path in iter_targets(root, args.paths, content_kind=args.content_kind):
        report = evaluate_markdown(path.read_text(encoding="utf-8"), guidelines)
        row = {"path": str(path.relative_to(root)), **report.to_dict()}
        rows.append(row)
        if not report.passed:
            failed.append(row)
        print(f"{'PASS' if report.passed else 'FAIL'} {report.score}/{report.minimum_score} {path.relative_to(root)}")

    if args.json_report:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
