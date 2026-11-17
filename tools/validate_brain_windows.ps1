param(
    [string[]]$Models = @('qwen2.5:0.5b', 'qwen2.5:1.5b'),
    [string]$Output = '',
    [string]$Python = '.venv-brain\Scripts\python.exe',
    [ValidateRange(1, 900)][int]$GenerationTimeout = 180
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repository = Split-Path -Parent $PSScriptRoot
Push-Location $repository
try {
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw 'Prepare Python 3.12 e requirements-brain.txt conforme docs/NOW_BRAIN_API_V1.md, ou informe -Python.'
    }
    if (-not $Output) {
        $Output = Join-Path ([System.IO.Path]::GetTempPath()) ('now-brain-v5-' + [guid]::NewGuid().ToString())
    }
    # Never start/stop an existing Ollama service, download weights or expose ports.
    & $Python tools\validate_brain_api.py --output $Output --models $Models --timeout $GenerationTimeout
    $result = $LASTEXITCODE
    if ($result -eq 2) {
        Write-Host 'BLOQUEADO: confira se o Ollama esta ativo e se as tags solicitadas aparecem em ollama list.'
    }
    Write-Host ('Evidencias locais: ' + $Output)
    exit $result
}
finally {
    Pop-Location
}
