# スクリプトのある場所に移動
Set-Location -Path $PSScriptRoot

# 監視対象ファイル
$targetFile = Join-Path $PSScriptRoot "latest_ohlc.csv"

# ファイル存在チェック
if (-Not (Test-Path $targetFile)) {
    Write-Host "[警告] ファイル $targetFile が見つかりません。"
    exit
}

Write-Host "[INFO] ファイル変更を監視中: $targetFile"
Write-Host "[INFO] 変更が検出されると、最新10行を表示します。"

# ファイルシステム監視オブジェクトの作成
$fsw = New-Object IO.FileSystemWatcher (Split-Path $targetFile), (Split-Path $targetFile -Leaf)
$fsw.NotifyFilter = [IO.NotifyFilters]'LastWrite'
$fsw.EnableRaisingEvents = $true

# イベント登録（Action内は複数行で安全に）
Register-ObjectEvent $fsw Changed -Action {
    Start-Sleep -Milliseconds 100  # 書き込み完了待ち（重要）
    Clear-Host
    Write-Host "[更新] $(Get-Date)"
    Get-Content $using:targetFile -Tail 10
} | Out-Null

# 無限ループで常駐（終了するまで）
while ($true) {
    Start-Sleep -Seconds 1
}
