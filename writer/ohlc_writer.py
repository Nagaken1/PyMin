import os
import csv
from datetime import datetime


class OHLCWriter:
    """
    OHLCを日付ごとのCSVファイルに保存するクラス。
    ファイルは自動で切り替わり、1行ずつ追記される。
    """

    def __init__(self, output_dir="csv"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.current_date = None
        self.file = None
        self.writer = None

    def _open_new_file(self, date: datetime):
        """
        新しい日付のファイルを開く
        """
        if self.file:
            self.file.close()

        self.current_date = date
        date_str = date.strftime("%Y%m%d")
        filename = os.path.join(self.output_dir, f"{date_str}_nikkei_mini_future.csv")
        self.file = open(filename, "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)

        # ファイルが空ならヘッダーを書く
        if os.stat(filename).st_size == 0:
            self.writer.writerow(["Time", "Open", "High", "Low", "Close"])

    def write_row(self, ohlc: dict):
        """
        OHLCデータをCSVに1行書き込む
        """
        time: datetime = ohlc["time"]
        date_only = time.date()

        if self.current_date is None or self.current_date.date() != date_only:
            self._open_new_file(time)

        self.writer.writerow([
            time.strftime("%Y-%m-%d %H:%M:%S"),
            ohlc["open"],
            ohlc["high"],
            ohlc["low"],
            ohlc["close"]
        ])
        self.file.flush()

    def close(self):
        """
        ファイルを閉じる
        """
        if self.file:
            self.file.close()
            self.file = None
