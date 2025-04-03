
from writer.ohlc_writer import OHLCWriter
from writer.tick_writer import TickWriter
from ohlc_builder import OHLCBuilder
from utils.time_util import is_closing_end, is_market_closed,is_pre_closing_minute
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
        self.latest_price = None
        self.latest_timestamp = None


    def handle_tick(self, price: float, timestamp: datetime):
        # Tickの最新情報を記録
        self.latest_price = price
        self.latest_timestamp = timestamp

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
            #print(f"[DEBUG] ohlc_time to write = {ohlc['time']}")

            #  出力対象は「現在のティックより1分以上前のOHLCのみ」
            current_tick_minute = timestamp.replace(second=0, microsecond=0, tzinfo=None)

            print(f"[DEBUG][handle_tick] ohlc_time = {ohlc_time}, current_tick_minute = {current_tick_minute}")
            print(f"[DEBUG][handle_tick] last_written_minute = {self.last_written_minute}")

            if ohlc_time >= current_tick_minute:
                # 未来または現在分 → まだ未確定なので書き込まない
                print(f"[SKIP][handle_tick] {ohlc_time} は現在分または未来分 → 未確定でスキップ")
                return

            ohlc["is_dummy"] = False  # 明示的に dummy でないことを付与
            ohlc["contract_month"] = contract_month

            # ログで追跡（デバッグ）
            print(f"[DEBUG] 完成した OHLC: {ohlc_time}, 値: {ohlc}")
            print(f"[DEBUG] 最後に書いた分: {self.last_written_minute}")

            #  重複防止：直前と同じ分は絶対書き込まない（イコールだけブロック、未来はOK）
            if self.last_written_minute and ohlc_time == self.last_written_minute:
                print(f"[SKIP] 重複のため {ohlc_time} をスキップ")
                return

            if not self.last_written_minute or ohlc_time > self.last_written_minute:
                self.ohlc_writer.write_row(ohlc)
                self.last_written_minute = ohlc_time
                self.ohlc_builder.current_minute = ohlc_time  # B: 整合性を保つために current_minute を更新

            print(f"[DEBUG][handle_tick] 確定 OHLC 書き込み: {ohlc_time}, 値: {ohlc}")
#        dummy_ohlc = self.ohlc_builder.finalize_with_next_session_price(timestamp)
#        if dummy_ohlc:
#            dummy_time = dummy_ohlc["time"].replace(second=0, microsecond=0)
#            if not self.last_written_minute or dummy_time > self.last_written_minute:
#                self.ohlc_writer.write_row(dummy_ohlc)
#                self.last_written_minute = dummy_time
#                self.ohlc_builder.current_minute = dummy_time

    def fill_missing_minutes(self, now: datetime):
        if is_market_closed(now):
            print(f"[DEBUG][fill_missing_minutes] 市場閉場中のため補完スキップ: {now}")
            return

        if self.ohlc_builder.current_minute is None or self.ohlc_builder.ohlc is None:
            print(f"[DEBUG][fill_missing_minutes] current_minute 未定義のため補完スキップ")
            return

        current_minute = now.replace(second=0, microsecond=0, tzinfo=None)
        last_minute = self.ohlc_builder.current_minute

        print(f"[DEBUG] fill_missing_minutes() 呼び出し")
        print(f"[DEBUG] last_ohlc.ohlc_time = {last_minute}")
        print(f"[DEBUG] current_minute = {current_minute}")
        print(f"[DEBUG] self.last_written_minute = {self.last_written_minute}")

        # last_written_minute を基準に補完スキップを判断
        if current_minute <= last_minute:
            print(f"[DEBUG][fill_missing_minutes] 補完不要: now={now}, current={current_minute}, last_written_minute={self.last_written_minute}")
            return

        while last_minute + timedelta(minutes=1) <= current_minute:
            print(f"[DEBUG][fill_missing_minutes] 補完開始: from {last_minute + timedelta(minutes=1)} to {current_minute - timedelta(minutes=1)}")
            next_minute = last_minute + timedelta(minutes=1)
            print(f"[TRACE] next_minute = {next_minute}")

            if is_market_closed(next_minute):
                print(f"[DEBUG][fill_missing_minutes] 補完対象が無音時間のためスキップ: {next_minute}")
                last_minute = next_minute
                continue

            last_minute = next_minute
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
            print(f"[TRACE] dummy_time = {dummy_time}, last_written_minute = {self.last_written_minute}")

            if not self.last_written_minute or dummy_time > self.last_written_minute:
                print(f"[DEBUG][fill_missing_minutes] ダミー補完: {dummy_time}")
                self.ohlc_writer.write_row(dummy)
                self.last_written_minute = dummy_time
                self.ohlc_builder.current_minute = dummy_time
                self.ohlc_builder.ohlc = dummy
            else:
                print(f"[DEBUG][fill_missing_minutes] 重複のため補完打ち切り: {dummy_time}")
                break

    def fill_pre_closing_minutes(self, timestamp: datetime):
        """
        プレクロージング時間帯（15:40〜15:44 または 5:55〜5:59）に、
        ダミーOHLCを5分分まとめて補完する。
        引数timestampは15:40または5:55のtick timestamp。
        """
        base_minute = timestamp.replace(second=0, microsecond=0)

        # すでに補完済みならスキップ（2回以上呼ばれないようにする）
        if self.last_written_minute and self.last_written_minute >= base_minute + timedelta(minutes=4):
            print(f"[SKIP] プレクロージング補完はすでに完了済み: {self.last_written_minute}")
            return

        if not is_pre_closing_minute(base_minute):
            print(f"[SKIP] プレクロージングの時間ではないため補完しません: {base_minute}")
            return

        last_close = self.ohlc_builder.ohlc["close"] if self.ohlc_builder.ohlc else 0
        for i in range(5):
            minute = base_minute + timedelta(minutes=i)
            dummy = {
                "time": minute,
                "open": last_close,
                "high": last_close,
                "low": last_close,
                "close": last_close,
                "is_dummy": True,
                "contract_month": "dummy"
            }

            if not self.last_written_minute or minute > self.last_written_minute:
                print(f"[PRE-CLOSING] ダミー補完: {minute}")
                self.ohlc_writer.write_row(dummy)
                self.last_written_minute = minute
                self.ohlc_builder.current_minute = minute
                self.ohlc_builder.ohlc = dummy
            else:
                print(f"[SKIP] 重複のため補完スキップ: {minute}")

    def finalize_ohlc(self):
        final = self.ohlc_builder._finalize_ohlc()
        if final:
            final_time = final["time"].replace(second=0, microsecond=0)
            if not self.last_written_minute or final_time > self.last_written_minute:
                print(f"[DEBUG][finalize_ohlc] 終了時最終OHLC書き込み: {final_time}")
                self.ohlc_writer.write_row(final)
                self.last_written_minute = final_time
            else:
                print(f"[DEBUG][finalize_ohlc] 重複でスキップ: {final_time}")
        else:
            print(f"[DEBUG][finalize_ohlc] 最終OHLCなし")

        if self.tick_writer:
            self.tick_writer.close()
