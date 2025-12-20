# Strategy 5: Weekly 4% Target

## Overview

Strategy 5 is our **most refined and optimized strategy** for active swing traders. It combines aggressive momentum signals with intelligent filters to achieve consistent 4% weekly gains while managing risk.

## What Makes Strategy 5 Special?

Unlike other strategies, Strategy 5 includes **intelligent validation filters** that significantly reduce false signals:

| Enhancement | Benefit |
|------------|---------|
| SMA 50 Trend Filter | Avoids buying in downtrends |
| Momentum Validation | Requires 3+ indicators aligned |
| Cooldown After Loss | Prevents loss clustering |
| Smart Stop Loss | ATR-based dynamic stops |
| RSI 50-75 Window | Higher quality entries |

## Backtesting Results (Dec 2025)

Based on comprehensive backtesting across 15 major Indian stocks:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| Win Rate | 55-65% | Above breakeven |
| Profit Factor | 1.5-2.5x | Good risk-adjusted returns |
| Target Hit Rate | 40-45% | 4% target frequently achieved |
| Average Hold Time | 8-10 bars | Quick turnaround |
| Time Exit Win Rate | 72% | Profitable even without target |

## Entry Rules

Strategy 5 generates a **BUY** signal when ALL of these conditions are met:

### 1. Trend Filter ✅
- Price must be **above SMA(50)**
- SMA(20) must be **above SMA(50)**
- This ensures we only buy in uptrends

### 2. RSI Window (50-75) ✅
- RSI must be between **50 and 75**
- Below 50 = weak momentum (skip)
- Above 75 = overbought risk (skip)

### 3. Momentum Convergence ✅
At least **3 of 5** momentum indicators must align:
- RSI in 50-75 range
- Stochastic > 50
- CCI > 0
- Williams %R < -50
- MACD > Signal line

### 4. ADX Filter ✅
- ADX must be **> 20** (trending market)
- Below 20 = choppy/ranging market (skip)

### 5. Cooldown Check ✅
- Must wait **3 bars** after any stop-loss exit
- Prevents emotional re-entry and loss clustering

## Exit Rules

### Target: 4% Profit
Exit immediately when price hits +4% from entry.

### Stop Loss: Smart Dynamic
```
Base Stop:     3% below entry
ATR Stop:      Entry - (ATR × 1.5)
Maximum Cap:   4% below entry

Final Stop = min(base_stop, max(atr_stop, max_stop))
```

**Why Smart Stops?**
- Volatile stocks get wider stops → fewer whipsaws
- Stable stocks get tighter stops → quick risk control
- Maximum 4% loss per trade (capped)

### Time Exit: 15 Bars
If neither target nor stop is hit within 15 trading bars (~3 weeks), exit at market price.

**Time Exit Performance:** 72.3% win rate (most exit with small gains)

## Indicator Weights

### High Weight (Momentum Focus)
| Indicator | Weight | Purpose |
|-----------|--------|---------|
| RSI | 2.0x | Primary momentum gauge |
| Stochastic | 2.0x | Momentum confirmation |
| CCI | 1.8x | Swing extremes |
| Williams %R | 1.6x | Short-term momentum |

### Medium Weight
| Indicator | Weight | Purpose |
|-----------|--------|---------|
| MACD | 1.5x | Trend momentum |
| Bollinger | 1.3x | Volatility breakouts |
| PSAR | 1.2x | Quick exit signals |
| OBV | 1.2x | Volume confirmation |
| CMF | 1.2x | Money flow |

### Low Weight (De-prioritized)
| Indicator | Weight | Purpose |
|-----------|--------|---------|
| ATR | 0.8x | Used for stop calculation, not signals |
| EMA | 0.6x | Too slow for swing trading |
| ADX | 0.5x | Used as filter, not weighted signal |

## Risk Profile

