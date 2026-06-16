$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python "tools/build_product_detail.py"
python "tools/check_product_detail.py"
