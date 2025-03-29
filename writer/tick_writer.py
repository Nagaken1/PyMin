import os
import csv
from datetime import datetime


class TickWriter:
    """
    受信したすべてのティックデータ（価格・時刻）をCSVファイルに記録するクラス。
    日付ごとにファイルを分割し、「tick/」フォルダに保存する。
    """

    def __init__(self, enable_output=True):
        self.enable_output = enable_output
        self.current_date = datetime.now().date()

        # Tick 出力ファイルの初期化
        self.file = None
        self.writer = None
        if self.enable_output:
            date_str = self.current_date.strftime("%Y%m%d")
            tick_dir = "tick"
            os.makedirs(tick_dir, exist_ok=True)

            self.file_path = os.path.join(tick_dir, f"{date_str}_tick.csv")
            self.file = open(self.file_path, "a", newline="", encoding="utf-8")
            self.writer = csv.writer(self.file)

            if os.stat(self.file_path).st_size == 0:
                self.writer.writerow(["Time", "Price"])

        #  first_tick 出力ファイルの初期化（常に記録）
        self.first_file = None
        self.first_writer = None
        self.first_file_path = os.path.join("tick", f"{self.current_date.strftime('%Y%m%d')}_first_tick.csv")
        os.makedirs("tick", exist_ok=True)
        self.first_file = open(self.first_file_path, "a", newline="", encoding="utf-8")
        self.first_writer = csv.writer(self.first_file)

        if os.stat(self.first_file_path).st_size == 0:
            self.first_writer.writerow(["Time", "Price"])

        self.last_written_minute = None  # 1分ごとの重複記録防止用

    def write_tick(self, price, timestamp: datetime):
        """
        TickデータをCSVファイルに追記する。日付が変わった場合は新しいファイルに切り替える。
        """

        # 日付が変わったらファイルを切り替える
        if timestamp.date() != self.current_date:
            if self.enable_output and self.file:
                self.file.close()
                date_str = timestamp.strftime("%Y%m%d")
                tick_dir = "tick"
                self.file_path = os.path.join(tick_dir, f"{date_str}_tick.csv")
                self.file = open(self.file_path, "a", newline="", encoding="utf-8")
                self.writer = csv.writer(self.file)
                if os.stat(self.file_path).st_size == 0:
                    self.writer.writerow(["Time", "Price"])

            if self.first_file:
                self.first_file.close()
            self.first_file_path = os.path.join("tick", f"{timestamp.strftime('%Y%m%d')}_first_tick.csv")
            self.first_file = open(self.first_file_path, "a", newline="", encoding="utf-8")
            self.first_writer = csv.writer(self.first_file)
            if os.stat(self.first_file_path).st_size == 0:
                self.first_writer.writerow(["Time", "Price"])

            self.current_date = timestamp.date()
            self.last_written_minute = None  # 日付変更時は最初のTick記録履歴をリセット

        # 書き込む内容を準備
        row = [timestamp.strftime("%Y/%m/%d %H:%M:%S"), price]

        #  first_tick は常に記録（1分ごとに1回だけ）
        tick_minute = timestamp.replace(second=0, microsecond=0)
        if self.last_written_minute != tick_minute:
            self.first_writer.writerow(row)
            self.first_file.flush()
            self.last_written_minute = tick_minute

        # 通常のTick出力（有効時のみ）
        if self.enable_output and self.writer:
            self.writer.writerow(row)
            self.file.flush()

    def close(self):
        """
        ファイルを閉じる。
        """
        if self.file:
            self.file.close()
        if self.first_file:
            self.first_file.close()