from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CloudflarePagesSite:
    project_name: str
    source_dir: Path
    url: str

    @property
    def public_dir(self) -> Path:
        return self.source_dir / "public"


def load_cloudflare_pages_sites(config: dict[str, Any]) -> list[CloudflarePagesSite]:
    deploy_config = config.get("deploy", {})
    if not isinstance(deploy_config, dict):
        return []

    pages_config = deploy_config.get("cloudflare_pages", {})
    if not isinstance(pages_config, dict) or not bool(pages_config.get("enabled", False)):
        return []

    raw_sites = pages_config.get("sites", [])
    if not isinstance(raw_sites, list):
        raise ValueError("deploy.cloudflare_pages.sites must be a list")

    sites: list[CloudflarePagesSite] = []
    for item in raw_sites:
        if not isinstance(item, dict):
            raise ValueError("Each Cloudflare Pages site entry must be a mapping")

        project_name = str(item.get("project_name", "")).strip()
        source_dir = str(item.get("source_dir", "")).strip()
        url = str(item.get("url", "")).strip()
        if not project_name or not source_dir or not url:
            raise ValueError(f"Invalid Cloudflare Pages site entry: {item}")

        sites.append(
            CloudflarePagesSite(
                project_name=project_name,
                source_dir=Path(source_dir),
                url=url,
            )
        )
    return sites
