from datetime import datetime, time as dtime, timedelta

def is_closing_session(ts: datetime) -> bool:
    t = ts.time()
    return (
        dtime(15, 40) <= t < dtime(15, 45) or
        dtime(5, 55) <= t < dtime(6, 0)
    )

def is_closing_start(ts: datetime) -> bool:
    t = ts.time()
    return t in [dtime(15, 40), dtime(5, 55)]

def is_closing_end(ts: datetime) -> bool:
    t = ts.time()
    return t in [dtime(15, 44), dtime(5, 59)]