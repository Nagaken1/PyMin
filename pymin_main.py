import os
import sys
import time
import json
import requests
from datetime import datetime, time as dtime
from datetime import timedelta
import pandas as pd
import csv

from config.logger import setup_logger
from config.settings import API_BASE_URL, get_api_password
from config.settings import ENABLE_TICK_OUTPUT

from client.kabu_websocket import KabuWebSocketClient
from handler.price_handler import PriceHandler
from writer.ohlc_writer import OHLCWriter
from writer.tick_writer import TickWriter
from utils.time_util import get_exchange_code, get_trade_date, is_night_session
from symbol_resolver import get_active_term, get_symbol_code

def wait_for_latest_file_update(file_path: str, timeout: int = 5):
    """ファイルの更新を一定時間（秒）待機する。更新されたら True を返す。"""
    start_time = time.time()
    last_mtime = os.path.getmtime(file_path)
    last_size = os.path.getsize(file_path)

    while time.time() - start_time < timeout:
        current_mtime = os.path.getmtime(file_path)
        current_size = os.path.getsize(file_path)
        if current_mtime != last_mtime or current_size != last_size:
            print(f"[INFO] ファイル {file_path} が更新されました。")
            return True
        time.sleep(0.5)

    print(f"[WARNING] ファイル {file_path} に更新が検出されませんでした。")
    return False

def export_latest_minutes_from_files(base_dir: str, minutes: int = 3, output_file: str = "latest_ohlc.csv"):
    """
    ディレクトリ内のCSVファイルから、最新2つを読み込み、N分間のデータを抽出して出力。
    """
    try:
        files = [
            f for f in os.listdir(base_dir)
            if f.endswith("_nikkei_mini_future.csv") and f[:8].isdigit()
        ]

        if len(files) < 1:
            print("[警告] 対象CSVファイルが見つかりませんでした")
            return

        files_sorted = sorted(files, reverse=True)
        target_files = files_sorted[:2]

        # 最新ファイルの更新完了を待つ
        latest_file_path = os.path.join(base_dir, target_files[0])
        wait_for_latest_file_update(latest_file_path)

        combined_df = pd.DataFrame()

        for fname in reversed(target_files):
            path = os.path.join(base_dir, fname)
            try:
                temp_df = pd.read_csv(path)
                temp_df["Time"] = pd.to_datetime(temp_df["Time"])
                combined_df = pd.concat([combined_df, temp_df], ignore_index=True)
            except Exception as e:
                print(f"[警告] {fname} の読み込みに失敗: {e}")

        if combined_df.empty:
            print("[警告] ファイル読み込みに失敗しました")
            return

        latest_time = combined_df["Time"].max()
        start_time = latest_time - timedelta(minutes=minutes - 1)
        latest_df = combined_df[combined_df["Time"] >= start_time].copy()
        latest_df.sort_values("Time", inplace=True)

        # フォーマットを YYYY/MM/DD に戻す ← 修正箇所
        latest_df["Time"] = latest_df["Time"].dt.strftime("%Y/%m/%d %H:%M:%S")

        latest_df.to_csv(output_file, index=False)
        print(f"[更新] {output_file} に最新{minutes}分を書き出しました。")

    except Exception as e:
        print(f"[エラー] 処理中に例外が発生しました: {e}")

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

def export_connection_info(symbol_code: str, exchange_code: int, token: str, output_file: str = "connection_info.csv"):
    """
    symbol_code, exchange_code, token をCSVファイルに1行で出力する。
    """
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["SymbolCode", "ExchangeCode", "Token"])
            writer.writerow([symbol_code, exchange_code, token])
        print(f"[INFO] 接続情報を {output_file} に書き出しました。")
    except Exception as e:
        print(f"[ERROR] 接続情報の書き出しに失敗しました: {e}")

def main():
    now = datetime.now().replace(tzinfo=None)
    # カレントディレクトリ変更（スクリプトのある場所を基準に）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # ログ設定
    setup_logger()

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

    # 接続情報を出力
    export_connection_info(symbol_code, exchange_code, token)

    # 初期化
    ohlc_writer = OHLCWriter()
    tick_writer = TickWriter(enable_output=ENABLE_TICK_OUTPUT)
    price_handler = PriceHandler(ohlc_writer, tick_writer)
    last_export_minute = None

    trade_date = get_trade_date(datetime.now())
    END_TIME = datetime.combine(trade_date, dtime(6, 5)) if is_night_session(now) else None

    if END_TIME and datetime.now().replace(tzinfo=None) >= END_TIME:
        print("[INFO] すでに取引終了時刻を過ぎているため、起動せず終了します。")
        return

    # WebSocketクライアント起動
    ws_client = KabuWebSocketClient(price_handler)
    ws_client.start()

    try:
        while True:
            now = datetime.now().replace(tzinfo=None)

            if END_TIME and datetime.now().replace(tzinfo=None) >= END_TIME:
                print("[INFO] 取引終了時刻になったため、自動終了します。")
                break

            # 1分おきの書き出し処理
            if now.second == 1 and now.minute != last_export_minute:
                price_handler.fill_missing_minutes(now) #補完処理を呼び出し

                export_latest_minutes_from_files(
                    base_dir="csv",
                    minutes=3,
                    output_file="latest_ohlc.csv"
                )

                last_export_minute = now.minute

            time.sleep(1)

    finally:
        price_handler.finalize_ohlc()
        ohlc_writer.close()
        if tick_writer:
            tick_writer.close()
        ws_client.stop()

if __name__ == "__main__":

    main()
