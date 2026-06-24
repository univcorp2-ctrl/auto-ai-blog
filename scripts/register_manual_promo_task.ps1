$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog\run_manual_promo.ps1`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "auto-ai-blog-manual-promo" -Action $action -Trigger $trigger -Force
Get-ScheduledTask -TaskName "auto-ai-blog-manual-promo"

