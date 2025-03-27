from datetime import datetime
from datetime import timedelta
from writer.ohlc_writer import OHLCWriter
from writer.tick_writer import TickWriter
from ohlc_builder import OHLCBuilder
from utils.time_util import is_closing_end

class PriceHandler:
    """
    ティック（現値）を受信して OHLC を生成し、
    OHLCWriter と TickWriter に出力を行う責任を持つクラス。
    """

    def __init__(self, ohlc_writer: OHLCWriter, tick_writer: TickWriter):
        self.ohlc_builder = OHLCBuilder()
        self.ohlc_writer = ohlc_writer
        self.tick_writer = tick_writer

    def handle_tick(self, price: float, timestamp: datetime):
        """
        ティックを受信したときに呼ばれるメイン処理
        """
        # ティックそのものを記録
        # --- ティック記録（tick_writer が有効なときだけ）
        if self.tick_writer is not None:
            self.tick_writer.write_tick(price, timestamp)

        # クロージングセッション開始前に次価格を記憶
        if self.ohlc_builder.first_price_of_next_session is None and not is_closing_end(timestamp):
            self.ohlc_builder.first_price_of_next_session = price

        # OHLCを更新
        ohlc = self.ohlc_builder.update(price, timestamp)
        if ohlc:
            self.ohlc_writer.write_row(ohlc)

        # クロージング終了時の補完
        dummy_ohlc = self.ohlc_builder.finalize_with_next_session_price(timestamp)
        if dummy_ohlc:
            self.ohlc_writer.write_row(dummy_ohlc)

    def finalize_ohlc(self):
        """
        強制終了時などに最後の未出力OHLCを保存
        """
        final = self.ohlc_builder._finalize_ohlc()
        if final:
            self.ohlc_writer.write_row(final)
        if self.tick_writer:
            self.tick_writer.close()

    def fill_missing_minutes(self, now: datetime):
    #"""
    #Tickが来なかった1分間のOHLCを補完して出力する。
    #"""
        if self.ohlc_builder.current_minute is None:
            return

        last_minute = self.ohlc_builder.current_minute
        current_minute = now.replace(second=0, microsecond=0, tzinfo=None)

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

            self.ohlc_writer.write_row(dummy)
            # current_minuteも更新（念のため）
            self.ohlc_builder.current_minute = last_minute
            self.ohlc_builder.ohlc = dummy