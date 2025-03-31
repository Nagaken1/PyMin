# スクリプトのある場所に移動
Set-Location -Path $PSScriptRoot

# 監視対象ファイルのフルパスを文字列で指定（$using: 使わずに済む）
$targetFilePath = Join-Path $PSScriptRoot "latest_ohlc.csv"

if (-Not (Test-Path $targetFilePath)) {
    Write-Host "[警告] ファイル $targetFilePath が見つかりません。"
    exit
}

Write-Host "[INFO] ファイル変更を監視中: $targetFilePath"
Write-Host "[INFO] 変更が検出されると、最新10行を表示します。"

$fsw = New-Object IO.FileSystemWatcher (Split-Path $targetFilePath), (Split-Path $targetFilePath -Leaf)
$fsw.NotifyFilter = [IO.NotifyFilters]'LastWrite'
$fsw.EnableRaisingEvents = $true

# $targetFilePath をイベント内で使えるように直接埋め込み
Register-ObjectEvent $fsw Changed -Action {
    try {
        Start-Sleep -Milliseconds 500
        Clear-Host
        Write-Host "[更新] $(Get-Date)"
        Write-Host "---------- 最新データ ----------"
        Get-Content "$($Event.SourceEventArgs.FullPath)" | Select-Object -Last 10
        Write-Host "--------------------------------"
    } catch {
        Write-Host "[ERROR] 読み込みに失敗: $_"
    }
} | Out-Null

# 終了待ちループ
while ($true) {
    Start-Sleep -Seconds 1
}
