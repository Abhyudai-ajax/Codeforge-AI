param(
    # Use the Next.js dev server (hot reload, but compiles each page on first
    # visit, which makes navigation feel slow). Default is the optimized build.
    [switch]$Dev
)

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "                CodeForge AI - System Launch" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"

Write-Host "[0/4] Stopping any previous CodeForge servers..." -ForegroundColor Yellow
# With --reload on Windows, worker processes inherit the listening socket and can
# outlive their parent, silently serving requests with stale code and settings.
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.ExecutablePath -like "$backend\.venv\*" -or $_.CommandLine -match 'uvicorn app\.main:app' } |
    ForEach-Object { taskkill /PID $_.ProcessId /T /F 2>$null | Out-Null }
foreach ($port in 8000, 3000) {
    Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { taskkill /PID $_.OwningProcess /T /F 2>$null | Out-Null }
}
Start-Sleep -Seconds 1

Write-Host "[1/4] Preparing database (problems, roadmaps, contests, demo user)..." -ForegroundColor Yellow
Push-Location $backend
& $python -m app.db.seed_data 2>&1 | Where-Object { $_ -match "seed_data" } | ForEach-Object { Write-Host "      $_" }
Pop-Location

Write-Host "[2/4] Starting Backend (FastAPI on http://127.0.0.1:8000)..." -ForegroundColor Yellow
# --reload-dir keeps the file watcher off .venv, which is large and slow to scan.
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$backend`" && .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir app"

if ($Dev) {
    Write-Host "[3/4] Starting Frontend in dev mode (Next.js on http://localhost:3000)..." -ForegroundColor Yellow
    $frontendCommand = "npm run dev"
} else {
    $buildId = Join-Path $frontend ".next\BUILD_ID"
    $sources = "app", "components", "lib", "providers", "store", "styles", "public" |
        ForEach-Object { Join-Path $frontend $_ } | Where-Object { Test-Path $_ }
    $configFiles = "package.json", "next.config.mjs", "tailwind.config.ts", ".env.local" |
        ForEach-Object { Join-Path $frontend $_ } | Where-Object { Test-Path $_ }
    $newestSource = @(Get-ChildItem $sources -Recurse -File) + @(Get-Item $configFiles) |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $needsBuild = -not (Test-Path $buildId) -or $newestSource.LastWriteTime -gt (Get-Item $buildId).LastWriteTime

    if ($needsBuild) {
        Write-Host "[3/4] Building optimized Frontend (about a minute, only when code changed)..." -ForegroundColor Yellow
        $frontendCommand = "npm run build && npm run start"
    } else {
        Write-Host "[3/4] Starting Frontend (optimized build, http://localhost:3000)..." -ForegroundColor Yellow
        $frontendCommand = "npm run start"
    }
}
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$frontend`" && $frontendCommand"

Write-Host "[4/4] Waiting for the platform to come up..." -ForegroundColor Yellow
$deadline = (Get-Date).AddMinutes(4)
$ready = $false
while ((Get-Date) -lt $deadline) {
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 3 | Out-Null
        Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 3 | Out-Null
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $ready) {
    Write-Host "      Still starting - check the Backend/Frontend windows for errors." -ForegroundColor Red
}
Start-Process "http://localhost:3000"
Start-Process "$root\presentation.html"

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host "Services are running!" -ForegroundColor Green
Write-Host " - Frontend Web App:     http://localhost:3000"
Write-Host " - Backend API Docs:     http://127.0.0.1:8000/api/docs"
Write-Host " - Demo Account:         demo@codeforge.ai / password123"
Write-Host " - Slide Presentation:   $root\presentation.html"
Write-Host "=====================================================================" -ForegroundColor Green
