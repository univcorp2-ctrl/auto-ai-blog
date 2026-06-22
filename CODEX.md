# CODEX.md

## Project role

This repository is a Hugo + Cloudflare Pages automated blog system. Python generates posts by calling AI CLIs only. It supports both Local Mode and Cloud Mode.

## Non-negotiable rule

Do not add direct AI API calls.

Forbidden examples:

- OpenAI SDK calls
- Anthropic SDK calls
- Google Generative AI SDK calls
- HTTP requests to AI API endpoints from Python

Allowed:

- `subprocess.run(["claude", "-p", prompt])`
- `subprocess.run(["gemini", "-p", prompt])`
- `subprocess.run(["codex", "-q", prompt])`

## Local Mode

```bash
python generator/generate.py
```

Windows entrypoint:

```bat
run_daily.bat
```

## Cloud Mode

```bash
export BLOG_EXECUTION_MODE=cloud
bash scripts/cloud_prepare_ai_cli.sh
bash scripts/cloud_generate.sh
```

Cloud workflow template:

```text
docs/workflows/cloud-daily-post.yml
```

The workflow template should be copied to `.github/workflows/cloud-daily-post.yml` when workflow-write permission is available.

## Test before committing

```bash
ruff check .
pytest
hugo --source hugo-site --gc --minify
```

If PaperMod is missing:

```bash
git clone --depth=1 https://github.com/adityatelange/hugo-PaperMod.git hugo-site/themes/PaperMod
```

## Important files

- `generator/generate.py`: article generation, Local Mode, Cloud Mode, git automation
- `scripts/cloud_prepare_ai_cli.sh`: cloud AI CLI preparation
- `scripts/cloud_generate.sh`: cloud generation entrypoint
- `generator/prompts.py`: prompts for local/cloud AI CLIs
- `generator/topics.yaml`: rotating topic list
- `hugo-site/config.toml`: Hugo and PaperMod settings
- `docs/cloud-mode.md`: Cloud Mode guide
- `docs/program-flow.md`: diagram-heavy program flow guide
