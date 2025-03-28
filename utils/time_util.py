from datetime import datetime, time as dtime, timedelta


def is_market_closed(now: datetime) -> bool:
    """
    市場が一時的に閉じている時間帯かどうかを判定。
    - 日中 → 15:46〜16:58
    - 夜間 → 06:01〜08:43
    """
    t = now.time()
    return dtime(15, 46) <= t <= dtime(16, 58) or dtime(6, 1) <= t <= dtime(8, 43)


def get_exchange_code(now: datetime) -> int:
    """
    現在の時刻に応じて、kabuステーション用の取引所コードを返す。
    - 23: 日中（8:43〜15:47）
    - 24: 夜間（それ以外）
    """
    t = now.time()
    return 23 if dtime(8, 43) <= t <= dtime(15, 47) else 24


def is_closing_end(ts: datetime) -> bool:
    """
    クロージングセッションの終了直前の時刻かを判定する。
    - 日中クロージング → 15:59
    - 夜間クロージング → 5:59
    """
    t = ts.time()
    return t == dtime(15, 59) or t == dtime(5, 59)


def get_trade_date(now: datetime) -> datetime.date:
    """
    日経225miniなどの先物取引日（17:00起点）を返す。
    - 17:00以降：翌営業日扱い
    - 17:00未満：当日
    """
    return (now + timedelta(days=1)).date() if now.time() >= dtime(17, 0) else now.date()
