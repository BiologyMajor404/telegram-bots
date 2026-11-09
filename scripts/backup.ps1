# Daily backup of the bots' data, run by Task Scheduler (scripts\install-backup.ps1):
# every PostgreSQL database (pg_dumpall, checked and gzipped) and a fresh Redis snapshot go to
# <Dest>\<date>_postgres.sql.gz and <Dest>\<date>_redis.rdb. Nothing old is deleted: a day takes
# a few dozen KB, so clean the folder by hand when you like. Events go to logs/backup.log.
param([string]$Dest = 'D:\Backups\daily')

$root = Split-Path $PSScriptRoot -Parent
$env:Path = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin;$env:Path"
$log = Join-Path $root 'logs\backup.log'
New-Item -ItemType Directory -Force (Split-Path $log), $Dest | Out-Null

function Log($msg) {
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg" | Add-Content $log -Encoding utf8
}

function Saved($path, $what) {
    if ((Test-Path $path) -and (Get-Item $path).Length -gt 0) {
        Log ('{0} saved: {1} ({2:N1} KB)' -f $what, (Split-Path $path -Leaf), ((Get-Item $path).Length / 1KB))
        return $true
    }
    Log "$what backup FAILED"
    return $false
}

Set-Location $root
docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) {
    Log 'Docker engine is down: no backup this time'
    exit 1
}
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmm'

# PostgreSQL: dumped, checked for its closing line and gzipped inside the container, then copied
# out byte for byte (PowerShell's own redirection would re-encode the text). No password needed:
# inside the container the superuser connects through the local socket.
$sql = Join-Path $Dest "${stamp}_postgres.sql.gz"
docker compose exec -T postgres sh -c 'pg_dumpall -U $POSTGRES_USER > /tmp/backup.sql && grep -q cluster.dump.complete /tmp/backup.sql && gzip -f /tmp/backup.sql' *> $null
if ($LASTEXITCODE -eq 0) { docker compose cp postgres:/tmp/backup.sql.gz $sql *> $null }
docker compose exec -T postgres rm -f /tmp/backup.sql /tmp/backup.sql.gz *> $null
$ok = Saved $sql 'PostgreSQL'

# Redis: a fresh snapshot, copied out
$rdb = Join-Path $Dest "${stamp}_redis.rdb"
docker compose exec -T redis redis-cli SAVE *> $null
if ($LASTEXITCODE -eq 0) { docker compose cp redis:/data/dump.rdb $rdb *> $null }
$ok = (Saved $rdb 'Redis') -and $ok

if (-not $ok) { exit 1 }
