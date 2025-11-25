# Comprehensive Trading System Plan

## Objective: Achieve 4% Return within 7 Days

---

## 1. SYSTEM OVERVIEW

### Goal

- **Target Return**: 4+% within 7 days per trade
- **Example**: Buy at ₹100 → Sell at ₹104+, minimum 4% return
- **Input**: Single stock symbol (e.g., "TCS.NS", "INFY.NS")
- **Output**: Trading signal with entry price, stop loss, target (104+% of entry)

---

## 2. INPUT STAGE

### Input Format

```
Symbol: "TCS.NS" or "INFY.NS"
Current Price: Fetched automatically from Yahoo Finance
Time Frame: 7 days (short-term trading)
```

### Processing the Input

1. **Accept symbol** from user {will be shared over payload by frontend}
2. **Fetch current price** from Yahoo Finance
3. **Scale analysis to stock price**:
   - Logic: Percentage-based, not fixed rupee amounts
   - 4+% change in amount

---

## 3. DATA FETCHING STAGE

### Source: Yahoo Finance

#### 3.1 What Data to Fetch?

```
OHLCV Data (Open, High, Low, Close, Volume):
- Essential for technical indicators
- Price action patterns
- Volatility calculation
- Volume analysis

Additional Data:
- Historical price data
- Trading volume
- Dividend information (for adjustments)
```

#### 3.2 How Much Data to Fetch?

```
Short-term (7-day focus):
- Minimum: 100 days of historical data (for indicator baseline)
- Optimal: 250 days (1 year of trading days)
- Reason: Indicators need sufficient history for accuracy

Data structure:
- Daily candles (1D timeframe)
- May also fetch hourly (1H) for intraday confirmation
```

#### 3.3 Data Format & Storage

```
Format from Yahoo Finance:
- JSON/CSV with: Date, Open, High, Low, Close, Volume, Adjusted Close

Storage Strategy:
┌─────────────────────────────────────┐
│  Fetch from Yahoo Finance           │
│  (Real-time + Historical)           │
└─────────────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│  (Already implemented)              │
│  Tables:                            │
│  - price_history (OHLCV)           │
│  - technical_indicators            │
│  - trading_signals                 │
│  - backtest_results                │
└─────────────────────┬───────────────┘
                      │
                      ▼
┌─────────────────────────────────────┐
│  Cache (Redis)                      │
│  - Current price                    │
│  - Recent indicators (5-10 min)    │
│  - Signal cache                     │
└─────────────────────────────────────┘
```

#### 3.4 How to Fetch Data?

```python
# Fetch Strategy
1. Real-time current price: Every 1-5 minutes
2. Historical data: 
   - Fetch once at startup
   - Update daily with new candle
   - Cache in PostgreSQL for reference

3. Fetch Frequency:
   - Market hours: Every 5 minutes
   - Off-market: Once daily at close
   
4. Data validation:
   - Check for gaps/missing data
   - Handle corporate actions (splits, dividends)
   - Verify data quality
```

---

## 4. DATA PROCESSING STAGE

### 4.1 Technical Indicator Calculation

```
For 4+% Target in 7 Days, Use:

SHORT-TERM INDICATORS (Momentum-focused):
1. RSI (14-period): Overbought/oversold levels
   - Buy signal: RSI > 50 with uptrend
   - Sell signal: RSI < 50 with downtrend

2. MACD (Fast-12, Slow-26, Signal-9): Trend + Momentum
   - Buy: MACD > Signal line + positive histogram
   - Sell: MACD < Signal line + negative histogram

3. Bollinger Bands (20-period): Volatility + Support/Resistance
   - Buy near lower band with RSI confirmation
   - Sell near upper band

4. ADX (14-period): Trend Strength
   - Only trade if ADX > 25 (strong trend)
   - Avoid ranging markets

5. ATR (14-period): Volatility measurement
   - Calculate stop loss: Entry - (2 × ATR)
   - Calculate target: Entry + (ATR × 3) for 4% goal

6. Volume Profile: Confirmation
   - Buy only on volume increase
   - Sell on volume confirmation

7. EMA Crossover (7, 21, 50):
   - 7 EMA > 21 EMA > 50 EMA = Uptrend
   - Buy when price > 7 EMA + 21 EMA crossover

8. Stochastic Oscillator: Quick momentum
   - %K > %D = Bullish
   - K > 50 with D crossover = Entry
```

### 4.2 Processing Logic Flow

