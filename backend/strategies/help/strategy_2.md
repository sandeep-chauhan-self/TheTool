# Strategy 2: Trend Following

## Overview

Strategy 2 is designed for **trending markets**. It heavily weights trend-identifying indicators (MACD, ADX, EMA, PSAR) while reducing the influence of oscillators that tend to give premature reversal signals during strong trends.

## When to Use

- **Trending Markets**: When stocks are making sustained directional moves
- **Breakout Trading**: After price breaks key support/resistance levels
- **Swing Trading**: Holding positions for days to weeks in trend direction
- **Momentum Plays**: Stocks with strong institutional buying/selling

## Indicator Weights

### High Weight (Trend Focused)
| Indicator | Weight | Why High? |
|-----------|--------|-----------|
| MACD | 2.5x | Best for identifying trend momentum |
| ADX | 2.5x | Confirms trend strength (ADX > 25 = strong trend) |
| EMA Crossover | 2.0x | Classic trend confirmation signal |
| Parabolic SAR | 1.5x | Identifies trend reversals |

### Low Weight (Reduced Influence)
| Indicator | Weight | Why Low? |
|-----------|--------|----------|
| RSI | 0.5x | Stays overbought/oversold in trends |
| Stochastic | 0.5x | Gives false reversal signals in trends |
| CCI | 0.5x | Oscillator, less useful in trends |
| Williams %R | 0.5x | Oscillator, less useful in trends |
| Bollinger Bands | 0.5x | Price rides bands in trends |

### Medium Weight
| Indicator | Weight | Why Medium? |
|-----------|--------|-------------|
| ATR | 1.0x | Useful for stop placement |
| OBV | 1.0x | Volume confirms trend |
| CMF | 1.0x | Money flow confirms trend |

## Risk Profile

| Setting | Value | Description |
|---------|-------|-------------|
| Stop Loss | 2.5% | Wider stops to avoid whipsaws |
| Target Multiplier | 3x | Let winners run (1:3 risk-reward) |
| Max Position Size | 25% | Larger positions in confirmed trends |

## How It Works

1. **Trend indicators dominate** the scoring (MACD, ADX, EMA, PSAR)
2. **Oscillators are dampened** to prevent false reversal signals
3. **ADX threshold raised to 25** to confirm strong trends
4. **Faster EMA settings** (9/21) for quicker trend detection

## The Philosophy

In trending markets, oscillators like RSI often stay "overbought" or "oversold" for extended periods. A stock can have RSI > 70 for weeks during a strong uptrend. 

Strategy 2 recognizes this by:
- **Trusting trend indicators** to tell you the direction
- **Ignoring oscillator warnings** that would exit too early
- **Using wider stops** to stay in the trend longer

## Best For

✅ Stocks making new 52-week highs/lows  
✅ Breakout plays with volume confirmation  
✅ Sector rotation (riding leading sectors)  
✅ Momentum stocks with institutional buying  

## Limitations

❌ Underperforms in choppy/sideways markets  
❌ Late entry signals (trends already started)  
❌ Can suffer during trend reversals  

## Example Use Case

> "RELIANCE has broken out of a 3-month consolidation with strong volume. I want to ride this trend and let my winners run."

Strategy 2 will:
1. Weight MACD/ADX heavily to confirm the uptrend
2. Ignore RSI overbought warnings
3. Set a wider 2.5% stop loss
4. Target 3x the risk (let profits run)

## Key Indicators Explained

### MACD (Weight: 2.5x)
- **Bullish**: MACD line > Signal line (histogram positive)
- **Bearish**: MACD line < Signal line (histogram negative)
- **Strength**: Larger histogram = stronger trend

### ADX (Weight: 2.5x)
- **ADX > 25**: Strong trend (triggers higher confidence)
- **ADX > 40**: Very strong trend
- **DI+ > DI-**: Bullish trend
- **DI- > DI+**: Bearish trend

### EMA Crossover (Weight: 2.0x)
- **Golden Cross**: Short EMA (9) crosses above Long EMA (21) = Bullish
- **Death Cross**: Short EMA (9) crosses below Long EMA (21) = Bearish
