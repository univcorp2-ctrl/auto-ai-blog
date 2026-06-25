from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from generator.config_loader import load_yaml
from generator.deploy_config import CloudflarePagesSite, load_cloudflare_pages_sites
from generator.runtime import repo_root


def run_command(root: Path, args: list[str]) -> None:
    result = subprocess.run(resolve_command(args), cwd=root, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {' '.join(args)}")


def resolve_command(args: list[str]) -> list[str]:
    if not args:
        return args
    executable = args[0]
    candidates = [executable]
    if os.name == "nt" and not executable.lower().endswith((".exe", ".cmd", ".bat")):
        candidates = [f"{executable}.cmd", f"{executable}.exe", executable]

    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return [resolved, *args[1:]]
    return args


def build_site(root: Path, site: CloudflarePagesSite) -> None:
    run_command(root, ["hugo", "--source", str(site.source_dir), "--gc", "--minify"])


def deploy_site(root: Path, site: CloudflarePagesSite) -> None:
    public_dir = root / site.public_dir
    if not public_dir.exists():
        raise FileNotFoundError(f"Public directory not found: {public_dir}")
    run_command(
        root,
        [
            "npx",
            "wrangler",
            "pages",
            "deploy",
            str(site.public_dir),
            "--project-name",
            site.project_name,
            "--branch",
            "main",
            "--commit-dirty=true",
        ],
    )


def select_sites(sites: list[CloudflarePagesSite], site_names: list[str]) -> list[CloudflarePagesSite]:
    if not site_names:
        return sites
    requested = set(site_names)
    selected = [site for site in sites if site.project_name in requested or site.source_dir.name in requested]
    missing = requested - {site.project_name for site in selected} - {site.source_dir.name for site in selected}
    if missing:
        raise ValueError(f"Unknown site name(s): {', '.join(sorted(missing))}")
    return selected


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and deploy configured Hugo sites to Cloudflare Pages.")
    parser.add_argument("--site", action="append", default=[], help="Project name or local site directory name to deploy.")
    parser.add_argument("--skip-build", action="store_true", help="Deploy existing public directories without rebuilding.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    config = load_yaml(root / "generator" / "config.yaml")
    sites = select_sites(load_cloudflare_pages_sites(config), args.site)
    if not sites:
        print("No Cloudflare Pages sites are enabled in generator/config.yaml.", file=sys.stderr)
        return 1

    for site in sites:
        print(f"==> {site.project_name}: {site.source_dir} -> {site.url}")
        if not args.skip_build:
            build_site(root, site)
        deploy_site(root, site)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
