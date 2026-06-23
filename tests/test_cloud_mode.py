from __future__ import annotations

from generator import cloud, generate, git_ops


def test_cloud_mode_enabled_by_argument(monkeypatch):
    monkeypatch.delenv("BLOG_EXECUTION_MODE", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert generate.cloud_mode_enabled(explicit_cloud=True) is True
    assert cloud.cloud_mode_enabled(explicit_cloud=True) is True


def test_cloud_mode_enabled_by_env(monkeypatch):
    monkeypatch.setenv("BLOG_EXECUTION_MODE", "cloud")
    assert generate.cloud_mode_enabled() is True


def test_get_push_branch_prefers_env(monkeypatch):
    monkeypatch.setenv("BLOG_GIT_BRANCH", "article-main")
    assert generate.get_push_branch({"branch": "main"}) == "article-main"
    assert git_ops.get_push_branch({"branch": "main"}) == "article-main"


def test_get_push_branch_falls_back_to_config(monkeypatch):
    monkeypatch.delenv("BLOG_GIT_BRANCH", raising=False)
    assert generate.get_push_branch({"branch": "production"}) == "production"
