$ErrorActionPreference = "Stop"
Set-Location "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog"
$env:PYTHONIOENCODING = "utf-8"
& .venv\Scripts\python.exe generator\generate_manual_posts.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .venv\Scripts\python.exe scripts\deploy_cloudflare_pages.py
