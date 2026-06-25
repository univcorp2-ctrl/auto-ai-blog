from __future__ import annotations

from pathlib import Path
from typing import Any


def route_category_to_site(config: dict[str, Any], category: str) -> Path:
    blog_config = config.get("blog", {})
    if not isinstance(blog_config, dict):
        return Path("sites/ai-tech")

    site_map = blog_config.get("site_map", {})
    if isinstance(site_map, dict):
        site = site_map.get(category)
        if site:
            return Path(str(site))

    return Path(str(blog_config.get("default_site", "sites/ai-tech")))
