@echo off
set PYTHONIOENCODING=utf-8
cd /d "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog"
set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"
"%PYTHON_EXE%" "scripts\run_daily_guarded.py"
pause
