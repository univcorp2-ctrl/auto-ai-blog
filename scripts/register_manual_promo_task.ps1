$action = New-ScheduledTaskAction -Execute "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog\run_manual_promo.bat"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
Register-ScheduledTask -TaskName "auto-ai-blog-manual-promo" -Action $action -Trigger $trigger -Force
Get-ScheduledTask -TaskName "auto-ai-blog-manual-promo"
