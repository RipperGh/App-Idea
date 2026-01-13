from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExecutionMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class Market(str, Enum):
    EQUITIES = "equities"
    CRYPTO = "crypto"


@dataclass
class RiskParameters:
    stop_loss_pct: float
    take_profit_pct: float

    def validate(self) -> None:
        if self.stop_loss_pct <= 0 or self.take_profit_pct <= 0:
            raise ValueError("Stop-loss and take-profit must be greater than 0.")


@dataclass
class TradeDirective:
    symbol: str
    side: str
    quantity: float
    market: Market
    risk: RiskParameters


@dataclass
class TradeResult:
    accepted: bool
    message: str


class TradeExecutor:
    def __init__(self, mode: ExecutionMode) -> None:
        self._mode = mode

    @property
    def mode(self) -> ExecutionMode:
        return self._mode

    def submit(self, directive: TradeDirective) -> TradeResult:
        directive.risk.validate()
        if directive.side not in {"buy", "sell"}:
            return TradeResult(False, "Side must be 'buy' or 'sell'.")
        if directive.quantity <= 0:
            return TradeResult(False, "Quantity must be greater than 0.")
        if self._mode == ExecutionMode.LIVE:
            return self._submit_live(directive)
        return self._submit_paper(directive)

    def close_position(self, symbol: str, market: Market) -> TradeResult:
        if self._mode == ExecutionMode.LIVE:
            return self._close_live(symbol, market)
        return TradeResult(True, f"Paper close requested for {symbol} on {market.value}.")

    def _submit_paper(self, directive: TradeDirective) -> TradeResult:
        return TradeResult(
            True,
            (
                f"Paper trade queued: {directive.side} {directive.quantity} {directive.symbol} "
                f"with SL {directive.risk.stop_loss_pct:.2f}% and TP {directive.risk.take_profit_pct:.2f}%"
            ),
        )

    def _submit_live(self, directive: TradeDirective) -> TradeResult:
        return TradeResult(
            False,
            (
                "Live trading integration not configured. "
                "Wire Alpaca-py for equities and CCXT for crypto before enabling live mode."
            ),
        )

    def _close_live(self, symbol: str, market: Market) -> TradeResult:
        return TradeResult(
            False,
            (
                "Live close not configured. "
                "Wire Alpaca-py/CCXT close logic before enabling live mode."
            ),
        )
