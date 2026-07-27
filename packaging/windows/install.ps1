$ErrorActionPreference = "Stop"

$wheelhouse = Join-Path $PSScriptRoot "wheelhouse"
$wheel = Get-Item (Join-Path $wheelhouse "termkeeper-*.whl")

uv tool install `
    --python 3.12 `
    --offline `
    --no-index `
    --find-links $wheelhouse `
    $wheel.FullName
uv tool update-shell

Write-Host "TermKeeper installed. Reopen PowerShell, then run 'tk --version' and 'tk doctor'."
