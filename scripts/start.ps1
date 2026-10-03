param([int]$Port = 8501)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    $pythonCommand = Get-Command python -ErrorAction Stop
    & $pythonCommand.Source -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Instale Python 3.11+ para criar o ambiente.' }
}
if (-not (Test-Path '.venv/.job-hunter-ready')) {
    & .venv/Scripts/python.exe -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação das dependências fixadas.' }
    & .venv/Scripts/python.exe -m pip install -e . --no-deps
    if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação das dependências.' }
    & .venv/Scripts/python.exe -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação do Chromium.' }
    New-Item -ItemType File .venv/.job-hunter-ready -Force | Out-Null
}
& .venv/Scripts/python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port $Port --browser.gatherUsageStats false
