# Ban.Tai ekiden watercolor assets upload (safe isolated clone)
# Uses the ZIP supplied by the article author; does not touch an existing working copy.
$ErrorActionPreference = 'Stop'
$branch = 'fix/ekiden-column-use-generated-watercolors-20261108'
$remote = 'https://github.com/bantai-education-design/bantai-education-design.github.io.git'
$zip = $null
$roots = @("$env:USERPROFILE\Downloads", "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Documents")
foreach ($root in $roots) {
  if (-not (Test-Path -LiteralPath $root)) { continue }
  $hits = @(Get-ChildItem -LiteralPath $root -Filter '*大学駅伝*.zip' -File -Recurse -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending)
  if ($hits.Count -gt 0) { $zip = $hits[0].FullName; break }
}
if (-not $zip) {
  Add-Type -AssemblyName System.Windows.Forms
  $dialog = New-Object System.Windows.Forms.OpenFileDialog
  $dialog.Title = '画像3枚が入った「大学駅伝・襷をつなぐ情熱-1.zip」を選んでください'
  $dialog.Filter = 'ZIP files (*.zip)|*.zip'
  if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { throw 'ZIP file selection was cancelled.' }
  $zip = $dialog.FileName
}
Write-Host "ZIP: $zip"
$work = Join-Path $env:TEMP ("bantai-ekiden-watercolor-" + [guid]::NewGuid().ToString('N'))
$unpack = Join-Path $work 'unpacked'
$checkout = Join-Path $work 'repo'
New-Item -ItemType Directory -Force -Path $unpack | Out-Null
Expand-Archive -LiteralPath $zip -DestinationPath $unpack -Force
$mapping = @(
  @{ Pattern = '*襷をつなぐ情熱*.png'; Dest = 'thumbnail.png' },
  @{ Pattern = '*データ連携イラスト*.png'; Dest = 'database-features.png' },
  @{ Pattern = '*研究する温かな書斎*.png'; Dest = 'making-process.png' }
)
$found = @()
foreach ($item in $mapping) {
  $matches = @(Get-ChildItem -LiteralPath $unpack -File -Recurse -Filter $item.Pattern)
  if ($matches.Count -ne 1) { throw "Missing or ambiguous image in ZIP: $($item.Pattern) (count $($matches.Count))" }
  if ($matches[0].Length -lt 100000) { throw "Suspiciously small image: $($matches[0].Name)" }
  $found += @{ Source = $matches[0].FullName; Dest = $item.Dest }
}
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Git is not installed or not on PATH.' }
& git clone --depth 1 --single-branch --branch $branch $remote $checkout
if ($LASTEXITCODE -ne 0) { throw 'Git clone failed.' }
$destDir = Join-Path $checkout 'assets\images\columns\university-ekiden-database-story-2026'
New-Item -ItemType Directory -Force -Path $destDir | Out-Null
foreach ($item in $found) { Copy-Item -LiteralPath $item.Source -Destination (Join-Path $destDir $item.Dest) -Force }
Push-Location $checkout
try {
  $paths = @('assets/images/columns/university-ekiden-database-story-2026/thumbnail.png',
             'assets/images/columns/university-ekiden-database-story-2026/database-features.png',
             'assets/images/columns/university-ekiden-database-story-2026/making-process.png')
  foreach ($path in $paths) { if (-not (Test-Path -LiteralPath $path)) { throw "Missing target image: $path" } }
  & git add -- $paths
  if ($LASTEXITCODE -ne 0) { throw 'Git add failed.' }
  & git diff --cached --check
  if ($LASTEXITCODE -ne 0) { throw 'Git diff --check failed.' }
  & git diff --cached --stat
  & git commit -m 'Add original uploaded watercolor illustrations for university ekiden column'
  if ($LASTEXITCODE -ne 0) { throw 'Git commit failed.' }
  & git push origin $branch
  if ($LASTEXITCODE -ne 0) { throw 'Git push failed.' }
  Write-Host 'SUCCESS: Three original watercolor images uploaded to PR #522.' -ForegroundColor Green
} finally { Pop-Location }
