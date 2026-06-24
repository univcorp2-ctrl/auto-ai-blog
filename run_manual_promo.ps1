$ErrorActionPreference = "Stop"
Set-Location "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog"
$env:PYTHONIOENCODING = "utf-8"
& .venv\Scripts\python.exe generator\generate_manual_posts.py
