$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

py "tools/build_product_detail.py" class-roster
py "tools/check_product_detail.py" class-roster
