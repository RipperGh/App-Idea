from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PyQt6 import QtCore, QtWidgets

from app.engine.data_fetcher import MarketSnapshot, MockMarketDataFetcher
from app.engine.decision_engine import DecisionEngine, DecisionInputs
from app.gui.market_tab import MarketTab


@dataclass
class MarketUpdate:
    timestamps: list[str]
    prices: list[float]
    probability: float
    logic: str


class MarketWorker(QtCore.QThread):
    update_signal = QtCore.pyqtSignal(MarketUpdate)

    def __init__(self, symbol: str, refresh_interval: float = 5.0) -> None:
        super().__init__()
        self._symbol = symbol
        self._refresh_interval = refresh_interval
        self._engine = DecisionEngine()
        self._fetcher = MockMarketDataFetcher(symbol)
        self._running = True

    def run(self) -> None:
        while self._running:
            snapshot = self._fetcher.fetch()
            update = self._process_snapshot(snapshot)
            self.update_signal.emit(update)
            self.msleep(int(self._refresh_interval * 1000))

    def stop(self) -> None:
        self._running = False

    def _process_snapshot(self, snapshot: MarketSnapshot) -> MarketUpdate:
        decision = self._engine.evaluate(
            DecisionInputs(prices=snapshot.prices, headlines=snapshot.headlines)
        )
        timestamps = [ts.strftime("%H:%M") for ts in snapshot.prices["timestamp"]]
        prices = snapshot.prices["close"].round(2).tolist()
        return MarketUpdate(
            timestamps=timestamps,
            prices=prices,
            probability=decision.decision_score,
            logic=decision.bias_summary,
        )


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Unified Quantitative Dashboard")
        self.resize(1200, 800)

        self._tabs = QtWidgets.QTabWidget()
        self._equities_tab = MarketTab("Market: Equities")
        self._crypto_tab = MarketTab("Market: Crypto")
        self._tabs.addTab(self._equities_tab, "Market: Equities")
        self._tabs.addTab(self._crypto_tab, "Market: Crypto")

        self._controls = self._build_controls()

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(self._controls)
        layout.addWidget(self._tabs)
        self.setCentralWidget(central_widget)

        self._equities_worker = MarketWorker("AAPL")
        self._crypto_worker = MarketWorker("BTCUSD")
        self._equities_worker.update_signal.connect(
            lambda update: self._apply_update(self._equities_tab, update)
        )
        self._crypto_worker.update_signal.connect(
            lambda update: self._apply_update(self._crypto_tab, update)
        )

    def _build_controls(self) -> QtWidgets.QWidget:
        container = QtWidgets.QGroupBox("Execution & Risk Controls")
        layout = QtWidgets.QHBoxLayout(container)

        self.trading_mode = QtWidgets.QComboBox()
        self.trading_mode.addItems(["Paper Trading", "Live Trading"])

        self.stop_loss = QtWidgets.QDoubleSpinBox()
        self.stop_loss.setRange(0.1, 100.0)
        self.stop_loss.setSuffix(" %")
        self.stop_loss.setValue(2.0)

        self.take_profit = QtWidgets.QDoubleSpinBox()
        self.take_profit.setRange(0.1, 100.0)
        self.take_profit.setSuffix(" %")
        self.take_profit.setValue(5.0)

        layout.addWidget(QtWidgets.QLabel("Mode"))
        layout.addWidget(self.trading_mode)
        layout.addWidget(QtWidgets.QLabel("Stop-Loss"))
        layout.addWidget(self.stop_loss)
        layout.addWidget(QtWidgets.QLabel("Take-Profit"))
        layout.addWidget(self.take_profit)
        layout.addStretch()

        return container

    def start_workers(self) -> None:
        self._equities_worker.start()
        self._crypto_worker.start()

    def closeEvent(self, event: QtCore.QEvent) -> None:
        self._equities_worker.stop()
        self._crypto_worker.stop()
        self._equities_worker.wait()
        self._crypto_worker.wait()
        super().closeEvent(event)

    @staticmethod
    def _apply_update(tab: MarketTab, update: MarketUpdate) -> None:
        tab.update_chart(update.timestamps, update.prices)
        tab.update_probability(update.probability)
        tab.update_logic_feed(update.logic)