```
┌──────────────────────────────────────────┐
│ 1. FETCH & VALIDATE DATA                 │
│    - Get 250 days OHLCV from Yahoo        │
│    - Check data integrity                │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 2. CALCULATE INDICATORS                  │
│    - RSI, MACD, Bollinger, ADX, ATR     │
│    - EMA crossover, Stochastic           │
│    - Volume analysis                     │
│    - Store in PostgreSQL                 │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 3. PRICE-BASED SCALING                   │
│    - High price (₹27,000):               │
│      * Target: 27,000 × 1.04 = 28,080   │
│      * Stop Loss: 27,000 × 0.97 = 26,190│
│      * Risk/Reward: 1:2 ratio            │
│    - Low price (₹109):                   │
│      * Target: 109 × 1.04 = 113.36      │
│      * Stop Loss: 109 × 0.97 = 105.73   │
│      * Percentage-based logic applies    │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 4. SIGNAL GENERATION                     │
│    - Aggregate indicator signals         │
│    - Voting mechanism (6/8 positive)     │
│    - Calculate confidence score          │
│    - Generate trade recommendation       │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│ 5. RISK MANAGEMENT                       │
│    - Apply position sizing               │
│    - Calculate risk per trade            │
│    - Apply stop loss (2×ATR or 3%)      │
│    - Calculate target (4% or 3×ATR)     │
└──────────────────────────────────────────┘
```

---

## 5. DATA AGGREGATION STAGE

### 5.1 Where to Aggregate?

```
PostgreSQL Database (Already Implemented)

Tables Structure:
┌────────────────────────────────────────┐
│ price_history                          │
├────────────────────────────────────────┤
│ - symbol (TCS.NS)                      │
│ - date                                 │
│ - open, high, low, close, volume       │
│ - adjusted_close                       │
│ - created_at, updated_at               │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ technical_indicators                   │
├────────────────────────────────────────┤
│ - symbol                               │
│ - date                                 │
│ - rsi, macd, bb_upper, bb_lower       │
│ - adx, atr, ema_7, ema_21, ema_50     │
│ - stochastic_k, stochastic_d          │
│ - volume_sma                           │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ trading_signals                        │
├────────────────────────────────────────┤
│ - symbol                               │
│ - date (today's date)                  │
│ - signal (BUY/SELL/HOLD)              │
│ - confidence (0-100%)                  │
│ - entry_price                          │
│ - stop_loss                            │
│ - target_price (104% of entry)        │
│ - raw_data (all indicator values)     │
│ - analysis_version                     │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ backtest_results (Historical Validation)│
├────────────────────────────────────────┤
│ - strategy_name                        │
│ - symbol                               │
│ - start_date, end_date                 │
│ - total_trades                         │
│ - winning_trades                       │
│ - average_return (target: 4%/7days)   │
│ - max_drawdown                         │
│ - sharpe_ratio                         │
└────────────────────────────────────────┘
```

### 5.2 Data Import Process

```
1. Fetch data from Yahoo Finance (Real-time + Historical)
2. Store in PostgreSQL:
   - price_history (updates daily)
   - technical_indicators (recalculated daily)
3. Use PostgreSQL as source of truth
4. Cache recent data in Redis for performance
5. Generate signals from aggregated data
```

---

## 6. HISTORICAL DATA & WARMING UP (30-Day Strategy)

### 6.1 Problem: "Takes 10-30 Days to Work Properly"

**Why?** Technical indicators need historical data to be accurate:

- Moving averages need 50-200 candles
- ADX needs 14+ candles minimum
- Bollinger Bands need 20+ candles
- Stochastic needs 14 candles

### 6.2 Solution: Data Warmup Period

```
WARMUP PHASE (Days 1-30):
┌─────────────────────────────────────────┐
│ Day 1-5: Collect baseline data          │
│ - Fetch 250 days of historical data    │
│ - Calculate all indicators              │
│ - Generate signals (confidence: LOW)    │
│ - Action: TEST SIGNALS (paper trading) │
│                                         │
│ Day 6-15: Validation phase              │
│ - Track signal accuracy                 │
│ - Validate indicator calculations       │
│ - Refine parameters                     │
│ - Action: SMALL TRADES (25% position)   │
│                                         │
│ Day 16-30: Optimization phase           │
│ - Backtest on 1-year historical data   │
│ - Calculate expected win rate           │
│ - Calculate risk/reward ratios          │
│ - Refine stop loss and targets          │
│ - Action: NORMAL TRADES (50% position)  │
│                                         │
│ Day 31+: Live trading                   │
│ - Use full position size                │
│ - Continue monitoring accuracy          │
│ - Adapt to market conditions            │
└─────────────────────────────────────────┘

STORAGE OF WARMUP DATA:
- Store ALL 30 days of processed data in PostgreSQL
- Keep backtest results for reference
- Track performance metrics daily
- Calculate rolling accuracy statistics
```

