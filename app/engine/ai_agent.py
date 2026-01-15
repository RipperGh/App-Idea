from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class AITradeContext:
    indicators: pd.DataFrame
    news_headlines: str
    portfolio_exposure: dict[str, Any]


@dataclass
class AITradeDecision:
    action: str
    confidence: float
    reasoning: str
    risk_limit: str

    def to_json(self) -> str:
        payload = {
            "action": self.action,
            "confidence": round(self.confidence, 2),
            "reasoning": self.reasoning,
            "risk_limit": self.risk_limit,
        }
        return json.dumps(payload)


class AITradingAgent:
    def __init__(self, api_client: Any | None = None) -> None:
        self._api_client = api_client

    def evaluate_trade(self, context: AITradeContext) -> AITradeDecision:
        technical_signal = self._technical_signal(context.indicators)
        sentiment_signal = self._sentiment_signal(context.news_headlines)

        if technical_signal == "BUY" and sentiment_signal == "STRONG_BEARISH":
            return AITradeDecision(
                action="HOLD",
                confidence=0.62,
                reasoning=(
                    "Safety Override: momentum is oversold but sentiment shows strong "
                    "bearish macro signal."
                ),
                risk_limit="2%",
            )

        if technical_signal == "SELL" and sentiment_signal == "STRONG_BULLISH":
            return AITradeDecision(
                action="HOLD",
                confidence=0.58,
                reasoning=(
                    "Safety Override: momentum is overbought but sentiment shows strong "
                    "bullish macro signal."
                ),
                risk_limit="2%",
            )

        decision = self._request_ai_decision(context, technical_signal, sentiment_signal)
        if decision is None:
            return AITradeDecision(
                action="HOLD",
                confidence=0.5,
                reasoning="Safety Override: AI API unavailable, defaulting to HOLD.",
                risk_limit="2%",
            )
        return decision

    def _technical_signal(self, indicators: pd.DataFrame) -> str:
        latest = indicators.iloc[-1]
        rsi = latest.get("rsi", 50)
        if rsi < 30:
            return "BUY"
        if rsi > 70:
            return "SELL"
        return "HOLD"

    def _sentiment_signal(self, headlines: str) -> str:
        bearish_terms = ["crisis", "selloff", "recession", "bear"]
        bullish_terms = ["rally", "breakout", "growth", "bull"]
        text = headlines.lower()
        bearish_hits = sum(term in text for term in bearish_terms)
        bullish_hits = sum(term in text for term in bullish_terms)
        if bearish_hits > bullish_hits and bearish_hits >= 2:
            return "STRONG_BEARISH"
        if bullish_hits > bearish_hits and bullish_hits >= 2:
            return "STRONG_BULLISH"
        return "NEUTRAL"

    def _request_ai_decision(
        self,
        context: AITradeContext,
        technical_signal: str,
        sentiment_signal: str,
    ) -> AITradeDecision | None:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a quantitative trading assistant. Return strict JSON with keys: "
                        "action, confidence, reasoning, risk_limit."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Technical signal: {technical_signal}. "
                        f"Sentiment signal: {sentiment_signal}. "
                        f"Portfolio exposure: {context.portfolio_exposure}."
                    ),
                },
            ],
        }

        if self._api_client is None:
            return None

        try:
            response = self._api_client.responses.create(**payload)
            raw = response.output_text
            parsed = json.loads(raw)
            return AITradeDecision(
                action=parsed.get("action", "HOLD"),
                confidence=float(parsed.get("confidence", 0.5)),
                reasoning=parsed.get("reasoning", ""),
                risk_limit=parsed.get("risk_limit", "2%"),
            )
        except Exception:
            return None
