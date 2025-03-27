from datetime import datetime


class OHLCBuilder:
    """
    ティックデータから1分足のOHLC（Open, High, Low, Close）を構築するクラス。
    クロージング補完などにも対応。
    """

    def __init__(self):
        self.current_minute = None
        self.ohlc = None
        self.first_price_of_next_session = None

    def update(self, price: float, timestamp: datetime) -> dict:
        """
        ティックを受信し、1分足のOHLCを更新。
        新しい1分が始まった場合は、直前のOHLCを返す。
        """
        minute = timestamp.replace(second=0, microsecond=0)

        # 最初の1本目
        if self.current_minute is None:
            self.current_minute = minute
            self.ohlc = {
                "time": minute,
                "open": price,
                "high": price,
                "low": price,
                "close": price
            }
            return None

        # 同じ1分内 → 更新のみ
        if minute == self.current_minute:
            self.ohlc["high"] = max(self.ohlc["high"], price)
            self.ohlc["low"] = min(self.ohlc["low"], price)
            self.ohlc["close"] = price
            return None

        # 1分経過 → 前のOHLCを返して、新しい足を作成
        completed = self.ohlc
        self.current_minute = minute
        self.ohlc = {
            "time": minute,
            "open": price,
            "high": price,
            "low": price,
            "close": price
        }
        return completed

    def _finalize_ohlc(self) -> dict:
        """
        強制終了時などに、現在構築中のOHLCを返す。
        """
        return self.ohlc

    def finalize_with_next_session_price(self, now: datetime) -> dict:
        """
        クロージング終了後、次セッションの最初の価格を使って
        1本分のダミーOHLCを出力（全値に同じ価格を適用）。
        """
        if self.first_price_of_next_session is None:
            return None

        minute = now.replace(second=0, microsecond=0)

        dummy = {
            "time": minute,
            "open": self.first_price_of_next_session,
            "high": self.first_price_of_next_session,
            "low": self.first_price_of_next_session,
            "close": self.first_price_of_next_session
        }

        self.first_price_of_next_session = None
        return dummy
