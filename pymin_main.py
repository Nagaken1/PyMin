from term_utils import get_active_term
from symbol_resolver import get_symbol_code
from kabu_ws_client import KabuWebSocketClient
from ohlc_builder import OHLCBuilder
from data_writer import OHLCWriter, TickWriter
from auth import get_token

from datetime import datetime, time as dtime
import requests
import json
import time

import os
import sys
from datetime import datetime

# スクリプトのある場所を基準にする（絶対パス化）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# ログディレクトリ作成
log_dir = "PyMin_log"
os.makedirs(log_dir, exist_ok=True)

# 実行日付でログファイル名を作成
log_date = datetime.now().strftime("%Y%m%d")
log_file_path = os.path.join(log_dir, f"{log_date}_PyMin_log.txt")

# 出力をファイルとコンソールの両方に
class DualLogger:
    def __init__(self, log_file):
        self.terminal = sys.__stdout__
        self.log = open(log_file, "a", encoding="utf-8")
        self.buffer = ""

    def write(self, message):
        self.buffer += message

        # 行末の \n が来たときに初めて1行完成とみなす
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            timestamp = datetime.now().strftime("[%Y/%m/%d %H:%M:%S] ")
            full_line = timestamp + line + "\n"

            self.terminal.write(full_line)
            self.log.write(full_line)

    def flush(self):
        if self.buffer:
            timestamp = datetime.now().strftime("[%Y/%m/%d %H:%M:%S] ")
            full_line = timestamp + self.buffer
            self.terminal.write(full_line)
            self.log.write(full_line)
            self.buffer = ""

        self.terminal.flush()
        self.log.flush()

# 出力をタイムスタンプ付きに変更
sys.stdout = DualLogger(log_file_path)
sys.stderr = sys.stdout

API_BASE_URL = "http://localhost:18080/kabusapi"

def is_market_closed(now: datetime) -> bool:
    t = now.time()
    return dtime(15, 46) <= t <= dtime(16, 58) or dtime(6, 1) <= t <= dtime(8, 43)

def get_exchange_code(now: datetime) -> int:
    t = now.time()
    return 23 if dtime(8, 43) <= t <= dtime(15, 47) else 24

def register_symbol(symbol_code, exchange_code, token):
    url = f"{API_BASE_URL}/register"
    headers = {"Content-Type": "application/json", "X-API-KEY": token}
    payload = {"Symbols": [{"Symbol": symbol_code, "Exchange": exchange_code}]}
    res = requests.put(url, headers=headers, data=json.dumps(payload))
    if res.status_code != 200:
        print("[ERROR] 銘柄登録失敗:", res.status_code, res.text, flush=True)
        return False
    print("[OK] 登録成功:", res.json(), flush=True)
    return True

def main():
    now = datetime.now()
    if is_market_closed(now):
        print("[INFO] 市場が閉じています。終了します。", flush=True)
        return

    token = get_token()
    if not token:
        return

    term = get_active_term(now)
    symbol = get_symbol_code(term, token)
    if not symbol:
        print("[ERROR] 銘柄コード取得失敗", flush=True)
        return

    exchange = get_exchange_code(now)
    if not register_symbol(symbol, exchange, token):
        return

    builder = OHLCBuilder()
    writer = OHLCWriter()
    tick_writer = TickWriter()#←ティック記録が不要ならコメントアウトする

    def on_tick(price, ts):

        #ティックをそのまま記録（すべての価格を確実に残す）
        tick_writer.write_tick(price, ts)#←ティック記録が不要ならコメントアウトする

        ohlc = builder.update(price, ts)
        if ohlc:
            writer.write_row(ohlc)

    client = KabuWebSocketClient(on_tick)
    client.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[STOP] 終了中...", flush=True)
        final = builder._finalize_ohlc()
        if final:
            writer.write_row(final)
        writer.close()
        client.stop()

if __name__ == "__main__":
    main()
