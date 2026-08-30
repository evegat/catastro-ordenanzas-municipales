param(
    [string]$Model = "qwen/qwen3.5-9b",
    [int]$BatchSize = 25,
    [int]$PauseMinutes = 1,
    [int]$CheckSeconds = 60,
    [int]$StaleMinutes = 12
)

$ErrorActionPreference = "Stop"
$repoPath = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$runnerPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "run_local_crawler.ps1")).Path
$crawlerPath = (Resolve-Path -LiteralPath (Join-Path $repoPath "src\continuous_commune_crawler.py")).Path
$sinimRunnerPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "run_sinim_discovery.ps1")).Path
$sinimFinalPath = Join-Path $repoPath "data\national_coverage_ledger.json"
$statePath = Join-Path $repoPath "data\crawler_state.json"
$crawlerLogPath = Join-Path $repoPath "logs\continuous_crawler.log"
$watchdogLogPath = Join-Path $repoPath "logs\local_crawler_watchdog.log"
$runnerOutPath = Join-Path $repoPath "logs\local_crawler_runner.out.log"
$runnerErrPath = Join-Path $repoPath "logs\local_crawler_runner.err.log"
$sinimOutPath = Join-Path $repoPath "logs\sinim_discovery.out.log"
$sinimErrPath = Join-Path $repoPath "logs\sinim_discovery.err.log"
$lmStudioModelsUri = "http://127.0.0.1:1234/v1/models"
$powershellExe = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"
if (-not (Test-Path -LiteralPath $powershellExe)) {
    $powershellExe = (Get-Process -Id $PID).Path
}
$mutexName = "Local\MW-P090-0014-local-crawler-watchdog"

if ($CheckSeconds -lt 15) { throw "CheckSeconds debe ser al menos 15." }
if ($StaleMinutes -lt ([Math]::Max(5, $PauseMinutes + 2))) {
    throw "StaleMinutes debe ser al menos 5 y superar la pausa del runner por 2 minutos."
}

function Write-WatchdogLog {
    param([string]$Level, [string]$Message)
    $line = "{0} [{1}] {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Message
    Add-Content -LiteralPath $watchdogLogPath -Value $line -Encoding UTF8
    Write-Output $line
}

function Test-LMStudio {
    try {
        $response = Invoke-RestMethod -Uri $lmStudioModelsUri -TimeoutSec 8
        return [bool]($response.data | Where-Object { $_.id -eq $Model })
    }
    catch {
        return $false
    }
}

function Get-ExactRunnerProcesses {
    $quotedNeedle = '-File "' + $runnerPath + '"'
    @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'pwsh.exe'" |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine.IndexOf($quotedNeedle, [StringComparison]::OrdinalIgnoreCase) -ge 0
        })
}

function Get-ExactCrawlerProcesses {
    $escapedCrawler = [Regex]::Escape($crawlerPath)
    @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe' OR Name = 'pythonw.exe'" |
        Where-Object { $_.CommandLine -and $_.CommandLine -match ('(?i)(?:"|''|)' + $escapedCrawler + '(?:"|''|)(?:\s|$)') })
}

function Get-ExactSinimProcesses {
    $quotedNeedle = '-File "' + $sinimRunnerPath + '"'
    @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe' OR Name = 'pwsh.exe'" |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine.IndexOf($quotedNeedle, [StringComparison]::OrdinalIgnoreCase) -ge 0
        })
}

function Get-LastActivity {
    $timestamps = @()
    foreach ($path in @($statePath, $crawlerLogPath)) {
        if (Test-Path -LiteralPath $path) {
            $timestamps += (Get-Item -LiteralPath $path).LastWriteTime
        }
    }
    if ($timestamps.Count -eq 0) { return $null }
    return ($timestamps | Sort-Object -Descending | Select-Object -First 1)
}

