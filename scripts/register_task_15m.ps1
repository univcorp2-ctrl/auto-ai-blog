$action = New-ScheduledTaskAction -Execute "G:\マイドライブ\AI_Agents\github\repos\auto-ai-blog\run_daily.bat"
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName "auto-ai-blog" -Action $action -Trigger $trigger -Description "Generate/import/deploy Auto AI Blog posts with local budget guard." -Force
Get-ScheduledTask -TaskName "auto-ai-blog"
