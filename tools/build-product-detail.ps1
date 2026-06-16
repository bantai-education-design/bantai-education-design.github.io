param(
  [Parameter(Mandatory = $true)]
  [string]$Slug
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

py "tools/build_product_detail.py" $Slug
py "tools/check_product_detail.py" $Slug
