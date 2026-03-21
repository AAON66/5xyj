Set-Location $PSScriptRoot
cmd /c start "backend" powershell -NoExit -ExecutionPolicy Bypass -File "$PSScriptRoot\start_backend_local.ps1"
cmd /c start "frontend" powershell -NoExit -ExecutionPolicy Bypass -File "$PSScriptRoot\start_frontend_local.ps1"
