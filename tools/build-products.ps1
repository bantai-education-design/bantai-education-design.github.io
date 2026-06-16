Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
  py tools/build_products.py
  py tools/check_products.py
}
finally {
  Pop-Location
}
