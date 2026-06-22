# CODEX.md

## Project role

This repository is a Hugo + Cloudflare Pages automated blog system. Python generates posts by calling local AI CLIs only.

## Non-negotiable rule

Do not add direct AI API calls.

Forbidden examples:

- OpenAI SDK calls
- Anthropic SDK calls
- Google Generative AI SDK calls
- HTTP requests to AI API endpoints

Allowed:

- `subprocess.run(["claude", "-p", prompt])`
- `subprocess.run(["gemini", "-p", prompt])`
- `subprocess.run(["codex", "-q", prompt])`

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