function Test-CrawlerComplete {
    if (-not (Test-Path -LiteralPath $statePath)) { return $false }
    try {
        $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        return [bool]$state.automatic_queue_complete
    }
    catch { return $false }
}

function Start-ExactRunner {
    if (Test-CrawlerComplete) {
        Write-WatchdogLog "INFO" "La cola automática del crawler está terminada; no se relanza."
        return
    }
    if ((Get-ExactRunnerProcesses).Count -gt 0) {
        Write-WatchdogLog "INFO" "El runner exacto ya está activo; no se crea otra instancia."
        return
    }
    if ((Get-ExactCrawlerProcesses).Count -gt 0) {
        Write-WatchdogLog "WARN" "Hay un crawler exacto sin runner detectable; no se inicia otro para evitar duplicidad."
        return
    }
    $arguments = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"{0}"' -f $runnerPath),
        "-Model", $Model, "-BatchSize", $BatchSize, "-PauseMinutes", $PauseMinutes
    )
    $process = Start-Process -FilePath $powershellExe -ArgumentList $arguments `
        -WorkingDirectory $repoPath -WindowStyle Hidden -RedirectStandardOutput $runnerOutPath `
        -RedirectStandardError $runnerErrPath -PassThru
    Write-WatchdogLog "ACTION" "Runner exacto iniciado con PID $($process.Id)."
}

function Start-SinimRunner {
    if (Test-Path -LiteralPath $sinimFinalPath) { return }
    $processes = @(Get-ExactSinimProcesses)
    if ($processes.Count -gt 1) {
        Write-WatchdogLog "STOP" "Se detectaron múltiples runners SINIM; no se elige ni inicia otro."
        exit 5
    }
    if ($processes.Count -eq 1) { return }
    $arguments = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"{0}"' -f $sinimRunnerPath))
    $process = Start-Process -FilePath $powershellExe -ArgumentList $arguments `
        -WorkingDirectory $repoPath -WindowStyle Hidden -RedirectStandardOutput $sinimOutPath `
        -RedirectStandardError $sinimErrPath -PassThru
    Write-WatchdogLog "ACTION" "Discovery SINIM iniciado con PID $($process.Id)."
}

$mutex = [System.Threading.Mutex]::new($false, $mutexName)
$hasMutex = $false
try {
    $hasMutex = $mutex.WaitOne(0)
    if (-not $hasMutex) { throw "Ya existe un watchdog MW-P090-0014 activo." }
    Write-WatchdogLog "INFO" "Watchdog iniciado; check=${CheckSeconds}s, stale=${StaleMinutes}m, modelo=$Model."

    while ($true) {
        if (-not (Test-LMStudio)) {
            Write-WatchdogLog "STOP" "LM Studio o el modelo '$Model' no están disponibles. El watchdog se detiene sin tocar procesos."
            exit 2
        }

        $runners = @(Get-ExactRunnerProcesses)
        if ($runners.Count -gt 1) {
            Write-WatchdogLog "STOP" "Se detectaron $($runners.Count) runners exactos. Se detiene para no elegir ni matar procesos ambiguos."
            exit 4
        }

        if ($runners.Count -eq 0) {
            Start-ExactRunner
        }
        else {
            $lastActivity = Get-LastActivity
            $ageMinutes = if ($null -eq $lastActivity) { [double]::PositiveInfinity } else { ((Get-Date) - $lastActivity).TotalMinutes }
            if ($ageMinutes -ge $StaleMinutes) {
                $runner = $runners[0]
                Write-WatchdogLog "ACTION" ("Runner PID {0} sin actividad por {1:N1} min; se detiene sólo ese PID exacto." -f $runner.ProcessId, $ageMinutes)
                Stop-Process -Id $runner.ProcessId -Force
                Start-Sleep -Seconds 3
                Start-ExactRunner
            }
        }

        Start-SinimRunner

        Start-Sleep -Seconds $CheckSeconds
    }
}
finally {
    if ($hasMutex) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
