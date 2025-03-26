import os
import csv
from datetime import datetime, timedelta

class OHLCWriter:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.current_date = None
        self.file_handle = None
        self.csv_writer = None

    def _get_trade_date(self, ts: datetime) -> str:
        # プレマーケット・夜間は「前日」とする
        if ts.time() < dtime(8, 45):
            ts -= timedelta(days=1)
        return ts.strftime("%Y%m%d")

    def _open_file_if_needed(self, ts: datetime):
        trade_date = self._get_trade_date(ts)
        if trade_date != self.current_date:
            if self.file_handle:
                self.file_handle.close()

            self.current_date = trade_date
            filepath = os.path.join(self.output_dir, f"{trade_date}_nikkei_mini_future.csv")
            is_new = not os.path.exists(filepath)

            self.file_handle = open(filepath, "a", newline='', encoding="utf-8")
            self.csv_writer = csv.DictWriter(self.file_handle,
                                             fieldnames=["Timestamp", "Open", "High", "Low", "Close", "IsDummy"])
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
        self.file_handle.flush()

    def close(self):
        if self.file_handle:
            self.file_handle.close()


class TickWriter:
    """
    すべてのティック（現値＋時刻）を記録するCSV出力用クラス
    """
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.current_date = None
        self.file_handle = None
        self.csv_writer = None

    def _get_trade_date(self, ts: datetime) -> str:
        if ts.time().hour >= 17:
            ts += timedelta(days=1)
        return ts.strftime("%Y%m%d")

    def _open_file_if_needed(self, ts: datetime):
        trade_date = self._get_trade_date(ts)

        if trade_date != self.current_date:
            if self.file_handle:
                self.file_handle.close()

            self.current_date = trade_date
            filepath = os.path.join(self.output_dir, f"{trade_date}_ticks.csv")
            is_new = not os.path.exists(filepath)

            self.file_handle = open(filepath, "a", newline='', encoding="utf-8")
            self.csv_writer = csv.DictWriter(self.file_handle, fieldnames=["Timestamp", "Price"])
            if is_new:
                self.csv_writer.writeheader()

    def write_tick(self, price: float, ts: datetime):
        self._open_file_if_needed(ts)
        self.csv_writer.writerow({
            "Timestamp": ts.isoformat(sep=" ", timespec="seconds"),
            "Price": price
        })
        self.file_handle.flush()

    def close(self):
        if self.file_handle:
            self.file_handle.close()
