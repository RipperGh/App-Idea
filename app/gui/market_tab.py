from __future__ import annotations

from dataclasses import dataclass

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView

import plotly.graph_objects as go


@dataclass
class MarketTabState:
    probability: float = 0.0


class MarketTab(QtWidgets.QWidget):
    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = MarketTabState()
        self._title = title
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        header = QtWidgets.QLabel(self._title)
        header.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header.setStyleSheet("font-size: 18px; font-weight: 600;")

        self.chart = QWebEngineView()
        self.chart.setMinimumHeight(360)

        gauge_layout = QtWidgets.QHBoxLayout()
        gauge_label = QtWidgets.QLabel("Probability Overlay")
        self.probability_bar = QtWidgets.QProgressBar()
        self.probability_bar.setRange(0, 100)
        self.probability_bar.setValue(0)
        self.probability_bar.setFormat("%p% Confidence")

        gauge_layout.addWidget(gauge_label)
        gauge_layout.addWidget(self.probability_bar)

        self.logic_feed = QtWidgets.QTextEdit()
        self.logic_feed.setReadOnly(True)
        self.logic_feed.setPlaceholderText("Logic feed will describe the decision bias.")

        layout.addWidget(header)
        layout.addWidget(self.chart)
        layout.addLayout(gauge_layout)
        layout.addWidget(QtWidgets.QLabel("Logic Feed"))
        layout.addWidget(self.logic_feed)

    def update_chart(self, timestamps: list[str], prices: list[float]) -> None:
        fig = go.Figure(
            data=[go.Scatter(x=timestamps, y=prices, mode="lines", name="Price")]
        )
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=20),
            template="plotly_dark",
        )
        html = fig.to_html(include_plotlyjs="cdn")
        self.chart.setHtml(html)

    def update_probability(self, probability: float) -> None:
        self.state.probability = probability
        self.probability_bar.setValue(int(probability * 100))

    def update_logic_feed(self, message: str) -> None:
        self.logic_feed.setPlainText(message)
