# スクリプトのある場所に移動
Set-Location -Path $PSScriptRoot

# 監視対象ファイルのフルパス
$filename = "latest_ohlc.csv"
$fullPath = Join-Path $PSScriptRoot $filename

# ファイル存在チェック
if (-not (Test-Path $fullPath)) {
    Write-Host "[警告] ファイルが見つかりません: $fullPath"
    exit
}

Write-Host "[INFO] ファイル変更を監視中: $fullPath"

# FileSystemWatcher の作成と設定
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = Split-Path $fullPath
$watcher.Filter = Split-Path $fullPath -Leaf
$watcher.NotifyFilter = [System.IO.NotifyFilters]'LastWrite'
$watcher.EnableRaisingEvents = $true

# イベント登録（ファイル変更時）
Register-ObjectEvent $watcher Changed -Action {
    Start-Sleep -Milliseconds 500  # 書き込み完了待ち
    try {
        Clear-Host
        Write-Host "[更新] $(Get-Date)"
        Get-Content $Event.SourceEventArgs.FullPath | Select-Object -Last 10
    } catch {
        Write-Host "[ERROR] 読み取り失敗: $_"
    }
} | Out-Null

# 無限ループで常駐（Ctrl + C で終了）
while ($true) {
    Start-Sleep -Seconds 1
}
