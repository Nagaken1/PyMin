from datetime import datetime

class OHLCBuilder:
    def __init__(self):
        self.current_minute = None
        self.buffer = []

    def update(self, price: float, timestamp: datetime):
        minute = timestamp.replace(second=0, microsecond=0)
        if self.current_minute is None:
            self.current_minute = minute

        if minute != self.current_minute:
            ohlc = self._finalize_ohlc()
            self.current_minute = minute
            self.buffer = [(price, timestamp)]
            return ohlc
        else:
            self.buffer.append((price, timestamp))
            return None

    def _finalize_ohlc(self):
        if not self.buffer:
            return None
        prices = [p for p, _ in self.buffer]
        timestamp = self.current_minute.strftime("%Y-%m-%d %H:%M")
        return {
            "Timestamp": timestamp,
            "Open": prices[0],
            "High": max(prices),
            "Low": min(prices),
            "Close": prices[-1],
        }
