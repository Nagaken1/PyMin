import requests
import json

# キャッシュ（限月ごとの銘柄コード）
_symbol_cache = {}

API_BASE_URL = "http://localhost:18080/kabusapi"

# ------------------------------------------------------------------------------
# 関数名 : get_symbol_code
# 概　要 : 限月（YYYYMM）から銘柄コードを取得（キャッシュ付き）
# 引　数 :
#     term (str)  : 例 "202506"
#     token (str) : 認証トークン（main.py から受け取る）
# ------------------------------------------------------------------------------
def get_symbol_code(term: str, token: str) -> str:
    if term in _symbol_cache:
        return _symbol_cache[term]

    url = f"{API_BASE_URL}/symbolname/future"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": token
    }
    params = {
        "FutureCode": "NK225mini",  # ← 正しいFutureCode
        "DerivMonth": int(term)
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        symbol = data.get("Symbol")

        if not symbol:
            print(f"[ERROR] Symbolが取得できません。レスポンス: {data}", flush=True)
            return None

        _symbol_cache[term] = symbol
        return symbol

    except Exception as e:
        print(f"[ERROR] 銘柄コード取得失敗: {e}", flush=True)
        return None