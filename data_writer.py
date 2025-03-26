import os
import csv
from datetime import datetime, timedelta

class OHLCWriter:
    def __init__(self, output_dir="data"):
        """
        初期化処理

        Parameters:
            output_dir (str): 出力先ディレクトリ（デフォルト: "data"）
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.current_date = None           # 現在の取引日（YYYYMMDD）
        self.file_handle = None            # オープン中のファイルハンドル
        self.csv_writer = None             # csv.DictWriter オブジェクト

    def _get_trade_date(self, ts: datetime) -> str:
        """
        時刻に基づいて取引日（YYYYMMDD）を返す。
        17:00以降の夜間取引は「翌営業日」として処理。
        """
        if ts.time().hour >= 17:
            ts += timedelta(days=1)
        return ts.strftime("%Y%m%d")

    def _open_file_if_needed(self, ts: datetime):
        """
        新しい取引日が検出されたら、CSVファイルを切り替える。
        """
        trade_date = self._get_trade_date(ts)

        if trade_date != self.current_date:
            if self.file_handle:
                self.file_handle.close()

            self.current_date = trade_date
            filepath = os.path.join(self.output_dir, f"{trade_date}_nikkei_mini_future.csv")
            is_new = not os.path.exists(filepath)

            self.file_handle = open(filepath, "a", newline='', encoding="utf-8")
            self.csv_writer = csv.DictWriter(
                self.file_handle,
                fieldnames=["Timestamp", "Open", "High", "Low", "Close"]
            )

            if is_new:
                self.csv_writer.writeheader()

    def write_row(self, ohlc: dict):
        """
        OHLCデータを1行CSVに書き込む。

        Parameters:
            ohlc (dict): {"Timestamp": ISO文字列, "Open": float, ...}
        """
        # ISO 8601形式をサポートするように修正（+09:00対応）
        try:
            ts = datetime.fromisoformat(ohlc["Timestamp"])
        except Exception as e:
            print(f"[ERROR] Timestamp変換失敗: {ohlc['Timestamp']} → {e}", flush=True)
            return

        self._open_file_if_needed(ts)
        self.csv_writer.writerow(ohlc)
        self.file_handle.flush()  # 確実に保存

    def close(self):
        """
        ファイルを安全に閉じる
        """
        if self.file_handle:
            self.file_handle.close()
