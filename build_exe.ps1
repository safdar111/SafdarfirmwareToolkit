$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Host "Preparing Windows 10 EXE build for Safdar Firmware Toolkit..."

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Error "Python launcher 'py' is required. Install Python for Windows and ensure it is on PATH."
    exit 1
}

py -m pip install --upgrade pip pyinstaller

$specPath = Join-Path $projectRoot 'main.spec'
if (Test-Path $specPath) { Remove-Item $specPath -Force }

py -m PyInstaller --onefile --windowed --name "SafdarFirmwareToolkit" `
    --distpath "$projectRoot\dist" `
    --workpath "$projectRoot\build" `
    --specpath "$projectRoot" `
    "$projectRoot\main.py"

Write-Host "Build finished. EXE is in: $projectRoot\dist"
Write-Host "You can install or run the generated EXE on a Windows 10 workshop laptop."
