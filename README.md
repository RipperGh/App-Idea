# Unified Quantitative Dashboard (Stocks + Crypto)

## Overview
A PyQt6-based quantitative dashboard skeleton that blends technical indicators, sentiment inputs, and liquidity signals into a probability overlay for both equities and crypto. It includes secure .env handling with encryption, a trade execution scaffold, and a GUI bootstrap featuring real-time data refresh via QThread.

## Project Structure
```
App-Idea/
├── app/
│   ├── __init__.py
│   ├── main.py                  # GUI bootstrap, master password prompt, worker startup
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── data_fetcher.py       # Mock fetcher (replace with Alpaca/CCXT)
│   │   └── decision_engine.py    # RSI/MACD/MFI + sentiment weighting logic
│   ├── execution/
│   │   ├── __init__.py
│   │   └── trade_executor.py     # Execution scaffold w/ risk checks & paper/live modes
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py        # QTabWidget + execution controls
│   │   └── market_tab.py         # Plotly chart + probability overlay + logic feed
│   └── security/
│       ├── __init__.py
│       └── env_crypto.py         # Encrypt/decrypt .env using Fernet
└── README.md
```

## Security Wrapper (.env encryption)
1. Create a `.env` file in the repo root with your Alpaca + CCXT keys.
2. Run the encryption script:
   ```bash
   python app/security/env_crypto.py
   ```
3. Store `.env.enc` and `.env.salt` securely. Remove plaintext `.env` after encrypting.
4. On app startup, the GUI prompts for the master password and decrypts secrets into memory only.

## Trade Execution (scaffold)
The `TradeExecutor` enforces mandatory stop-loss and take-profit inputs and supports paper vs. live mode. Live trade and close operations are stubbed until Alpaca-py (equities) and CCXT (crypto) wiring is added.

## Running the GUI
```bash
python app/main.py
```

## Notes
- Replace the mock data fetcher in `app/engine/data_fetcher.py` with Alpaca (equities) and CCXT (crypto) integrations.
- Sentiment is handled via VADER; swap in FinBERT if you need domain-specific modeling.
