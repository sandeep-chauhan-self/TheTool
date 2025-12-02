# Strategy 3: Mean Reversion

## Overview

Strategy 3 is designed for **range-bound/sideways markets**. It heavily weights oscillators (RSI, Stochastic, Bollinger Bands) that identify overbought/oversold conditions, while reducing the influence of trend indicators.

## When to Use

- **Sideways Markets**: When stocks are bouncing between support and resistance
- **Counter-Trend Trading**: Buying dips and selling rallies
- **Stocks with Clear Ranges**: Those respecting support/resistance levels
- **Low ADX Environment**: When ADX < 25 indicates no strong trend

## Indicator Weights

### High Weight (Oscillators)
| Indicator | Weight | Why High? |
|-----------|--------|-----------|
| RSI | 2.5x | Primary overbought/oversold detector |
| Bollinger Bands | 2.5x | Price deviation from mean |
| Stochastic | 2.0x | Momentum exhaustion signals |
| CCI | 1.5x | Cyclical price movements |
| Williams %R | 1.5x | Short-term momentum extremes |

### Low Weight (Trend Indicators)
| Indicator | Weight | Why Low? |
|-----------|--------|----------|
| MACD | 0.5x | Trend signals less relevant in ranges |
| ADX | 0.5x | Actually, low ADX confirms range! |
| EMA | 0.5x | Crossovers whipsaw in ranges |
| PSAR | 0.5x | Flips frequently in ranges |

### Medium Weight
| Indicator | Weight | Why Medium? |
|-----------|--------|-------------|
| ATR | 1.0x | Volatility context |
| OBV | 1.0x | Volume confirmation |
| CMF | 1.0x | Money flow direction |

## Risk Profile

| Setting | Value | Description |
|---------|-------|-------------|
| Stop Loss | 1.5% | Tighter stops (ranges are defined) |
| Target Multiplier | 1.5x | Smaller, more frequent targets |
| Max Position Size | 15% | Smaller positions (counter-trend risk) |

## How It Works

1. **Oscillators dominate** the scoring (RSI, Bollinger, Stochastic)
2. **Trend indicators dampened** to avoid false trend signals
3. **Focus on extremes**: Buy when oversold, sell when overbought
4. **Tighter risk management** due to counter-trend nature

## The Philosophy

In ranging markets, prices oscillate between support (oversold) and resistance (overbought). Trend indicators give whipsaw signals as there's no sustained direction.

Strategy 3 recognizes this by:
- **Trusting oscillators** to identify extremes
- **Buying oversold conditions** (RSI < 30, price at lower Bollinger)
- **Selling overbought conditions** (RSI > 70, price at upper Bollinger)
- **Using tighter stops** since ranges are well-defined

## Best For

✅ Stocks trading in clear channels  
✅ Sideways consolidation patterns  
✅ Range-bound market conditions  
✅ Stocks with strong support/resistance  

## Limitations

❌ Underperforms when trends emerge  
❌ Counter-trend = higher risk per trade  
❌ Can get caught in breakouts  

## Example Use Case

> "HDFC Bank has been trading between ₹1600-1700 for 2 months. I want to buy near support and sell near resistance."

Strategy 3 will:
1. Weight RSI/Bollinger heavily to identify extremes
2. Signal BUY when RSI < 30 and price touches lower Bollinger
3. Signal SELL when RSI > 70 and price touches upper Bollinger
4. Use tighter 1.5% stops (clear support/resistance levels)

## Key Indicators Explained

### RSI (Weight: 2.5x)
- **Oversold (< 30)**: Potential buy signal
- **Overbought (> 70)**: Potential sell signal
- **Best in ranges**: RSI works perfectly when prices oscillate

### Bollinger Bands (Weight: 2.5x)
- **Price at Lower Band**: Oversold, potential bounce
- **Price at Upper Band**: Overbought, potential pullback
- **Price at Middle Band**: Neutral, wait for extremes

### Stochastic (Weight: 2.0x)
- **%K < 20**: Oversold condition
- **%K > 80**: Overbought condition
- **Crossover**: %K crossing %D confirms signal

## Warning: Range Breakouts

The biggest risk with mean reversion is getting caught in a **breakout**. If the stock breaks out of its range with volume:

1. The stop loss should trigger quickly (1.5%)
2. Consider switching to Strategy 2 (Trend Following)
3. Watch for ADX rising above 25 (trend emerging)

## Identifying Good Candidates

Look for stocks with:
- **ADX < 25** (weak trend = ranging)
- **Clear horizontal support/resistance**
- **Multiple touches** of support/resistance levels
- **Bollinger Bands** not expanding dramatically
