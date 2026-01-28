# Jalshi - Kalshi BTC HFT Trading System

A Python trading system for Kalshi BTC 15-minute contracts with strong safety guardrails.

## Project Structure

```
jalshi/
├── src/
│   ├── api/          # Kalshi API client (authentication, rate limiting)
│   ├── model/        # Strategy development (BTC analysis, trading signals)
│   ├── core/         # Shared utilities (safety, configuration)
│   └── trading/      # Trade execution with guardrails
├── tests/            # Test suite
├── scripts/          # Utility scripts (backtesting)
└── notebooks/        # Jupyter notebooks for exploration
```

## Quick Start

### 1. Set Up Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (IMPORTANT for security!)
pre-commit install
```

### 2. Configure Credentials

```bash
# Copy the example config
cp .env.example .env

# Edit .env with your Kalshi API credentials
# Get credentials from: https://kalshi.com/account/api
```

### 3. Run the Backtest

```bash
python scripts/run_backtest.py
```

## For Strategy Developers (Model Side)

If you're working on the trading strategy, you only need to work in `src/model/`.

**Start here:**
1. Read `src/model/README.md` for a beginner-friendly guide
2. Look at `src/model/strategy.py` for the example strategy
3. Use helper functions from `src/model/btc_analyzer.py`

You don't need to worry about:
- API calls or authentication
- Rate limiting
- Safety mechanisms
- Actually placing orders

All of that is handled automatically!

## Safety Features

This project has multiple layers of protection:

| Feature | Description | Default |
|---------|-------------|---------|
| DRY_RUN | Orders are logged but not executed | ON |
| Confirmations | Interactive prompt before trades | ON |
| Environment | Defaults to development mode | development |
| Daily Loss Limit | Circuit breaker for losses | $50 |
| Order Size Limit | Max single order size | $10 |
| Pre-commit Hooks | Block commits with secrets | Enabled |
| GitHub Actions | Scan for secrets on push | Enabled |

### Enabling Live Trading

Live trading requires multiple explicit steps:

```bash
# 1. Set environment to production
export KALSHI_ENV=production

# 2. Confirm you understand the risks
export KALSHI_PRODUCTION_CONFIRMED=yes_i_understand_this_is_real_money

# 3. Disable dry run in your code
from src.core.safety import get_safety_config
config = get_safety_config()
config.dry_run = False
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .
```

### Security Scanning

```bash
# Check for secrets in git history
gitleaks detect

# Check for vulnerable dependencies
pip-audit
safety check
```

## API Reference

### Creating a Strategy

```python
from src.model.strategy import BaseStrategy, TradingSignal, Signal

class MyStrategy(BaseStrategy):
    def analyze(self, btc_prices, market_data):
        # Your analysis here...
        return TradingSignal(
            signal=Signal.BUY,  # or SELL or HOLD
            confidence=0.6,
            reason="My reason for this trade"
        )
```

### Using the API Client

```python
from src.api import KalshiClient

# Readonly client (for fetching data)
client = KalshiClient.from_env(readonly=True)
markets = client.get_markets()

# Write client (for placing orders - use with caution!)
client = KalshiClient.from_env(readonly=False)
```

## License

Private - not for distribution.
