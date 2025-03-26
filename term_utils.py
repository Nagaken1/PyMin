from datetime import datetime, time, timedelta

# ------------------------------------------------------------------------------
# メジャーSQがある月（3・6・9・12月）
# ------------------------------------------------------------------------------
SQ_MONTHS = [3, 6, 9, 12]

# ------------------------------------------------------------------------------
# 関数名 : get_major_sqd
# 概　要 : 指定された年月におけるメジャーSQ日（第2金曜日）を求める
# ------------------------------------------------------------------------------
def get_major_sqd(year, month):
    first_day = datetime(year, month, 1)
    weekday = first_day.weekday()
    days_until_friday = (4 - weekday) % 7  # 金曜=4
    first_friday = first_day + timedelta(days=days_until_friday)
    second_friday = first_friday + timedelta(days=7)
    return second_friday

# ------------------------------------------------------------------------------
# 関数名 : get_near_term
# 概　要 : 現在時点で有効な「期近」限月（YYYYMM）を返す
#          - SQ日を過ぎていたら自動的に次の限月に進める
# ------------------------------------------------------------------------------
def get_near_term(now: datetime) -> str:
    year = now.year
    month = now.month
    future_month = ((month - 1) // 3 + 1) * 3

    term = f"{year}{future_month:02d}"

    # SQ日を取得して、過ぎていれば次の限月へ進める
    sq_day = get_major_sqd(year, future_month)
    if now.date() >= sq_day.date():
        return get_next_term(now)

    return term

# ------------------------------------------------------------------------------
# 関数名 : get_next_term
# 概　要 : 「期近」の次の限月（期先）を返す
# ------------------------------------------------------------------------------
def get_next_term(now: datetime) -> str:
    near_term = get_near_term_basic(now)  # 再帰しない基本版を使用
    year = int(near_term[:4])
    month = int(near_term[4:])

    month += 3
    if month > 12:
        month -= 12
        year += 1

    return f"{year}{month:02d}"

# ------------------------------------------------------------------------------
# 関数名 : get_near_term_basic
# 概　要 : SQ日判定なしで単純に「期近」限月を求める（内部利用用）
# ------------------------------------------------------------------------------
def get_near_term_basic(now: datetime) -> str:
    year = now.year
    month = now.month
    future_month = ((month - 1) // 3 + 1) * 3

    if future_month > 12:
        future_month -= 12
        year += 1

    return f"{year}{future_month:02d}"

# ------------------------------------------------------------------------------
# 関数名 : is_sqd_eve
# 概　要 : メジャーSQの「前日」であるかを判定（3・6・9・12月限定）
# ------------------------------------------------------------------------------
def is_sqd_eve(now: datetime) -> bool:
    near_term = get_near_term(now)
    year = int(near_term[:4])
    month = int(near_term[4:])

    if month not in SQ_MONTHS:
        return False

    sq_day = get_major_sqd(year, month)
    return now.date() == (sq_day - timedelta(days=1)).date()

# ------------------------------------------------------------------------------
# 関数名 : get_active_term
# 概　要 : 期近 or 期先どちらを使用すべきか判断して返す
#          - メジャーSQ前日の 8:45〜15:45 は「期先」
#          - それ以外は「期近」
# ------------------------------------------------------------------------------
def get_active_term(now: datetime) -> str:
    if is_sqd_eve(now):
        if time(8, 45) <= now.time() <= time(15, 45):
            return get_next_term(now)
    return get_near_term(now)