<#
.SYNOPSIS
    Stops all LungCancer.NET services.
#>

Write-Host "Stopping all LungCancer.NET services..." -ForegroundColor Yellow

$ports = @(8000, 3000, 8001)
$killed = 0

foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "  Killing $($proc.ProcessName) on port $port (PID $($proc.Id))" -ForegroundColor Gray
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                $killed++
            }
        }
    }
}

# Ollama stays running — it's a shared Docker service
Write-Host "`n✅ Stopped $killed process(es)." -ForegroundColor Green
Write-Host "   Ollama (Docker) still running — use 'docker stop ollama' to stop it separately." -ForegroundColor Gray