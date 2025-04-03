import threading
import asyncio
import websockets
import json
from datetime import datetime

class DummyWebSocketClient:
    def __init__(self, handler, uri="ws://localhost:9000"):
        self.handler = handler
        self.uri = uri
        self.thread = threading.Thread(target=self._start_event_loop, daemon=True)

    def start(self):
        self.thread.start()

    def _start_event_loop(self):
        asyncio.run(self._run())

    async def _run(self):
        print(f"[MOCK WS] 接続: {self.uri}")
        try:
            async with websockets.connect(self.uri) as websocket:
                async for message in websocket:
                    tick = json.loads(message)

                    # 変数取り出し
                    price = float(tick["Price"])
                    timestamp = datetime.strptime(tick["Time"], "%Y-%m-%d %H:%M:%S")

                    # ✅ handle_tick を正しく呼び出す
                    self.handler.handle_tick(price, timestamp)

        except Exception as e:
            print(f"[MOCK WS] 接続エラー: {e}")
