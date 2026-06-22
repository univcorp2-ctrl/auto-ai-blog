$action = New-ScheduledTaskAction -Execute "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog\run_daily.bat"
$trigger = New-ScheduledTaskTrigger -Daily -At 9:00am
Register-ScheduledTask -TaskName "auto-ai-blog" -Action $action -Trigger $trigger
Get-ScheduledTask -TaskName "auto-ai-blog"
