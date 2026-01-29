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
        self._dashboard_tab = self._build_dashboard_tab()
        self._macro_tab = self._build_macro_tab()
        self._equities_tab = MarketTab("Market: Equities")
        self._crypto_tab = MarketTab("Market: Crypto")
        self._tabs.addTab(self._dashboard_tab, "Dashboard")
        self._tabs.addTab(self._macro_tab, "Macro Pulse")
        self._tabs.addTab(self._equities_tab, "Market: Equities")
        self._tabs.addTab(self._crypto_tab, "Market: Crypto")

        self._controls = self._build_controls()
        self._search_bar = self._build_search_bar()

        central_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.addWidget(self._search_bar)
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

    def _build_search_bar(self) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.asset_search = QtWidgets.QLineEdit()
        self.asset_search.setPlaceholderText("Search asset for fact sheet...")
        search_button = QtWidgets.QPushButton("Search")
        search_button.clicked.connect(self._show_fact_sheet)

        layout.addWidget(QtWidgets.QLabel("Universal Search"))
        layout.addWidget(self.asset_search)
        layout.addWidget(search_button)
        layout.addStretch()

        return container

    def _build_dashboard_tab(self) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)

        tables_layout = QtWidgets.QHBoxLayout()
        self.stocks_table = self._create_ranking_table(
            title="Stocks (Options Bias)",
            columns=["Ticker", "IV Rank", "Expected Value", "Auto-Trade", "Direction", "Kill Switch"],
        )
        self.crypto_table = self._create_ranking_table(
            title="Crypto (Momentum Bias)",
            columns=["Ticker", "24h Z-Score", "Mean Reversion", "Auto-Trade", "Direction", "Kill Switch"],
        )
        tables_layout.addWidget(self.stocks_table["container"])
        tables_layout.addWidget(self.crypto_table["container"])

        layout.addLayout(tables_layout)
        return container

    def _build_macro_tab(self) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)

        self.yield_curve_label = QtWidgets.QLabel("Yield Curve (10Y-2Y): awaiting data")
        self.fear_greed_label = QtWidgets.QLabel("Sentiment Gauge: awaiting data")
        self.ai_reasoner_log = QtWidgets.QTextEdit()
        self.ai_reasoner_log.setReadOnly(True)
        self.ai_reasoner_log.setPlaceholderText("AI Reasoner Log will stream decision context.")

        layout.addWidget(self.yield_curve_label)
        layout.addWidget(self.fear_greed_label)
        layout.addWidget(QtWidgets.QLabel("AI Reasoner Log"))
        layout.addWidget(self.ai_reasoner_log)

        return container

    def _create_ranking_table(self, title: str, columns: list[str]) -> dict[str, QtWidgets.QWidget]:
        container = QtWidgets.QGroupBox(title)
        layout = QtWidgets.QVBoxLayout(container)

        table = QtWidgets.QTableWidget(0, len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)

        self._seed_table_rows(table, title)
        return {"container": container, "table": table}

    def _seed_table_rows(self, table: QtWidgets.QTableWidget, title: str) -> None:
        sample_rows = [
            ("AAPL", "62", "0.18"),
            ("MSFT", "55", "0.12"),
        ]
        if "Crypto" in title:
            sample_rows = [
                ("BTCUSD", "1.8", "0.32"),
                ("ETHUSD", "-0.6", "0.27"),
            ]

        for ticker, metric_a, metric_b in sample_rows:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(ticker))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(metric_a))
            table.setItem(row, 2, QtWidgets.QTableWidgetItem(metric_b))

            auto_trade = QtWidgets.QCheckBox()
            auto_trade.setChecked(False)
            table.setCellWidget(row, 3, auto_trade)

            direction = QtWidgets.QComboBox()
            direction.addItems(["Long", "Short", "Both"])
            table.setCellWidget(row, 4, direction)

            kill_switch = QtWidgets.QPushButton("Kill Switch")
            kill_switch.clicked.connect(lambda _, symbol=ticker: self._kill_switch(symbol))
            table.setCellWidget(row, 5, kill_switch)

    def _show_fact_sheet(self) -> None:
        query = self.asset_search.text().strip().upper()
        if not query:
            QtWidgets.QMessageBox.information(self, "Fact Sheet", "Enter a symbol to query.")
            return
        fact_sheet = (
            f"Asset: {query}\n"
            "Class: Equity/Crypto\n"
            "Margin Requirement: 50%\n"
            "30-Day Volatility: 0.32"
        )
        QtWidgets.QMessageBox.information(self, f"Fact Sheet: {query}", fact_sheet)

    def _kill_switch(self, symbol: str) -> None:
        QtWidgets.QMessageBox.warning(
            self,
            "Kill Switch",
            f"Kill Switch triggered for {symbol}.",
        )

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