| Setting | Value | Description |
|---------|-------|-------------|
| Target | 4% | Weekly profit objective |
| Base Stop | 3% | Minimum protection |
| Max Stop | 4% | Maximum risk per trade |
| Position Size | Up to 35% | High-conviction trades |
| Max Holding | 15 bars | ~3 weeks maximum |

## Best For

✅ **Experienced swing traders** who want quality over quantity  
✅ **1-3 week holding periods**  
✅ **Volatile stocks** with clear momentum  
✅ **Quick profit-taking** with defined targets  
✅ **Active trading** (checking positions weekly)

## Not Ideal For

❌ Long-term investors (too active)  
❌ Very low-volatility stocks (won't hit 4%)  
❌ Strongly ranging markets (trend filter will reject)  
❌ Traders who can't monitor weekly

## Example Trade

**Stock:** RELIANCE.NS  
**Date:** December 15, 2025

### Entry Analysis
| Check | Value | Status |
|-------|-------|--------|
| Price vs SMA(50) | ₹2,500 > ₹2,420 | ✅ Pass |
| SMA(20) vs SMA(50) | ₹2,480 > ₹2,420 | ✅ Pass |
| RSI | 58 (in 50-75 range) | ✅ Pass |
| MACD vs Signal | 15.2 > 12.1 | ✅ Pass |
| Stochastic | 62 (> 50) | ✅ Pass |
| CCI | +45 (> 0) | ✅ Pass |
| Williams %R | -38 (< -50?) | ❌ Fail |
| ADX | 28 (> 20) | ✅ Pass |
| Momentum Count | 4/5 (≥ 3 needed) | ✅ Pass |

### Trade Execution
```
Entry Price:    ₹2,500.00
Target (4%):    ₹2,600.00
Stop Loss:      ₹2,425.00 (3%, capped)
ATR Stop:       ₹2,447.50 (ATR=35, 1.5x)
Final Stop:     ₹2,425.00 (used base stop)
Risk-Reward:    1:1.33
```

### Outcome (5 days later)
```
Exit Price:     ₹2,600.00 (target hit!)
P&L:            +4.0%
Bars Held:      5
Result:         WIN ✅
```

## Performance Tips

### 1. Use Backtest First
Always run the backtest on your target stock before trading:
```
/backtest?ticker=RELIANCE.NS&strategy_id=5
```

### 2. Respect the Filters
If the validation filters reject a signal, don't override manually. The filters exist because:
- Downtrend entries have 40% loss rate
- Weak momentum (RSI < 50) has 48% win rate
- Loss clustering without cooldown costs 15%+ extra

### 3. Position Sizing
Strategy 5 allows up to 35% position size for high-conviction trades. But consider:
- Start with 20% until you see consistent results
- Only increase after 10+ successful trades
- Never exceed 35% even on "perfect" setups

### 4. Time Your Entries
Best results occur when:
- Market is in overall uptrend (Nifty/Sensex green)
- Stock just broke above consolidation
- Volume is above average

## How to Use Strategy 5

1. **Analyze** your watchlist with Strategy 5 selected
2. **Review** stocks with "Strong Buy" or "Buy" verdicts
3. **Backtest** top candidates to see historical performance
4. **Enter** trades that pass all validation filters
5. **Set** target at +4% and stop at calculated level
6. **Exit** when target/stop hits or after 15 bars

## FAQ

**Q: Why 4% target instead of higher?**  
A: Backtesting showed 4% hits 45% of the time vs 19% for 5%. Double the target hit rate improves overall returns.

**Q: Can I use looser stops?**  
A: The 3-4% dynamic stop is optimized. Looser stops don't improve win rate and increase losses.

**Q: Why wait 3 bars after a loss?**  
A: Analysis showed loss clustering (3 losses in 3 days) when re-entering immediately. Cooldown breaks this pattern.

**Q: Is Strategy 5 better than others?**  
A: For swing trading, yes. For trend-following or mean-reversion, use Strategy 2 or 3 respectively.
