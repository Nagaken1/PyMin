import os
import time
import pandas as pd
from datetime import datetime, timedelta, time as dtime
from handler.price_handler import PriceHandler
from writer.ohlc_writer import OHLCWriter
from writer.tick_writer import TickWriter
from utils.time_util import get_exchange_code
from kabu_websocket import KabuWebSocket
from symbol_resolver import resolve_symbol


def export_latest_minutes_from_files(base_dir: str, minutes: int = 30, output_file: str = "latest_ohlc.csv"):
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

        latest_df.to_csv(output_file, index=False)
        print(f"[更新] {output_file} に最新{minutes}分を書き出しました。")

    except Exception as e:
        print(f"[エラー] 処理中に例外が発生しました: {e}")


def main():
    symbol = resolve_symbol()
    exchange_code = get_exchange_code(datetime.now())

    ohlc_writer = OHLCWriter()
    tick_writer = TickWriter()
    price_handler = PriceHandler(ohlc_writer, tick_writer)

    ws = KabuWebSocket(symbol, exchange_code, price_handler)
    ws.start()

    last_export_minute = None

    try:
        while True:
            now = datetime.now()
            price_handler.fill_missing_minutes(now)

            # 1分おきの書き出し処理
            if now.second == 0 and now.minute != last_export_minute:
                export_latest_minutes_from_files(
                    base_dir="csv",
                    minutes=30,
                    output_file="latest_ohlc.csv"
                )
                last_export_minute = now.minute

            # 終了条件（例：6:05に終了）
            if now.time() >= dtime(6, 5):
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("[終了] Ctrl+C により停止します")
    finally:
        price_handler.finalize_ohlc()
        ws.stop()


if __name__ == "__main__":
    main()
