import os
import sys
import time
import json
import requests
from datetime import datetime, time as dtime

from config.logger import setup_logger
from config.settings import API_BASE_URL, FUTURE_CODE, get_api_password
from config.settings import ENABLE_TICK_OUTPUT

from client.kabu_websocket import KabuWebSocketClient
from handler.price_handler import PriceHandler
from writer.ohlc_writer import OHLCWriter
from writer.tick_writer import TickWriter
from utils.time_util import is_market_closed, get_exchange_code
from symbol_resolver import get_active_term, get_symbol_code

def get_token() -> str:
    """APIトークンを取得する"""
    url = f"{API_BASE_URL}/token"
    headers = {"Content-Type": "application/json"}
    payload = json.dumps({"APIPassword": get_api_password()})

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()["Token"]
    except Exception as e:
        print(f"[ERROR] トークン取得失敗: {e}")
        return None


def register_symbol(symbol_code: str, exchange_code: int, token: str) -> bool:
    """銘柄をKabuステーションに登録"""
    url = f"{API_BASE_URL}/register"
    headers = {"Content-Type": "application/json", "X-API-KEY": token}
    payload = {
        "Symbols": [
            {"Symbol": symbol_code, "Exchange": exchange_code}
        ]
    }

    try:
        response = requests.put(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print("[OK] 銘柄登録成功:", response.json())
        return True
    except Exception as e:
        print(f"[ERROR] 銘柄登録失敗: {e}")
        return False


def main():
    # カレントディレクトリ変更（スクリプトのある場所を基準に）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # ログ設定
    setup_logger()

    now = datetime.now()
    if is_market_closed(now):
        print("[INFO] 市場が閉まっています。終了します。")
        return

    token = get_token()
    if not token:
        return

    active_term = get_active_term(now)
    symbol_code = get_symbol_code(active_term, token)
    if not symbol_code:
        print("[ERROR] 銘柄コード取得失敗")
        return

    exchange_code = get_exchange_code(now)
    if not register_symbol(symbol_code, exchange_code, token):
        return

    # 初期化
    ohlc_writer = OHLCWriter()
    tick_writer = TickWriter() if ENABLE_TICK_OUTPUT else None
    price_handler = PriceHandler(ohlc_writer, tick_writer)


    # WebSocketクライアント起動
    ws_client = KabuWebSocketClient(price_handler)
    ws_client.start()

    try:
        while True:
            now = datetime.now().time()
            if now >= dtime(6, 5):
                print("[INFO] 午前6:05になったため、自動終了します。")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("[STOP] ユーザーによる終了要求")
    finally:
        price_handler.finalize_ohlc()
        ohlc_writer.close()
        if tick_writer:
            tick_writer.close()
        ws_client.stop()

if __name__ == "__main__":
    main()
