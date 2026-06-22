#!/usr/bin/env bash
set -euo pipefail

echo "== Cloud article generation =="

export PYTHONIOENCODING=utf-8
export BLOG_EXECUTION_MODE=cloud
export BLOG_GIT_BRANCH="${BLOG_GIT_BRANCH:-main}"

git config user.name "${GIT_AUTHOR_NAME:-github-actions[bot]}"
git config user.email "${GIT_AUTHOR_EMAIL:-41898282+github-actions[bot]@users.noreply.github.com}"

python generator/generate.py --cloud
