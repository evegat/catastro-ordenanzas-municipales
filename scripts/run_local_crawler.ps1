param(
    [string]$Model = "qwen/qwen3.5-9b",
    [int]$BatchSize = 25,
    [int]$PauseMinutes = 1
)
$ErrorActionPreference = "Stop"
$repoPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repoPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = "python" }
Set-Location -LiteralPath $repoPath
while ($true) {
    & $pythonPath "src\continuous_commune_crawler.py" --model $Model --max $BatchSize --retry-failed
    if ($LASTEXITCODE -eq 2) { throw "LM Studio o el modelo no están disponibles; la cola no fue alterada." }
    if ($LASTEXITCODE -eq 3) { Write-Output "Cola automática terminada."; exit 0 }
    if ($LASTEXITCODE -ne 0) { Write-Warning "Lote terminó con código $LASTEXITCODE; se reintentará." }
    Start-Sleep -Seconds ($PauseMinutes * 60)
}
