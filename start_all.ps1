$ROOT = "E:\Hackathon Ai Congress\LungCancer.NET"
$FRONTEND = Join-Path $ROOT "frontend"
Write-Host "`n=== Starting LungCancer.NET Services ===" -ForegroundColor Cyan
# 1. Ollama
Write-Host "`n[1/3] Starting Ollama..." -ForegroundColor Yellow
docker start ollama 2>&1 | Out-Null
Start-Sleep -Seconds 2
Write-Host "  OK — Ollama on http://localhost:11434" -ForegroundColor Green
# 2. FastAPI
Write-Host "`n[2/3] Starting FastAPI (port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$ROOT'; `$host.UI.RawUI.WindowTitle='FastAPI'; .\.venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000"
Start-Sleep -Seconds 3
Write-Host "  OK — http://localhost:8000/docs" -ForegroundColor Green
# 3. Next.js
Write-Host "`n[3/3] Starting Next.js (port 3000)..." -ForegroundColor Yellow
if (Test-Path $FRONTEND) {
    Start-Process powershell -ArgumentList "-NoExit","-Command","cd '$FRONTEND'; `$host.UI.RawUI.WindowTitle='Next.js'; npm run dev"
    Start-Sleep -Seconds 3
    Write-Host "  OK — http://localhost:3000/login" -ForegroundColor Green
} else {
    Write-Host "  SKIP — frontend folder not found at $FRONTEND" -ForegroundColor Yellow
}
Write-Host "`n=== All services launched ===" -ForegroundColor Cyan
Write-Host "Press Enter to close this window (services stay running)." -ForegroundColor Gray
Read-Host
