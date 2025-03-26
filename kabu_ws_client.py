import websocket
import threading
import json
import time
from datetime import datetime

class KabuWebSocketClient:
    def __init__(self, on_tick_callback):
        self.ws = None
        self.thread = None
        self.on_tick_callback = on_tick_callback
        self.running = False

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            price = data.get("CurrentPrice")
            timestamp_str = data.get("CurrentPriceTime")

            if price is not None and timestamp_str:
                #  ISO 8601 フォーマットをそのまま扱えるように修正
                timestamp = datetime.fromisoformat(timestamp_str)
                self.on_tick_callback(price, timestamp)

        except Exception as e:
            print("[ERROR] メッセージ処理エラー:", e, flush=True)

    def on_error(self, ws, error):
        print("[ERROR] WebSocket エラー:", error, flush=True)

    def on_close(self, ws, close_status_code, close_msg):
        print("[INFO] WebSocket 切断", flush=True)

    def on_open(self, ws):
        print("[INFO] WebSocket 接続成功", flush=True)

    def start(self):
        self.running = True
        def run():
            while self.running:
                try:
                    self.ws = websocket.WebSocketApp(
                        "ws://localhost:18080/kabusapi/websocket",
                        on_message=self.on_message,
                        on_error=self.on_error,
                        on_close=self.on_close,
                        on_open=self.on_open
                    )
                    self.ws.run_forever()
                except Exception as e:
                    print("[ERROR] 再接続エラー:", e, flush=True)
                    time.sleep(5)
        self.thread = threading.Thread(target=run)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()
        if self.thread:
            self.thread.join()
