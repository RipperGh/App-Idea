from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass
class MarketSnapshot:
    prices: pd.DataFrame
    headlines: Iterable[str]


class MockMarketDataFetcher:
    def __init__(self, symbol: str) -> None:
        self._symbol = symbol
        self._seed = np.random.default_rng()

    def fetch(self) -> MarketSnapshot:
        now = datetime.utcnow()
        timestamps = [now - timedelta(minutes=15 * i) for i in range(60)][::-1]
        base_price = 100 + self._seed.normal(0, 0.5)
        prices = [base_price]
        for _ in range(1, len(timestamps)):
            prices.append(prices[-1] + self._seed.normal(0, 0.8))
        close = np.array(prices)
        high = close + np.abs(self._seed.normal(0.2, 0.1, size=len(close)))
        low = close - np.abs(self._seed.normal(0.2, 0.1, size=len(close)))
        volume = self._seed.integers(1000, 5000, size=len(close))
        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "open": close,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            }
        )
        headlines = [
            f"{self._symbol} sees institutional accumulation amid macro uncertainty",
            f"Analysts review {self._symbol} momentum as volume trends shift",
        ]
        return MarketSnapshot(prices=df, headlines=headlines)
