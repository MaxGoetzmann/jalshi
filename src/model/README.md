# Model Module - Strategy Development Guide

Welcome! This folder is where you'll build your trading strategy.
Don't worry if you've never coded before - I've tried to make everything
as simple and well-documented as possible.

## Quick Start

### 1. Understand the Files

```
src/model/
├── __init__.py       # Ignore this (just Python boilerplate)
├── strategy.py       # WHERE YOU WRITE YOUR STRATEGY
├── btc_analyzer.py   # Helper functions you can use
└── README.md         # You're reading this!
```

### 2. Look at the Example

Open `strategy.py` and find the `ExampleStrategy` class. This shows you
the pattern you need to follow. Your job is to:

1. Create a new class that inherits from `BaseStrategy`
2. Implement the `analyze()` method
3. Return a `TradingSignal`

### 3. Create Your Strategy

Here's the simplest possible strategy:

```python
from src.model.strategy import BaseStrategy, TradingSignal, Signal

class MyStrategy(BaseStrategy):
    def analyze(self, btc_prices, market_data):
        # Always hold (do nothing) - safest possible strategy!
        return TradingSignal(
            signal=Signal.HOLD,
            confidence=0.5,
            reason="I'm being cautious"
        )
```

## Understanding the Inputs

Your `analyze()` method receives two arguments:

### `btc_prices` - List of Recent BTC Prices

```python
btc_prices = [65000.0, 65100.0, 65050.0, 65200.0]
#             oldest -----------------------> newest
```

- The **last** price is the most recent
- Use these to calculate trends, volatility, etc.
- The helper functions in `btc_analyzer.py` work with this format

### `market_data` - Current Kalshi Market Info

```python
market_data = {
    'yes_bid': 45,          # Best bid for YES contracts (cents)
    'yes_ask': 47,          # Best ask for YES contracts (cents)
    'no_bid': 52,           # Best bid for NO contracts (cents)
    'no_ask': 55,           # Best ask for NO contracts (cents)
    'strike_price': 65500,  # The target BTC price
    'expiry_minutes': 12,   # Minutes until contract expires
}
```

**What do these mean?**

- `yes_bid`/`yes_ask`: If you think BTC will be ABOVE strike, buy YES
- `no_bid`/`no_ask`: If you think BTC will be BELOW strike, buy NO
- Prices are in cents (1-99), representing probability (50 cents = 50%)

## Using the Helper Functions

The `btc_analyzer.py` file has useful functions you can use:

```python
from src.model.btc_analyzer import (
    calculate_variance,
    calculate_sharpe_ratio,
    detect_trend,
    estimate_probability,
    calculate_edge,
)

class MyStrategy(BaseStrategy):
    def analyze(self, btc_prices, market_data):
        # Calculate some useful metrics
        variance = calculate_variance(btc_prices)
        trend = detect_trend(btc_prices)
        sharpe = calculate_sharpe_ratio(btc_prices)

        # Estimate probability
        prob = estimate_probability(
            current_price=btc_prices[-1],  # Most recent price
            strike_price=market_data['strike_price'],
            std_dev=calculate_standard_deviation(btc_prices),
            minutes_to_expiry=market_data['expiry_minutes']
        )

        # Calculate edge
        edge = calculate_edge(prob, market_data['yes_ask'])

        # Make a decision based on your analysis
        if edge > 5 and trend == "up":
            return TradingSignal(
                signal=Signal.BUY,
                confidence=0.6,
                reason=f"Edge: {edge:.1f}%, trend: {trend}"
            )
        else:
            return TradingSignal(
                signal=Signal.HOLD,
                confidence=0.5,
                reason=f"No clear opportunity. Edge: {edge:.1f}%"
            )
```

## Understanding the Output

Your strategy must return a `TradingSignal`:

```python
TradingSignal(
    signal=Signal.BUY,     # BUY, SELL, or HOLD
    confidence=0.6,        # 0.0 to 1.0 (0.5 = unsure, 0.8 = confident)
    reason="My reason",    # Why you made this decision (for debugging)
    fair_price=55.0,       # Optional: what you think the fair price is
)
```

**The three signals:**
- `Signal.BUY` = Buy YES contracts (you think price will be ABOVE strike)
- `Signal.SELL` = Buy NO contracts (you think price will be BELOW strike)
- `Signal.HOLD` = Do nothing (no clear opportunity - **this is the safe default!**)

## Tips for Beginners

1. **Start with HOLD**: Your first strategy should return HOLD most of the time.
   Only signal BUY or SELL when you're confident.

2. **Test with fake money first**: The system has safety modes that prevent
   real trading. Use them!

3. **Print statements are your friend**: Add `print()` statements to see
   what your code is doing:
   ```python
   print(f"BTC prices: {btc_prices}")
   print(f"Variance: {variance}")
   print(f"My decision: {signal}")
   ```

4. **Use the Jupyter notebooks**: The `notebooks/` folder is a great place
   to experiment with data analysis before putting it in your strategy.

5. **Ask questions!**: If you're stuck, ask your brother. That's what he's
   there for!

## Common Mistakes to Avoid

- **Don't overthink it**: Start simple and add complexity later
- **Don't trade too often**: HOLD is usually the right answer
- **Don't use high confidence**: Even if you're sure, use 0.6-0.7, not 0.9+
- **Don't forget to test**: Run your strategy with fake data first

## Next Steps

1. Read through `btc_analyzer.py` to understand the helper functions
2. Copy `ExampleStrategy` and modify it
3. Test your strategy in a notebook
4. When ready, your brother will help you connect it to real data

Good luck! 🎯
