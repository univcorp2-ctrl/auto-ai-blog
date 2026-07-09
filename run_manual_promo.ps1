$ErrorActionPreference = "Stop"
Set-Location "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog"
$env:PYTHONIOENCODING = "utf-8"
python generator\generate_manual_posts.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python scripts\deploy_cloudflare_pages.py

