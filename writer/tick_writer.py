import os
import csv
from datetime import datetime


class TickWriter:
    """
    受信したすべてのティックデータ（価格・時刻）をCSVファイルに記録するクラス。
    日付ごとにファイルを分割し、「tick/」フォルダに保存する。
    """

    def __init__(self):
        self.current_date = None
        self.file = None
        self.writer = None
        self.file_path = None
        self._init_writer(datetime.now())

    def _init_writer(self, dt: datetime):
        """
        書き込み用のCSVファイルを日付に基づいて初期化する。
        """
        self.current_date = dt.date()
        date_str = self.current_date.strftime("%Y%m%d")
        tick_dir = "tick"
        os.makedirs(tick_dir, exist_ok=True)

        self.file_path = os.path.join(tick_dir, f"{date_str}_tick.csv")
        self.file = open(self.file_path, "a", newline="", encoding="utf-8")
        self.writer = csv.writer(self.file)

        # ヘッダーがなければ書く
        if os.stat(self.file_path).st_size == 0:
            self.writer.writerow(["Time", "Price"])

    def write_tick(self, price: float, timestamp: datetime):
        """
        ティック（価格と時刻）を1行書き込む。
        """
        if timestamp.date() != self.current_date:
            self.file.close()
            self._init_writer(timestamp)

        row = [
            timestamp.strftime("%Y/%m/%d %H:%M:%S"),
            price
        ]
        self.writer.writerow(row)
        self.file.flush()

    def close(self):
        """
        ファイルを閉じる。
        """
        if self.file:
            self.file.close()
