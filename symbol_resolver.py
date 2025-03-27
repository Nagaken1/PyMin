import requests
from config.settings import API_BASE_URL, FUTURE_CODE

# 銘柄コードキャッシュ
_symbol_cache = {}


def get_active_term(now) -> int:
    """
    現在の日付から、最も近い限月（YYYYMM）を返す。
    限月は3・6・9・12月（3の倍数）に切り上げ。
    """
    year = now.year
    month = now.month

    # 3の倍数の月へ切り上げ（3, 6, 9, 12）
    future_month = ((month - 1) // 3 + 1) * 3
    if future_month > 12:
        future_month -= 12
        year += 1

    return year * 100 + future_month


def get_symbol_code(term: int, token: str) -> str:
    """
    限月（YYYYMM）から銘柄コードを取得する。
    結果はキャッシュに保存して再利用。
    """
    if term in _symbol_cache:
        return _symbol_cache[term]

    url = f"{API_BASE_URL}/symbolname/future"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": token
    }
    params = {
        "FutureCode": FUTURE_CODE,
        "DerivMonth": term
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        symbol = response.json()["Symbol"]
        _symbol_cache[term] = symbol
        print(f"[DEBUG] 銘柄コード取得成功: {symbol}")
        return symbol
    except Exception as e:
        print(f"[ERROR] 銘柄コード取得失敗: {e}")
        return None
