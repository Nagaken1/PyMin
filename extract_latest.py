import os
import pandas as pd
from datetime import datetime, timedelta
import argparse

def get_latest_ohlc(count=10, data_dir="data"):
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    today_file = os.path.join(data_dir, today.strftime("%Y%m%d") + "_nikkei_mini_future.csv")
    yest_file = os.path.join(data_dir, yesterday.strftime("%Y%m%d") + "_nikkei_mini_future.csv")
    dfs = []
    if os.path.exists(yest_file):
        dfs.append(pd.read_csv(yest_file))
    if os.path.exists(today_file):
        dfs.append(pd.read_csv(today_file))
    if not dfs:
        print("[INFO] データなし", flush=True)
        return None
    df_all = pd.concat(dfs).reset_index(drop=True)
    return df_all.tail(count)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--output", type=str, default="latest.csv")
    args = parser.parse_args()
    df = get_latest_ohlc(args.count)
    if df is not None:
        df.to_csv(args.output, index=False)
        print(f"[OK] 出力成功: {args.output}", flush=True)
    else:
        print("[INFO] 出力なし")

if __name__ == "__main__":
    main()
