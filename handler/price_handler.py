from datetime import datetime, timedelta
from writer.ohlc_writer import OHLCWriter
from writer.tick_writer import TickWriter
from ohlc_builder import OHLCBuilder
from utils.time_util import is_closing_end


class PriceHandler:
    """
    ティックを受信してOHLCを生成し、
    ファイルへの出力を管理するクラス。
    """

    def __init__(self, ohlc_writer: OHLCWriter, tick_writer: TickWriter):
        self.ohlc_builder = OHLCBuilder()
        self.ohlc_writer = ohlc_writer
        self.tick_writer = tick_writer
        self.last_written_minute = None  # 重複出力ガード用

    def handle_tick(self, price: float, timestamp: datetime):
        """
        ティック受信時のメイン処理
        """
        # ティック記録
        if self.tick_writer is not None:
            self.tick_writer.write_tick(price, timestamp)

        # 次セッションの始値候補を記録（closing未完了時のみ）
        if (self.ohlc_builder.first_price_of_next_session is None
            and not is_closing_end(timestamp)
            and self.ohlc_builder.closing_completed_session != self.ohlc_builder._get_session_id(timestamp)):
            self.ohlc_builder.first_price_of_next_session = price

        # OHLC更新
        ohlc = self.ohlc_builder.update(price, timestamp)
        if ohlc and ohlc["time"] != self.last_written_minute:
            self.ohlc_writer.write_row(ohlc)
            self.last_written_minute = ohlc["time"]

        # クロージング補完
        dummy_ohlc = self.ohlc_builder.finalize_with_next_session_price(timestamp)
        if dummy_ohlc and dummy_ohlc["time"] != self.last_written_minute:
            self.ohlc_writer.write_row(dummy_ohlc)
            self.last_written_minute = dummy_ohlc["time"]

    def fill_missing_minutes(self, now: datetime):
        """
        Tickが来なかった1分間のOHLCを補完出力する
        """
        if self.ohlc_builder.current_minute is None or self.ohlc_builder.ohlc is None:
            return

        last_minute = self.ohlc_builder.current_minute
        current_minute = now.replace(second=0, microsecond=0, tzinfo=None)

        # 欠損分をループで補完
        while last_minute + timedelta(minutes=1) < current_minute:
            last_minute += timedelta(minutes=1)
            last_close = self.ohlc_builder.ohlc["close"]

            dummy = {
                "time": last_minute,
                "open": last_close,
                "high": last_close,
                "low": last_close,
                "close": last_close
            }

            if dummy["time"] != self.last_written_minute:
                self.ohlc_writer.write_row(dummy)
                self.last_written_minute = dummy["time"]

            # ビルダー状態を更新（次の補完の基準となる）
            self.ohlc_builder.current_minute = last_minute
            self.ohlc_builder.ohlc = dummy

    def finalize_ohlc(self):
        """
        強制終了時などに未出力OHLCを保存
        """
        final = self.ohlc_builder._finalize_ohlc()
        if final and final["time"] != self.last_written_minute:
            self.ohlc_writer.write_row(final)
            self.last_written_minute = final["time"]

        if self.tick_writer:
            self.tick_writer.close()
