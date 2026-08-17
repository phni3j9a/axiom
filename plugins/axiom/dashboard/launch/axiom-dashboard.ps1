$ErrorActionPreference = "Stop"

$DashboardDir = Split-Path -Parent $PSScriptRoot
$Binary = Join-Path $DashboardDir "bin/windows-x86_64/axiom-dashboard.exe"

if (Test-Path $Binary) {
    & $Binary @args
    exit $LASTEXITCODE
}

if (Get-Command cargo -ErrorAction SilentlyContinue) {
    & cargo run --quiet --release --manifest-path (Join-Path $DashboardDir "Cargo.toml") -- @args
    exit $LASTEXITCODE
}

Write-Error @"
Axiom Dashboard binary was not found.
Expected: $Binary

Build this source package with:
  cargo build --release --manifest-path "$DashboardDir/Cargo.toml"

Then copy target/release/axiom-dashboard.exe into:
  $DashboardDir/bin/windows-x86_64/

Official release packages include the prebuilt Windows binary.
"@
