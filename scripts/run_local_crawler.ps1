param(
    [string]$Model = "qwen/qwen3.5-9b",
    [ValidateRange(1, 1000)][int]$BatchSize = 25,
    [ValidateRange(0, 60)][int]$PauseMinutes = 1,
    [ValidateRange(1, 1000)][int]$MaxBatches = 1,
    [switch]$ValidateOnly
)
$ErrorActionPreference = "Stop"
$repoPath = Split-Path -Parent $PSScriptRoot
$crawlerPath = Join-Path $repoPath "src\continuous_commune_crawler.py"
if (-not (Test-Path -LiteralPath $crawlerPath -PathType Leaf)) {
    throw "Dependencia ausente: src\continuous_commune_crawler.py. No se inició ningún lote."
}
$pythonPath = Join-Path $repoPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = "python" }
if (-not (Get-Command $pythonPath -ErrorAction SilentlyContinue)) { throw "Python no disponible." }
if ($ValidateOnly) { Write-Output "Dependencias presentes; no se ejecutó el crawler ni se verificó LM Studio."; exit 0 }
Set-Location -LiteralPath $repoPath
$consecutiveFailures = 0
for ($batch = 1; $batch -le $MaxBatches; $batch++) {
    & $pythonPath "src\continuous_commune_crawler.py" --model $Model --max $BatchSize --retry-failed
    if ($LASTEXITCODE -eq 2) { throw "LM Studio o el modelo no están disponibles; la cola no fue alterada." }
    if ($LASTEXITCODE -eq 3) { Write-Output "Cola automática terminada."; exit 0 }
    if ($LASTEXITCODE -ne 0) {
        $consecutiveFailures++
        if ($consecutiveFailures -ge 2 -or $batch -eq $MaxBatches) {
            throw "Lote fallido (código $LASTEXITCODE); se detiene conservando el progreso."
        }
        Write-Warning "Lote fallido; queda un reintento dentro del límite autorizado de lotes."
    } else { $consecutiveFailures = 0 }
    if ($batch -lt $MaxBatches) { Start-Sleep -Seconds ($PauseMinutes * 60) }
}
Write-Output "Límite de $MaxBatches lotes alcanzado; no implica que la cola esté completa."
