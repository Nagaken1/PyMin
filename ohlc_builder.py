from datetime import datetime
from market_time_utils import is_closing_start, is_closing_end

class OHLCBuilder:
    def __init__(self):
        self.current_minute = None
        self.prices = []
        self.last_price = None
        self.closing_buffer = {}  # クロージング補完用
        self.first_price_of_next_session = None

    def update(self, price: float, ts: datetime):
        print(f"[DEBUG] update called: {ts} / price: {price}", flush=True)

        minute = ts.replace(second=0, microsecond=0)
        if self.current_minute and minute != self.current_minute:
            print(f"[DEBUG] New minute: {minute}, finalizing previous minute: {self.current_minute}", flush=True)
            ohlc = self._finalize_ohlc()
            self.current_minute = minute
            self.prices = [price]
            return ohlc

        self.current_minute = minute if self.current_minute is None else self.current_minute
        self.prices.append(price)
        return None

    def _finalize_ohlc(self):
        if self.prices and self.current_minute:
            return self._build_ohlc_from_prices(self.prices, self.current_minute)

    def _build_ohlc_from_prices(self, prices, minute, is_dummy=False):
        return {
            "Timestamp": minute.isoformat(sep=" ", timespec="minutes"),
            "Open": prices[0],
            "High": max(prices),
            "Low": min(prices),
            "Close": prices[-1],
            "IsDummy": is_dummy
        }

    def _build_ohlc(self, price, minute, is_dummy=True):
        return {
            "Timestamp": minute.isoformat(sep=" ", timespec="minutes"),
            "Open": price,
            "High": price,
            "Low": price,
            "Close": price,
            "IsDummy": is_dummy
        }

    def finalize_with_next_session_price(self, ts: datetime):
        """クロージング終了時に、次セッションの初ティックからOHLC補完"""
        if self.first_price_of_next_session and is_closing_end(ts):
            minute = ts.replace(second=0, microsecond=0)
            return self._build_ohlc(self.first_price_of_next_session, minute, is_dummy=True)
        return None
