# Registers backup.ps1 in Windows Task Scheduler (current user, every day at 04:00, hidden).
# Run once: powershell -ExecutionPolicy Bypass -File scripts\install-backup.ps1

$taskName = 'TelegramBots Backup'
$script = Join-Path $PSScriptRoot 'backup.ps1'

# conhost --headless runs PowerShell without flashing a console window
$action = New-ScheduledTaskAction -Execute 'conhost.exe' `
    -Argument "--headless powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Daily -At 4am
# A night missed while the PC was off is made up as soon as it is on again
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
    -Description 'Daily backup of the Telegram bots databases (scripts\backup.ps1)' -Force | Out-Null
Write-Output "Task '$taskName' registered"
