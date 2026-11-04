<#
.SYNOPSIS
    Starts all LungCancer.NET services in separate PowerShell windows.

.DESCRIPTION
    Launches:
      1. Ollama (Docker container)
      2. FastAPI backend (port 8000)
      3. Next.js frontend (port 3000)
      4. MCP server (port 8001) [optional]

.EXAMPLE
    .\start_all.ps1
    .\start_all.ps1 -WithMCP
    .\start_all.ps1 -BackendOnly
#>

param(
    [switch]$WithMCP,
    [switch]$FrontendOnly,
    [switch]$BackendOnly
)

$ROOT = "E:\Hackathon Ai Congress\LungCancer.NET"
$FRONTEND = Join-Path $ROOT "frontend"

# ── Colour helpers ─────────────────────────────────────────────────
function Write-Step($msg) { Write-Host "`n▶ $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  ✅ $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  ⚠️  $msg" -ForegroundColor Yellow }
function Write-Err($msg)  { Write-Host "  ❌ $msg" -ForegroundColor Red }
function Write-URL($url)  { Write-Host "     → $url" -ForegroundColor White }

# ── Banner ─────────────────────────────────────────────────────────
Clear-Host
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║   🫁  LungCancer.NET — All Services Launcher        ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Magenta

# ── Verify project folder ──────────────────────────────────────────
if (-not (Test-Path $ROOT)) {
    Write-Err "Project folder not found: $ROOT"
    exit 1
}
Set-Location $ROOT

# ── Verify venv ────────────────────────────────────────────────────
if (-not (Test-Path "$ROOT\.venv\Scripts\Activate.ps1")) {
    Write-Err "Python venv not found at $ROOT\.venv"
    Write-Warn "Create it first: python -m venv .venv"
    exit 1
}

# ══════════════════════════════════════════════════════════════════
# STEP 1 — Docker / Ollama
# ══════════════════════════════════════════════════════════════════
if (-not $FrontendOnly -and -not $BackendOnly) {
    Write-Step "Checking Docker + Ollama..."

    $dockerRunning = $false
    try {
        $null = docker info 2>&1
        if ($LASTEXITCODE -eq 0) { $dockerRunning = $true }
    } catch { }

    if (-not $dockerRunning) {
        Write-Warn "Docker Desktop is not running"
        Write-URL "Start Docker Desktop manually, then re-run this script"
        Write-Host "     (or press Ctrl+C to skip Ollama — AI summaries will use fallback)" -ForegroundColor DarkGray
    } else {
        $ollamaStatus = (docker ps -a --filter "name=ollama" --format "{{.Status}}" 2>&1) -join ""
        if ($ollamaStatus -match "Up") {
            Write-OK "Ollama container already running"
        } elseif ($ollamaStatus -match "Exited") {
            docker start ollama 2>&1 | Out-Null
            Write-OK "Ollama container started"
            Start-Sleep -Seconds 3
        } else {
            Write-Warn "Ollama container not found"
            Write-URL "Run first: docker run -d --name ollama -v ollama:/root/.ollama -p 11434:11434 ollama/ollama"
        }

        # Verify API
        try {
            $tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -ErrorAction Stop
            Write-OK "Ollama API responding ($($tags.models.Count) models installed)"
        } catch {
            Write-Warn "Ollama API not responding yet — may still be starting"
        }
    }
}

# ══════════════════════════════════════════════════════════════════
# STEP 2 — FastAPI backend (port 8000)
# ══════════════════════════════════════════════════════════════════
if (-not $FrontendOnly) {
    Write-Step "Starting FastAPI backend on :8000..."
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$ROOT'; " +
        "`$host.UI.RawUI.WindowTitle = 'LungCancer.NET — FastAPI'; " +
        "Write-Host 'Starting FastAPI backend...' -ForegroundColor Cyan; " +
        ".\.venv\Scripts\Activate.ps1; " +
        "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    )
    Start-Sleep -Seconds 4
    Write-OK "FastAPI launched in new window"
    Write-URL "http://localhost:8000/docs"
}

# ══════════════════════════════════════════════════════════════════
# STEP 3 — Next.js frontend (port 3000)
# ══════════════════════════════════════════════════════════════════
if (-not $BackendOnly) {
    if (Test-Path $FRONTEND) {
        Write-Step "Starting Next.js frontend on :3000..."
        Start-Process powershell -ArgumentList @(
            "-NoExit",
            "-Command",
            "cd '$FRONTEND'; " +
            "`$host.UI.RawUI.WindowTitle = 'LungCancer.NET — Next.js'; " +
            "Write-Host 'Starting Next.js frontend...' -ForegroundColor Cyan; " +
            "npm run dev"
        )
        Start-Sleep -Seconds 3
        Write-OK "Next.js launched in new window"
        Write-URL "http://localhost:3000/login"
    } else {
        Write-Warn "Frontend folder not found at $FRONTEND"
        Write-URL "Skipping — Antigravity may have created it elsewhere"
    }
}

# ══════════════════════════════════════════════════════════════════
# STEP 4 — MCP server (port 8001) — optional
# ══════════════════════════════════════════════════════════════════
if ($WithMCP) {
    Write-Step "Starting MCP server on :8001..."
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$ROOT'; " +
        "`$host.UI.RawUI.WindowTitle = 'LungCancer.NET — MCP'; " +
        "Write-Host 'Starting MCP server...' -ForegroundColor Cyan; " +
        ".\.venv\Scripts\Activate.ps1; " +
        "python mcp_server.py --http --port 8001"
    )
    Start-Sleep -Seconds 3
    Write-OK "MCP server launched in new window"
    Write-URL "http://localhost:8001/mcp"
}

# ══════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════
Write-Host "`n╔══════════════════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║              ✅ All Services Launched               ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Magenta

Write-Host "`n📋 URLs:" -ForegroundColor Cyan
if (-not $FrontendOnly) {
    Write-Host "   FastAPI backend    → http://localhost:8000/docs" -ForegroundColor White
}
if (-not $BackendOnly) {
    Write-Host "   React frontend     → http://localhost:3000/login" -ForegroundColor White
}
if ($WithMCP) {
    Write-Host "   MCP server         → http://localhost:8001/mcp" -ForegroundColor White
}
Write-Host "   Ollama API         → http://localhost:11434/api/tags" -ForegroundColor White

Write-Host "`n💡 To stop services:" -ForegroundColor Cyan
Write-Host "   Close the individual PowerShell windows, OR" -ForegroundColor White
Write-Host "   Run: .\stop_all.ps1   (if you created it)" -ForegroundColor White

Write-Host "`n🌐 Opening frontend in browser...`n" -ForegroundColor Cyan
if (-not $BackendOnly -and (Test-Path $FRONTEND)) {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000/login"
}

Write-Host "Press Enter to close this window (services stay running)." -ForegroundColor DarkGray
Read-Host