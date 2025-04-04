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
        self._loop = None  # イベントループ保持用
        self._running = True

    def start(self):
        self.thread.start()

    def stop(self):
        print("[MOCK WS] DummyWebSocketClient を停止します")
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _start_event_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._run())

    async def _run(self):
        print(f"[MOCK WS] 接続: {self.uri}")
        try:
            async with websockets.connect(self.uri) as websocket:
                while self._running:
                    message = await websocket.recv()
                    tick = json.loads(message)

                    price = float(tick["Price"])
                    timestamp = datetime.strptime(tick["Time"], "%Y-%m-%d %H:%M:%S")

                    self.handler.handle_tick(price, timestamp)

        except Exception as e:
            print(f"[MOCK WS] 接続エラー: {e}")