### 6.3 Continuous Learning

```
Database stores:
- All historical signals (with results)
- Win rate per stock
- Average return per setup
- Best time of day to trade
- Seasonal patterns
- Market condition analysis

This allows system to:
1. Learn from past 30 days
2. Adapt parameters automatically
3. Improve signal quality over time
4. Identify best trading patterns
```

---

## 7. OUTPUT STAGE

### 7.1 What Output Will User Get?

```
FOR EACH STOCK ANALYSIS:

┌────────────────────────────────────────┐
│ TRADING RECOMMENDATION                 │
├────────────────────────────────────────┤
│ Signal: BUY / SELL / HOLD               │
│ Confidence: 85% (based on 6/8 votes)   │
│                                         │
│ Entry Price: ₹27,000                   │
│ Target Price: ₹28,080 (4% profit)     │
│ Stop Loss: ₹26,190 (3% loss)           │
│ Risk/Reward Ratio: 1:2.7                │
│ Holding Period: 7 days                  │
│                                         │
│ TECHNICAL ANALYSIS DETAILS:             │
│ - RSI: 65 (Bullish - above 50)         │
│ - MACD: Bullish crossover ✓            │
│ - Bollinger: Price above middle band ✓ │
│ - ADX: 32 (Strong trend) ✓             │
│ - EMA: 7>21>50 (Uptrend) ✓             │
│ - Volume: Above average ✓              │
│ - Stochastic: 72 (Bullish) ✓           │
│                                         │
│ MARKET CONTEXT:                         │
│ - Trend: Up                             │
│ - Volatility (ATR): ₹420               │
│ - Support: ₹26,500                      │
│ - Resistance: ₹28,200                   │
│                                         │
│ BACKTEST DATA:                          │
│ - Strategy Win Rate: 72% (last 30 days)│
│ - Average Return: 4.2%                  │
│ - Avg Win: 4.8% | Avg Loss: -2.1%     │
│ - Similar setups past 30 days: 8/12 won│
└────────────────────────────────────────┘

UI DISPLAYS:
1. Dashboard: Overview of all signals
2. Stock Details: Deep technical analysis
3. Trade Journal: Historical performance
4. Portfolio: Position tracking
5. Analytics: Win rate, ROI, Sharpe ratio
```

---

## 8. COMPLETE DATA FLOW DIAGRAM

