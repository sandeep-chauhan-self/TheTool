# Strategy 4: Momentum Breakout

## Overview

Strategy 4 is designed for **breakout trading** with volume confirmation. It heavily weights volume indicators (OBV, CMF) and volatility (ATR) to catch breakouts that have institutional backing.

## When to Use

- **Breakout Trades**: When price breaks key levels with volume
- **Earnings Plays**: Post-earnings momentum moves
- **News-Driven Moves**: Catching institutional buying/selling
- **High Volume Spikes**: Unusual volume indicating big player activity

## Indicator Weights

### Highest Weight (Volume)
| Indicator | Weight | Why Highest? |
|-----------|--------|--------------|
| OBV | 2.5x | Volume accumulation before breakout |
| CMF | 2.5x | Money flow direction (institutional) |

### High Weight (Momentum & Volatility)
| Indicator | Weight | Why High? |
|-----------|--------|-----------|
| RSI | 2.0x | Momentum confirmation |
| ATR | 2.0x | Volatility expansion on breakout |
| Stochastic | 1.5x | Momentum exhaustion |
| CCI | 1.5x | Cyclical momentum |
| Bollinger | 1.5x | Band expansion confirms breakout |

### Medium Weight (Trend)
| Indicator | Weight | Why Medium? |
|-----------|--------|-------------|
| MACD | 1.5x | Trend confirmation |
| ADX | 1.5x | Trend strength |
| EMA | 1.0x | Direction confirmation |
| PSAR | 1.0x | Trend reversal |
| Williams %R | 1.0x | Momentum |

## Risk Profile

| Setting | Value | Description |
|---------|-------|-------------|
| Stop Loss | 3% | Wider stops for volatile breakouts |
| Target Multiplier | 2.5x | Good targets on confirmed moves |
| Max Position Size | 20% | Standard position sizing |

## How It Works

1. **Volume indicators dominate** (OBV, CMF)
2. **ATR high weight** to confirm volatility expansion
3. **Lower ADX threshold (20)** to catch early breakouts
4. **Momentum confirmation** via RSI, Stochastic

## The Philosophy

True breakouts are backed by **volume**. Institutional traders can't hide their activity - large orders create volume spikes and OBV/CMF changes before price moves.

Strategy 4 recognizes this by:
- **Trusting volume indicators** to detect accumulation/distribution
- **Confirming with ATR expansion** (volatility increases on breakouts)
- **Using momentum** for timing
- **Wider stops** to handle breakout volatility

## Best For

✅ Breakout plays from consolidation  
✅ Volume spike trades  
✅ Post-earnings momentum  
✅ Sector rotation leaders  

## Limitations

❌ False breakouts (volume fakeouts)  
❌ Requires good volume data  
❌ Wider stops = larger initial risk  

## Example Use Case

> "TATAMOTORS has been consolidating for 6 weeks. Volume is starting to increase and OBV is rising. I want to catch the breakout."

Strategy 4 will:
1. Weight OBV/CMF heavily to confirm accumulation
2. Look for ATR expansion (volatility increasing)
3. Confirm momentum with RSI
4. Set a wider 3% stop for volatility
5. Target 2.5x risk on confirmed breakout

## Key Indicators Explained

### OBV - On Balance Volume (Weight: 2.5x)
- **Rising OBV + Rising Price**: Confirmed uptrend (accumulation)
- **Rising OBV + Flat Price**: Hidden accumulation (bullish divergence)
- **Falling OBV + Falling Price**: Confirmed downtrend (distribution)
- **Falling OBV + Flat Price**: Hidden distribution (bearish divergence)

### CMF - Chaikin Money Flow (Weight: 2.5x)
- **CMF > 0**: Buying pressure (money flowing in)
- **CMF < 0**: Selling pressure (money flowing out)
- **CMF > 0.25**: Strong buying pressure
- **CMF < -0.25**: Strong selling pressure

### ATR - Average True Range (Weight: 2.0x)
- **ATR expanding**: Volatility increasing (breakout likely)
- **ATR contracting**: Volatility decreasing (consolidation)
- **ATR spike**: Major move in progress

## Volume Breakout Checklist

Before taking a breakout trade, confirm:

1. ✅ **OBV rising** before price breaks out
2. ✅ **CMF positive** (buying pressure)
3. ✅ **ATR expanding** (volatility increasing)
4. ✅ **Volume > 1.5x average** on breakout candle
5. ✅ **Price closes above resistance** (not just wick)

## Avoiding False Breakouts

False breakouts occur when price breaks a level but immediately reverses. To filter these:

1. **Wait for close**: Don't enter on intraday break
2. **Volume confirmation**: Must have above-average volume
3. **OBV confirmation**: Should confirm the direction
4. **Multiple indicators**: RSI, MACD should align

## Risk Management

Breakouts are volatile. Protect yourself:

- **Position size**: Don't exceed 20% of capital
- **Stop loss**: Place below breakout level (wider 3%)
- **Partial profits**: Take 50% at 1:1, let rest run
- **Trailing stop**: Use PSAR or ATR-based trailing stop
