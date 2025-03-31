from datetime import datetime, timedelta, time


class OHLCBuilder:
    """
    ティックデータから1分足のOHLCを構築するクラス。
    日中・夜間セッションごとにクロージング補完に対応。
    """

    def __init__(self):
        self.current_minute = None
        self.ohlc = None
        self.first_price_of_next_session = None
        self.closing_completed_session = None  # ← セッション単位で記録

    def update(self, price: float, timestamp: datetime, contract_month=None) -> dict:
        """
        ティックを受信してOHLCを更新。新しい1分が始まったら前のOHLCを返す。
        """
        minute = timestamp.replace(second=0, microsecond=0, tzinfo=None)

        if self.current_minute is None:
            self.current_minute = minute
            self.ohlc = {
                "time": minute,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "is_dummy": False,
                "contract_month": contract_month
            }
            return self.ohlc

        if minute == self.current_minute:
            self.ohlc["high"] = max(self.ohlc["high"], price)
            self.ohlc["low"] = min(self.ohlc["low"], price)
            self.ohlc["close"] = price
            return None

        completed = self.ohlc
        self.current_minute = minute
        self.ohlc = {
            "time": minute,
            "open": price,
            "high": price,
            "low": price,
            "close": price,
            "is_dummy": False,
            "contract_month": contract_month
        }
        return completed

    def _finalize_ohlc(self) -> dict:
        return self.ohlc

    def finalize_with_next_session_price(self, now: datetime) -> dict:
        """
        セッション終了後、次セッションの最初の価格でダミーOHLCを生成。
        同一セッションでの多重補完を防ぐ。
        """
        session_id = self._get_session_id(now)

        if self.first_price_of_next_session is None or self.closing_completed_session == session_id:
            return None

        minute = now.replace(second=0, microsecond=0, tzinfo=None)

        dummy = {
            "time": minute,
            "open": self.first_price_of_next_session,
            "high": self.first_price_of_next_session,
            "low": self.first_price_of_next_session,
            "close": self.first_price_of_next_session,
            "is_dummy": True,
            "contract_month": "dummy"
        }

        self.first_price_of_next_session = None
        self.closing_completed_session = session_id  # ← セッション単位でフラグON
        return dummy

    def _get_session_id(self, dt: datetime) -> str:
        """
        日中・夜間セッションごとのIDを返す。
        """
        t = dt.time()

        if t < time(6, 0):
            # 深夜は前日夜間セッションに属する
            session_date = (dt - timedelta(days=1)).date()
            session_type = "night"
        elif t < time(15, 30):
            session_date = dt.date()
            session_type = "day"
        else:
            session_date = dt.date()
            session_type = "night"

        return f"{session_date.strftime('%Y%m%d')}_{session_type}"