```
┌──────────────────────────────────────────────────────────────┐
│                         USER INPUT                           │
│                    Symbol: "TCS.NS"                          │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│              YAHOO FINANCE DATA FETCHER                       │
│  • Fetch 250 days OHLCV data                                 │
│  • Fetch current price                                       │
│  • Fetch volume data                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│               PostgreSQL Database                            │
│  ┌─ price_history table (store raw OHLCV)                   │
│  └─ Updated/validated                                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│          TECHNICAL INDICATOR ENGINE                          │
│  • RSI Calculator                                            │
│  • MACD Calculator                                           │
│  • Bollinger Bands                                           │
│  • ADX Trend Strength                                        │
│  • ATR Volatility                                            │
│  • EMA Crossover                                             │
│  • Stochastic Oscillator                                     │
│  • Volume Analysis                                           │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│               PostgreSQL Database                            │
│  ┌─ technical_indicators table (store all calculated values) │
│  └─ Indexed for fast retrieval                               │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│          PRICE-BASED SCALING MODULE                          │
│  • Calculate 4% target based on current price                │
│  • Calculate 3% stop loss based on current price             │
│  • Adjust for low/high price stocks                          │
│  • Calculate position size                                   │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│          SIGNAL AGGREGATION ENGINE                           │
│  • Vote from each indicator (8 indicators)                   │
│  • Weighted voting system                                    │
│  • Confidence calculation (need 6/8 positive)                │
│  • Generate BUY/SELL/HOLD signals                            │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│               PostgreSQL Database                            │
│  ┌─ trading_signals table (store final signal)               │
│  ├─ Includes: Entry, Target, StopLoss, Confidence           │
│  └─ Includes: All raw indicator data                         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│            RISK MANAGEMENT MODULE                            │
│  • Validate risk/reward ratio > 1:2                          │
│  • Check portfolio heat (total risk)                         │
│  • Apply position sizing rules                               │
│  • Final approval/rejection                                  │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│             BACKTEST VALIDATION                              │
│  • Validate signal against 30-day history                    │
│  • Calculate expected win rate                               │
│  • Calculate expected return                                 │
│  • Store backtest results in PostgreSQL                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────────────┐
│                  API RESPONSE / UI                           │
│  • Signal recommendation                                     │
│  • Entry/Target/StopLoss prices                              │
│  • Confidence level                                          │
│  • Indicator breakdown                                       │
│  • Historical performance stats                              │
│  • Risk metrics                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. IMPLEMENTATION TIMELINE

### Phase 1: Foundation (Weeks 1-2)

- ✅ Data fetching from Yahoo Finance
- ✅ PostgreSQL schema setup
- ✅ Basic indicator calculations
- ✅ Store data in database

### Phase 2: Signal Generation (Weeks 3-4)

- ✅ All 8 indicator implementations
- ✅ Voting mechanism
- ✅ Signal generation logic
- ✅ Price-based scaling

### Phase 3: Backtesting (Weeks 5-6)

- ✅ Historical data analysis
- ✅ Performance metrics calculation
- ✅ Parameter optimization
- ✅ Win rate calculation

### Phase 4: Risk Management (Weeks 7-8)

- ✅ Position sizing
- ✅ Stop loss calculation
- ✅ Risk/reward validation
- ✅ Portfolio heat monitoring

### Phase 5: Frontend & Monitoring (Weeks 9-10)

- ✅ Dashboard UI
- ✅ Trade journal
- ✅ Real-time alerts
- ✅ Performance tracking

### Phase 6: Live Trading Readiness (Week 11+)

- ✅ 30-day paper trading
- ✅ System optimization
- ✅ Live deployment
- ✅ Continuous monitoring

---

## 10. KEY SUCCESS METRICS

```
TARGET: 4% Return in 7 Days

TRACKING METRICS:
1. Win Rate: Target 70%+ (should win 7/10 trades)
2. Average Win: 4-5% per trade
3. Average Loss: -2% to -3% per trade
4. Profit Factor: (Win % × Avg Win) / (Loss % × Avg Loss) > 2
5. Sharpe Ratio: > 1.5
6. Maximum Drawdown: < 15%
7. Recovery Factor: Total Profit / Max Drawdown > 3
8. Accuracy per symbol: Track which stocks work best
9. Best time to trade: Identify optimal entry hours
10. Market conditions: Track performance in bullish/bearish/ranging

MONTHLY REVIEW:
- Win rate trending up/down?
- Which indicators performing best?
- Which stocks most profitable?
- What market conditions work best?
- Adapt parameters based on performance
```

---

## 11. 30-DAY HISTORICAL DATA STRATEGY

```
COLDSTART PROBLEM:
- New stock: Need 30 days to warm up
- Solution: Run on historical data first

EXECUTION:
┌─────────────────────────────────────────────────────────┐
│ Day 1-5: Backtest on 1 year historical data             │
│ - Calculate historical win rate                         │
│ - Validate indicator calculations                       │
│ - Optimize parameters                                   │
│ Result: Expected performance baseline                   │
│                                                         │
│ Day 6-15: Paper trading (watch-only)                    │
│ - Apply live signals to historical data                 │
│ - Track accuracy                                        │
│ - Compare vs backtest                                   │
│ Result: Real-time validation                            │
│                                                         │
│ Day 16-30: Small position trading (1-5% of capital)    │
│ - Take real small trades                                │
│ - Monitor entry/exit                                    │
│ - Track P&L                                             │
│ Result: Live calibration                                │
│                                                         │
│ Day 31+: Full position trading                          │
│ - Normal trade sizing                                   │
│ - Continue optimization                                 │
│ Result: Revenue generation                              │
└─────────────────────────────────────────────────────────┘

