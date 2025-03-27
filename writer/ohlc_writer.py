import os
import csv
from datetime import datetime


class OHLCWriter:
    """
    1分足のOHLCデータをCSVファイルに出力するクラス。
    日付ごとにファイルを分け、フォルダ「data/」以下に保存。
    """

    def __init__(self):
        self.current_date = None
        self.file = None
        self.writer = None
        self.file_path = None
        self._init_writer(datetime.now())

    def _init_writer(self, dt: datetime):
        """
        指定した日時に基づき、新しいCSVファイルを初期化する。
        """
        self.current_date = dt.date()
        date_str = self.current_date.strftime("%Y%m%d")
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        self.file_path = os.path.join(data_dir, f"{date_str}_nikkei_mini_future.csv")
        self.file = open(self.file_path, "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)

        # ヘッダーがなければ書き込む
        if os.stat(self.file_path).st_size == 0:
            self.writer.writerow(["Time", "Open", "High", "Low", "Close"])

    def write_row(self, ohlc: dict):
        """
        OHLC1本分をCSVに書き出す。
        """
        dt = ohlc["time"]
        if dt.date() != self.current_date:
            self.file.close()
            self._init_writer(dt)

        row = [
            dt.strftime("%Y/%m/%d %H:%M"),
            ohlc["open"],
            ohlc["high"],
            ohlc["low"],
            ohlc["close"]
        ]
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        """
        ファイルを安全に閉じる。
        """
        if self.file:
            self.file.close()
