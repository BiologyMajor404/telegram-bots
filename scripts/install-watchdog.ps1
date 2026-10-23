# Registers watchdog.ps1 in Windows Task Scheduler (current user, every 5 minutes, hidden).
# Run once: powershell -ExecutionPolicy Bypass -File scripts\install-watchdog.ps1

$taskName = 'TelegramBots Watchdog'
$script = Join-Path $PSScriptRoot 'watchdog.ps1'

# conhost --headless runs PowerShell without flashing a console window
$action = New-ScheduledTaskAction -Execute 'conhost.exe' `
    -Argument "--headless powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 5)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings `
    -Description 'Keeps Docker Desktop and the Telegram bots running' -Force | Out-Null
Write-Output "Task '$taskName' registered"
