# Keeps the bots alive on a home PC. Run by Task Scheduler every 5 minutes:
# - starts Docker Desktop if it isn't running, restarts it if its engine hangs;
# - brings back any compose service that is not running.
# Events are written to logs/watchdog.log.

$root = Split-Path $PSScriptRoot -Parent
$dockerDesktop = "$env:LOCALAPPDATA\Programs\DockerDesktop\Docker Desktop.exe"
$env:Path = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin;$env:Path"
$log = Join-Path $root 'logs\watchdog.log'
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null

# A bot stopped on purpose (e.g. to run it locally) must stay stopped: while this file
# exists the watchdog does nothing
if (Test-Path (Join-Path $root 'logs\watchdog.pause')) { exit 0 }

# Past 1 MB the log starts over; the previous one is kept as watchdog.log.1
if ((Test-Path $log) -and (Get-Item $log).Length -gt 1MB) { Move-Item $log "$log.1" -Force }

function Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Add-Content $log -Encoding utf8
}

function Test-Engine {
    docker info --format '{{.ServerVersion}}' *> $null
    return $LASTEXITCODE -eq 0
}

function Wait-Engine($seconds) {
    for ($i = 0; $i -lt $seconds; $i += 5) {
        if (Test-Engine) { return $true }
        Start-Sleep 5
    }
    return $false
}

if (-not (Test-Engine)) {
    $desktop = Get-Process 'Docker Desktop' -ErrorAction SilentlyContinue |
        Sort-Object StartTime | Select-Object -First 1

    if (-not $desktop) {
        Log 'Docker Desktop is not running, starting it'
        Start-Process $dockerDesktop
    }
    elseif ($desktop.StartTime -gt (Get-Date).AddMinutes(-3)) {
        Log 'Docker Desktop is still starting, waiting'
    }
    else {
        Log 'Docker engine is down, restarting Docker Desktop'
        Get-Process 'Docker Desktop', 'com.docker.backend', 'com.docker.build' -ErrorAction SilentlyContinue |
            Stop-Process -Force
        wsl --shutdown
        Start-Process $dockerDesktop
    }

    if (-not (Wait-Engine 180)) {
        Log 'Docker engine did not come up within 3 minutes'
        exit 1
    }
    Log 'Docker engine is up'
}

Set-Location $root
$running = @(docker compose ps --status running --services)
$missing = @(docker compose config --services | Where-Object { $_ -notin $running })
if ($missing.Count) {
    Log "Not running: $($missing -join ', '). Starting"
    docker compose up -d *> $null
    if ($LASTEXITCODE -ne 0) { Log 'docker compose up failed' } else { Log 'Services started' }
}
