param(
    [switch]$NoReload,
    [switch]$Preview
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $projectRoot ".env"

function Get-DotEnvValue {
    param(
        [string]$FilePath,
        [string]$Key,
        [string]$DefaultValue = ""
    )

    if (-not (Test-Path $FilePath)) {
        return $DefaultValue
    }

    foreach ($rawLine in Get-Content -Path $FilePath) {
        $line = $rawLine.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            continue
        }
        $pair = $line.Split("=", 2)
        if ($pair.Length -ne 2) {
            continue
        }
        if ($pair[0].Trim() -eq $Key) {
            return $pair[1].Trim()
        }
    }

    return $DefaultValue
}

$pythonCandidates = @(
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path $projectRoot "venv\Scripts\python.exe")
)

$pythonExe = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $pythonExe) {
    throw "No project virtual environment found. Expected .venv\Scripts\python.exe or venv\Scripts\python.exe."
}

$bindHost = Get-DotEnvValue -FilePath $envFile -Key "AC_BIND_HOST" -DefaultValue "127.0.0.1"
$bindPort = Get-DotEnvValue -FilePath $envFile -Key "AC_BIND_PORT" -DefaultValue "8008"

$arguments = @("-m", "uvicorn", "run:app", "--host", $bindHost, "--port", $bindPort)
if (-not $NoReload) {
    $arguments += "--reload"
}

Write-Host "Project root: $projectRoot"
Write-Host "Python: $pythonExe"
Write-Host "Host: $bindHost"
Write-Host "Port: $bindPort"
Write-Host "Reload: $((-not $NoReload).ToString().ToLower())"
Write-Host "Command: $pythonExe $($arguments -join ' ')"

if ($Preview) {
    exit 0
}

Push-Location $projectRoot
try {
    & $pythonExe @arguments
}
finally {
    Pop-Location
}
