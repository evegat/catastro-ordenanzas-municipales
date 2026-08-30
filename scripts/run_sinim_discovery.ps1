param([int]$ShardCount = 10)

$runnerMutex = [System.Threading.Mutex]::new($false, "Local\MW-P090-0014-sinim-runner")
$hasRunnerMutex = $runnerMutex.WaitOne(0)
if (-not $hasRunnerMutex) { $runnerMutex.Dispose(); exit 0 }
try {
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$repoPath = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$pythonPath = Join-Path $repoPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { $pythonPath = "python" }
$logPath = Join-Path $repoPath "logs\sinim_discovery_runner.log"
Set-Location -LiteralPath $repoPath

function Write-RunnerLog([string]$message) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $message
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try { Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8; break }
        catch { if ($attempt -eq 3) { throw }; Start-Sleep -Milliseconds 250 }
    }
    Write-Output $line
}

for ($index = 0; $index -lt $ShardCount; $index++) {
    $outPath = "data\sinim_discovery_shard_{0:D2}.json" -f $index
    $valid = $false
    if (Test-Path -LiteralPath $outPath) {
        try {
            $payload = Get-Content -LiteralPath $outPath -Raw | ConvertFrom-Json
            $valid = $payload.task_id -eq "MW-P090-0012" -and $payload.shard.index -eq $index -and $payload.shard.count -eq $ShardCount
        } catch { $valid = $false }
    }
    if ($valid) { Write-RunnerLog "Shard $index/$ShardCount ya válido; se conserva."; continue }
    $success = $false
    for ($attempt = 1; $attempt -le 2 -and -not $success; $attempt++) {
        Write-RunnerLog "Ejecutando shard $index/$ShardCount, intento $attempt."
        & $pythonPath -u "src\sinim_seed_enrichment.py" --shard-index $index --shard-count $ShardCount --out $outPath --timeout 15 --max-site-pages 8
        $success = $LASTEXITCODE -eq 0
    }
    if (-not $success) { throw "Shard $index falló dos veces; se detiene sin perder shards anteriores." }
}

Write-RunnerLog "Uniendo shards y construyendo semillas validadas."
& $pythonPath -u "src\merge_sinim_discovery_shards.py" --shard-count $ShardCount
if ($LASTEXITCODE -ne 0) { throw "Falló merge SINIM." }
& $pythonPath -u "src\build_sinim_extraction_seeds.py"
if ($LASTEXITCODE -ne 0) { throw "Falló construcción de semillas SINIM." }
Write-RunnerLog "Discovery SINIM completo; iniciando extracción documental en shards."

for ($index = 0; $index -lt $ShardCount; $index++) {
    $outPath = "data\sinim_extraction_shard_{0:D2}.json" -f $index
    $valid = $false
    if (Test-Path -LiteralPath $outPath) {
        try {
            $payload = Get-Content -LiteralPath $outPath -Raw | ConvertFrom-Json
            $valid = $payload.task_id -eq "MW-P090-0013" -and $payload.shard.index -eq $index -and $payload.shard.count -eq $ShardCount
        } catch { $valid = $false }
    }
    if ($valid) { Write-RunnerLog "Extracción shard $index/$ShardCount ya válida; se conserva."; continue }
    $success = $false
    for ($attempt = 1; $attempt -le 2 -and -not $success; $attempt++) {
        Write-RunnerLog "Extracción shard $index/$ShardCount, intento $attempt."
        & $pythonPath -u "src\extract_sinim_validated_sources.py" --shard-index $index --shard-count $ShardCount --out $outPath --timeout 15
        $success = $LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq 2
    }
    if (-not $success) { throw "Extracción shard $index falló dos veces; se conserva el progreso anterior." }
}

& $pythonPath -u "src\merge_sinim_extraction_shards.py" --shard-count $ShardCount
if ($LASTEXITCODE -ne 0) { throw "Falló merge de extracción SINIM." }
& $pythonPath -u "src\classify_sinim_evidence_lmstudio.py"
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 2) { throw "Falló clasificación local LM Studio." }
& $pythonPath -u "src\build_national_coverage_ledger.py"
if ($LASTEXITCODE -ne 0) { throw "Falló ledger nacional de brechas." }
Write-RunnerLog "Extracción SINIM terminada y consolidada en cuarentena; no se publicó ni promovió evidencia."
}
finally {
    if ($hasRunnerMutex) { $runnerMutex.ReleaseMutex() }
    $runnerMutex.Dispose()
}
