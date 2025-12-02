# Strategy 1: Balanced Analysis

## Overview

Strategy 1 is the **default strategy** that gives equal weight to all 12 technical indicators. It provides a comprehensive, unbiased view of the market without favoring any particular trading style.

## When to Use

- **General Market Scanning**: When you want a balanced view across all indicator types
- **Beginners**: Good starting point to understand how different indicators contribute
- **Unclear Market Conditions**: When you're unsure if the market is trending or ranging
- **Baseline Comparison**: Use as a reference point before trying specialized strategies

## Indicator Weights

All indicators have **equal weight (1.0)**:

### Trend Indicators
| Indicator | Weight | Purpose |
|-----------|--------|---------|
| MACD | 1.0 | Trend momentum and direction |
| ADX | 1.0 | Trend strength measurement |
| EMA Crossover | 1.0 | Trend confirmation via moving averages |
| Parabolic SAR | 1.0 | Trend reversal detection |

### Momentum Indicators
| Indicator | Weight | Purpose |
|-----------|--------|---------|
| RSI | 1.0 | Overbought/oversold conditions |
| Stochastic | 1.0 | Momentum exhaustion |
| CCI | 1.0 | Cyclical price movements |
| Williams %R | 1.0 | Short-term momentum |

### Volatility Indicators
| Indicator | Weight | Purpose |
|-----------|--------|---------|
| Bollinger Bands | 1.0 | Price deviation from mean |
| ATR | 1.0 | Volatility measurement |

### Volume Indicators
| Indicator | Weight | Purpose |
|-----------|--------|---------|
| OBV | 1.0 | Volume accumulation/distribution |
| CMF | 1.0 | Money flow direction |

## Risk Profile

| Setting | Value | Description |
|---------|-------|-------------|
| Stop Loss | 2% | Standard stop loss from entry |
| Target Multiplier | 2x | Target = 2× risk (1:2 risk-reward) |
| Max Position Size | 20% | Maximum 20% of capital per trade |

## How It Works

1. **All 12 indicators** are calculated for the stock
2. Each indicator votes: **Buy (+1)**, **Sell (-1)**, or **Neutral (0)**
3. Votes are weighted equally and summed
4. Final score determines verdict:
   - **Score ≥ 60**: Strong Buy
   - **Score ≥ 20**: Buy
   - **Score -20 to 20**: Hold
   - **Score ≤ -20**: Sell
   - **Score ≤ -60**: Strong Sell

## Best For

✅ General market analysis  
✅ Learning how indicators work together  
✅ When market direction is unclear  
✅ Diversified portfolio scanning  

## Limitations

❌ May give conflicting signals in transitional markets  
❌ Doesn't emphasize any particular trading style  
❌ May underperform in strongly trending or ranging markets  

## Example Use Case

> "I want to scan my watchlist and get a balanced view of each stock without bias toward trend-following or mean-reversion strategies."

Use Strategy 1 as your starting point, then compare results with Strategy 2 (Trend) or Strategy 3 (Mean Reversion) to see which approach fits the current market conditions.
