from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import pandas_ta as ta
from nltk.sentiment.vader import SentimentIntensityAnalyzer


@dataclass
class DecisionInputs:
    prices: pd.DataFrame
    headlines: Iterable[str]


@dataclass
class DecisionOutput:
    technical_score: float
    sentiment_score: float
    money_flow_score: float
    decision_score: float
    bias_summary: str


class DecisionEngine:
    def __init__(self) -> None:
        self._sentiment = SentimentIntensityAnalyzer()

    def evaluate(self, inputs: DecisionInputs) -> DecisionOutput:
        indicators = self._calculate_indicators(inputs.prices)
        technical_score = self._technical_alignment_score(indicators)
        sentiment_score = self._sentiment_score(inputs.headlines)
        money_flow_score = float(indicators["mfi"].iloc[-1]) / 100.0
        decision_score = (
            technical_score * 0.4 + sentiment_score * 0.3 + money_flow_score * 0.3
        )
        bias_summary = self._build_bias_summary(
            indicators=indicators,
            sentiment_score=sentiment_score,
            technical_score=technical_score,
            money_flow_score=money_flow_score,
        )
        return DecisionOutput(
            technical_score=technical_score,
            sentiment_score=sentiment_score,
            money_flow_score=money_flow_score,
            decision_score=decision_score,
            bias_summary=bias_summary,
        )

    def _calculate_indicators(self, prices: pd.DataFrame) -> pd.DataFrame:
        df = prices.copy()
        df["rsi"] = ta.rsi(df["close"], length=14)
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        df["macd"] = macd["MACD_12_26_9"]
        df["macd_signal"] = macd["MACDs_12_26_9"]
        df["mfi"] = ta.mfi(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            volume=df["volume"],
            length=14,
        )
        return df.dropna().reset_index(drop=True)

    def _technical_alignment_score(self, indicators: pd.DataFrame) -> float:
        latest = indicators.iloc[-1]
        rsi_score = self._scale(latest["rsi"], 0, 100)
        macd_alignment = 1.0 if latest["macd"] > latest["macd_signal"] else 0.0
        return float(np.clip((rsi_score + macd_alignment) / 2.0, 0.0, 1.0))

    def _sentiment_score(self, headlines: Iterable[str]) -> float:
        scores = [self._sentiment.polarity_scores(text)["compound"] for text in headlines]
        if not scores:
            return 0.5
        normalized = [(score + 1) / 2 for score in scores]
        return float(np.clip(np.mean(normalized), 0.0, 1.0))

    def _build_bias_summary(
        self,
        indicators: pd.DataFrame,
        sentiment_score: float,
        technical_score: float,
        money_flow_score: float,
    ) -> str:
        latest = indicators.iloc[-1]
        sentiment_label = "Bullish" if sentiment_score > 0.6 else "Bearish" if sentiment_score < 0.4 else "Neutral"
        technical_label = "Aligned" if technical_score > 0.6 else "Mixed"
        mfi_label = "rising" if latest["mfi"] > indicators["mfi"].iloc[-2] else "falling"
        return (
            f"MFI is {mfi_label}; Sentiment is {sentiment_label}; "
            f"Technicals are {technical_label}."
        )

    @staticmethod
    def _scale(value: float, min_value: float, max_value: float) -> float:
        if max_value == min_value:
            return 0.0
        return float(np.clip((value - min_value) / (max_value - min_value), 0.0, 1.0))
