
from writer.ohlc_writer import OHLCWriter
from writer.tick_writer import TickWriter
from ohlc_builder import OHLCBuilder
from utils.time_util import is_closing_end, is_market_closed
from datetime import datetime, timedelta, time as dtime
from symbol_resolver import get_active_term

class PriceHandler:
    """
    ティックを受信してOHLCを生成し、
    ファイルへの出力を管理するクラス。
    """
    def __init__(self, ohlc_writer: OHLCWriter, tick_writer: TickWriter):
        self.ohlc_builder = OHLCBuilder()
        self.ohlc_writer = ohlc_writer
        self.tick_writer = tick_writer
        self.last_written_minute = None
        self.first_ohlc_skipped = False

    def handle_tick(self, price: float, timestamp: datetime):

        # 限月をあらかじめ取得（常に必要なので）
        contract_month = get_active_term(timestamp)

        if self.tick_writer is not None:
            self.tick_writer.write_tick(price, timestamp)

        if (
            self.ohlc_builder.first_price_of_next_session is None
            and not is_closing_end(timestamp)
            and self.ohlc_builder.closing_completed_session != self.ohlc_builder._get_session_id(timestamp)
        ):
            self.ohlc_builder.first_price_of_next_session = price

        ohlc = self.ohlc_builder.update(price, timestamp, contract_month=contract_month)
        if ohlc:
            ohlc_time = ohlc["time"].replace(second=0, microsecond=0)

            ohlc["is_dummy"] = False  # 明示的に dummy でないことを付与
            ohlc["contract_month"] = contract_month

            # 最初の1分間はスキップして書き出さない
            if not self.first_ohlc_skipped:
                self.first_ohlc_skipped = True
                return

            if not self.last_written_minute or ohlc_time > self.last_written_minute:
                self.ohlc_writer.write_row(ohlc)
                self.last_written_minute = ohlc_time
                self.ohlc_builder.current_minute = ohlc_time  # B: 整合性を保つために current_minute を更新

#        dummy_ohlc = self.ohlc_builder.finalize_with_next_session_price(timestamp)
#        if dummy_ohlc:
#            dummy_time = dummy_ohlc["time"].replace(second=0, microsecond=0)
#            if not self.last_written_minute or dummy_time > self.last_written_minute:
#                self.ohlc_writer.write_row(dummy_ohlc)
#                self.last_written_minute = dummy_time
#                self.ohlc_builder.current_minute = dummy_time

    def fill_missing_minutes(self, now: datetime):
        if is_market_closed(now):
            return  # 市場休止中は何もしない

        if self.ohlc_builder.current_minute is None or self.ohlc_builder.ohlc is None:
            return

        last_minute = self.ohlc_builder.current_minute
        current_minute = now.replace(second=0, microsecond=0, tzinfo=None)

        # 補完処理で「直近の current_minute の1分後」を補完しないように明示的に制限
        if current_minute <= last_minute:
            return  # 同じ分内なら補完不要

        # まだ1分未満しか経っていない場合は補完しない（← NEW）
        if current_minute == last_minute + timedelta(minutes=1):
            return

        while last_minute + timedelta(minutes=1) < current_minute:
            last_minute += timedelta(minutes=1)
            last_close = self.ohlc_builder.ohlc["close"]

            dummy = {
                "time": last_minute,
                "open": last_close,
                "high": last_close,
                "low": last_close,
                "close": last_close,
                "is_dummy": True,
                "contract_month": "dummy"
            }

            dummy_time = dummy["time"].replace(second=0, microsecond=0)
            if not self.last_written_minute or dummy_time > self.last_written_minute:
                self.ohlc_writer.write_row(dummy)
                self.last_written_minute = dummy_time
                self.ohlc_builder.current_minute = dummy_time  # A: current_minute を進めて順序を保証
                self.ohlc_builder.ohlc = dummy
            else:
                break  # A: 順序・重複チェックのため break で終了

    def finalize_ohlc(self):
        final = self.ohlc_builder._finalize_ohlc()
        if final:
            final_time = final["time"].replace(second=0, microsecond=0)
            if not self.last_written_minute or final_time > self.last_written_minute:
                self.ohlc_writer.write_row(final)
                self.last_written_minute = final_time

        if self.tick_writer:
            self.tick_writer.close()
