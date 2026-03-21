Set-Location (Join-Path $PSScriptRoot 'frontend')
if (-not (Test-Path 'node_modules')) {
  cmd /c npm.cmd install
}
cmd /c npm.cmd run dev -- --host 127.0.0.1 --port 5173
