# スクリプトのある場所に移動
Set-Location -Path $PSScriptRoot

# 監視対象ファイル
$targetFile = Join-Path $PSScriptRoot "latest_ohlc.csv"

if (-Not (Test-Path $targetFile)) {
    Write-Host "[警告] ファイル $targetFile が見つかりません。"
    exit
}

Write-Host "[INFO] ファイル変更を監視中: $targetFile"
Write-Host "[INFO] 変更が検出されると、最新10行を表示します。"

$fsw = New-Object IO.FileSystemWatcher (Split-Path $targetFile), (Split-Path $targetFile -Leaf)
$fsw.NotifyFilter = [IO.NotifyFilters]'LastWrite'
$fsw.EnableRaisingEvents = $true

Register-ObjectEvent $fsw Changed -Action {
    try {
        Start-Sleep -Milliseconds 500  # 書き込み完了待ちを少し長めに
        Clear-Host
        Write-Host "[更新] $(Get-Date)"
        Write-Host "---------- 最新データ ----------"
        Get-Content $using:targetFile | Select-Object -Last 10
        Write-Host "--------------------------------"
    } catch {
        Write-Host "[ERROR] 読み込みに失敗: $_"
    }
} | Out-Null

while ($true) {
    Start-Sleep -Seconds 1
}
