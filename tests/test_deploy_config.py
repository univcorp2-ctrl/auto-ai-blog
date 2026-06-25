from __future__ import annotations

from pathlib import Path

from generator.config_loader import load_yaml
from generator.deploy_config import load_cloudflare_pages_sites
from scripts.deploy_cloudflare_pages import resolve_command


def test_cloudflare_pages_sites_are_configured_for_existing_hugo_sites() -> None:
    root = Path(__file__).resolve().parents[1]
    config = load_yaml(root / "generator" / "config.yaml")

    sites = load_cloudflare_pages_sites(config)

    assert [site.project_name for site in sites] == [
        "ai-tech-blog",
        "business-blog",
        "real-estate-blog",
    ]
    for site in sites:
        assert (root / site.source_dir / "hugo.toml").exists()
        assert site.public_dir == site.source_dir / "public"
        assert site.url.startswith("https://")


def test_resolve_command_uses_windows_cmd_shims(monkeypatch) -> None:
    monkeypatch.setattr("scripts.deploy_cloudflare_pages.shutil.which", lambda name: f"C:/tools/{name}")

    command = resolve_command(["npx", "wrangler", "--version"])

    assert command[0] == "C:/tools/npx.cmd"
    assert command[1:] == ["wrangler", "--version"]
