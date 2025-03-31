# スクリプトのある場所に移動（任意）
Set-Location -Path $PSScriptRoot

# 監視対象ファイルのパス（必要なら相対パスをフルパスに変換）
$targetFile = Join-Path $PSScriptRoot "latest_ohlc.csv"

# ファイル存在確認
if (-Not (Test-Path $targetFile)) {Write-Host "[警告] ファイル $targetFile が見つかりません。"exit}

Write-Host "[INFO] ファイル変更を監視中: $targetFile"
Write-Host "[INFO] 変更が検出されると、最新10行を表示します。"

# イベントの登録
$fsw = New-Object IO.FileSystemWatcher (Split-Path $targetFile), (Split-Path $targetFile -Leaf)
$fsw.NotifyFilter = [IO.NotifyFilters]'LastWrite'
Register-ObjectEvent $fsw Changed -Action {Clear-Host Write-Host "[更新] $(Get-Date)"Get-Content $using:targetFile -Tail 10}

# 終了待ち（手動で Ctrl + C）
while ($true) {Start-Sleep -Seconds 1}