STORAGE:
- All 30 days of data in PostgreSQL
- backtest_results table: Store historical analysis
- trading_signals table: Store each day's signals
- Performance metrics: Calculate rolling averages
- Continuous learning: Adapt based on 30-day performance
```

---

## 12. DATA FLOW SUMMARY: INPUT TO OUTPUT

```
INPUT: "TCS.NS"
  │
  ├─→ Yahoo Finance: Fetch 250 days OHLCV + current price
  │
  ├─→ PostgreSQL: Store price_history
  │
  ├─→ Calculate Indicators:
  │   - RSI, MACD, Bollinger, ADX, ATR, EMA, Stochastic, Volume
  │
  ├─→ PostgreSQL: Store technical_indicators
  │
  ├─→ Price Scaling:
  │   - Current: ₹27,000
  │   - Target: ₹28,080 (27,000 × 1.04)
  │   - Stop: ₹26,190 (27,000 × 0.97)
  │
  ├─→ Signal Aggregation:
  │   - Vote from 8 indicators
  │   - Calculate confidence
  │   - Generate BUY/SELL/HOLD
  │
  ├─→ PostgreSQL: Store trading_signals
  │
  ├─→ Backtesting: Validate against 30-day history
  │   - Win rate: 72%
  │   - Similar setups: 8 wins, 2 losses
  │
  ├─→ PostgreSQL: Store backtest_results
  │
  └─→ OUTPUT to User:
      ✓ BUY signal with 85% confidence
      ✓ Entry: ₹27,000
      ✓ Target: ₹28,080 (4% profit target)
      ✓ Stop Loss: ₹26,190 (3% risk)
      ✓ Hold for 7 days
      ✓ Expected win rate: 72%
      ✓ Risk/Reward: 1:2.7
```

---

## 13. TECHNICAL REQUIREMENTS CHECKLIST

```
✓ Yahoo Finance API Integration
✓ PostgreSQL Database with proper schema
✓ Redis Cache for performance
✓ 8 Technical Indicators Engine
✓ Signal Voting Mechanism
✓ Price-scaled position sizing
✓ 30-day historical data storage
✓ Backtesting engine
✓ Performance metrics calculation
✓ Risk management module
✓ REST API endpoints
✓ Frontend dashboard
✓ Real-time alerts
✓ Trade journal tracking
✓ Performance analytics
```

---

## 14. CRITICAL SUCCESS FACTORS

```
1. DATA QUALITY
   - Ensure Yahoo Finance data accuracy
   - Validate OHLCV data integrity
   - Handle corporate actions (splits, dividends)

2. INDICATOR ACCURACY
   - Test each indicator calculation
   - Backtest against known patterns
   - Validate against TradingView/MT5

3. SIGNAL CONFIDENCE
   - Require 6/8 indicators agreement
   - Adjust weights if needed
   - Don't trade weak signals

4. RISK MANAGEMENT
   - Strict stop loss adherence
   - Position sizing discipline
   - Portfolio heat monitoring

5. CONTINUOUS IMPROVEMENT
   - Track every trade
   - Analyze winning patterns
   - Optimize parameters monthly
   - Adapt to market changes

6. 30-DAY WARMUP
   - Don't skip this phase
   - Validate before live trading
   - Learn from historical data
   - Build confidence in system
```

---

## 15. EXECUTION ROADMAP

```
WEEK 1-2: Setup & Data
├─ Implement Yahoo Finance fetcher
├─ Design PostgreSQL schema
├─ Load 250 days historical data
└─ Test data pipeline

WEEK 3-4: Indicators
├─ Implement 8 technical indicators
├─ Calculate on historical data
├─ Store in PostgreSQL
└─ Validate calculations

WEEK 5-6: Signals
├─ Build voting mechanism
├─ Implement signal generation
├─ Price-based scaling
└─ Generate historical signals

WEEK 7-8: Backtesting
├─ Analyze 30-day history
├─ Calculate win rates
├─ Optimize parameters
└─ Build backtest results table

WEEK 9-10: Frontend
├─ Build dashboard
├─ Display signals
├─ Show trade metrics
└─ Implement trade journal

WEEK 11: Testing & Optimization
├─ Paper trading validation
├─ Performance monitoring
├─ Parameter tuning
└─ 30-day warmup period

WEEK 12+: Live Trading
├─ Real trade execution
├─ Continuous monitoring
├─ Performance tracking
└─ System optimization
```

---

This comprehensive plan covers:
✅ Input processing (symbol → price scaling)
✅ Data fetching (Yahoo Finance what/how/how much)
✅ Data storage (PostgreSQL for persistence)
✅ Data processing (8 indicators calculation)
✅ Data aggregation (voting mechanism)
✅ Signal generation (BUY/SELL/HOLD)
✅ 30-day historical warmup strategy
✅ Output format (trading recommendation with all details)
✅ Risk management (stop loss, target, position sizing)
✅ Performance metrics (win rate, ROI, Sharpe ratio)

**The system is designed to achieve 4+% return within 7 days through disciplined technical analysis, backtesting, and continuous optimization.**
