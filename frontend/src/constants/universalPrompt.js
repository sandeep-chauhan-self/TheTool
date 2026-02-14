/**
 * Universal Stock Analysis Prompt Template
 * 
 * Optimized for "Balanced" or "Hold" signals where directional conviction is low.
 * Focuses on determining if a trade should be taken despite weak technicals, 
 * or if it should be skipped/aborted.
 */

export const UNIVERSAL_PROMPT_TEMPLATE = `
# Comprehensive Trade Validation: {stockName} ({ticker})

## 🎯 TECHNICAL SIGNAL OVERVIEW

**Stock:** {stockName} ({ticker})
**Sector:** [AUTO-DETECT SECTOR]
**Market Cap:** [AUTO-DETECT] Cr

---

### Technical Analysis Summary

**Signal:** {verdict}
**Conviction Score:** {score} / 1.000 🔴 **CRITICALLY WEAK**
- Score Range: -1.0 (Strong Sell) → 0.0 (Neutral) → +1.0 (Strong Buy)
- Current: **Nearly Neutral** (within ±0.05 of zero)
- Interpretation: **NO CLEAR DIRECTIONAL BIAS**

**Price Levels:**
- Entry Price: ₹{entry}
- Stop Loss: ₹{stopLoss}
- Target: ₹{target}
- Risk-Reward: [CALCULATE]

**Strategy:** {strategyName} (Balanced Analysis)
- 12 equally-weighted indicators
- 4 Trend: MACD, ADX, EMA Crossover, Parabolic SAR
- 4 Momentum: RSI, Stochastic, CCI, Williams %R
- 2 Volatility: Bollinger Bands, ATR
- 2 Volume: OBV, CMF
- Timeframe: Daily/Weekly

---

## ⚠️ CRITICAL CONTEXT: WEAK SIGNAL ALERT

**This is NOT a typical trade signal. Here's why:**
\`\`\`
Conviction Score: {score}
├─ Interpretation: Market is indecisive
├─ Technical indicators are conflicting
├─ Roughly 50% bullish / 50% bearish signals
└─ High probability of whipsaw or sideways movement

Default Recommendation: WAIT for clearer setup
\`\`\`

**Your Analysis Objective:**
Since technical analysis provides NO clear direction, your fundamental/qualitative analysis must be DECISIVE. You need to determine if there are compelling non-technical reasons to:
1. **Override HOLD** → Upgrade to BUY (if strong fundamentals/catalysts)
2. **Override HOLD** → Downgrade to SELL (if red flags/deterioration)
3. **Confirm HOLD** → Wait for better technical setup

---

## 📋 PRE-ANALYSIS DATA CHECKLIST

Before starting analysis, verify data accessibility:

**Required Data Sources:**
- [ ] Current stock price (within 24 hours)
- [ ] Company financial statements (latest 2 quarters minimum)
- [ ] Recent news (past 7-14 days)
- [ ] Shareholding patterns (latest available quarter)
- [ ] Sector performance data
- [ ] NSE/BSE announcements

**Data Quality Baseline:**
\`\`\`
If ≥80% data available → Proceed with HIGH confidence ceiling
If 60-79% data available → Proceed with MEDIUM confidence ceiling  
If <60% data available → FLAG as insufficient and explain gaps
\`\`\`

**Specific Considerations:**
- Small-cap stock: Data may be limited vs large-caps
- Sector specific risks (Regulatory, Export, etc.)
- Promoter pledge data critical

---

## SECTION 1: LIQUIDITY & EXECUTION FEASIBILITY

### Priority: CRITICAL ⚠️

**Why This Matters:**
Small-cap stocks often have liquidity issues. A technically neutral signal becomes HIGHLY risky if you can't exit cleanly.

### Search Strategy:
Query 1: "{stockName} NSE volume average"
Query 2: "{stockName} average daily volume"
Query 3: "{stockName} bid ask spread"
Query 4: "{stockName} circuit breaker hits"

### Analysis Tasks:

1. **Volume Analysis:**
   - Average daily traded value (20-day): ₹[VALUE]
   - Average daily traded volume: [SHARES]
   - Volume trend: [Increasing/Stable/Decreasing]

2. **Liquidity Metrics:**
   - Market cap: [AUTO-DETECT]
   - Free float: [AUTO-DETECT]
   - Delivery percentage (avg): [X]%
   - Typical bid-ask spread: [X]%

3. **Risk Indicators:**
   - Circuit hits (last 30 days): [COUNT]
   - Upper circuit / Lower circuit hits
   - Price manipulation concerns: [YES/NO]

### Liquidity Decision Matrix:
\`\`\`
IF Avg Daily Value <₹25 Lakhs:
   → 🔴 SKIP - Too illiquid for safe trading
   → Stop analysis here

IF Avg Daily Value ₹25L-₹50L:
   → ⚠️ HIGH RISK - Only micro positions (<1% portfolio)
   → Proceed with extreme caution

IF Avg Daily Value >₹50L:
   → ✅ ACCEPTABLE - Standard position sizing possible
   → Proceed with analysis
\`\`\`

**Liquidity Verdict:** [EXECUTE / CAUTION / SKIP]

---

## SECTION 2: NEWS, SENTIMENT & CATALYST ANALYSIS

### Search Strategy:
Query 1: "{stockName} news last 14 days"
Query 2: "{stockName} earnings results latest"
Query 3: "{stockName} corporate announcements"
Query 4: "{stockName} management changes dividend"

### Analysis Framework:

#### 1. Recent News Scan (Last 14 Days):
- **Corporate Announcements:** Earnings, dividends, management changes.
- **Business Developments:** Product launches, new clients.
- **Regulatory & Legal:** CDSCO, FDA, compliance issues.

#### 2. Sentiment Analysis:
- Analyst Coverage: Reports, targets.
- Retail Sentiment: Trends, forums.

#### 3. Upcoming Events (Next 30 Days):
- Earnings date, Board meetings, AGM.

#### 4. Red Flags vs Green Flags:
- 🔴 Auditor resignation, pledge increase, penalties.
- 🟢 Export wins, capacity expansion, promoter buying.

### Sentiment Verdict:
- **Score:** [Rating]
- **Support for HOLD?** [✅ YES / ⚠️ MIXED / ❌ NO]
- **Recommendation Override:** [If sentiment strongly contradicts, suggest BUY/SELL]

---

## SECTION 3: FUNDAMENTAL HEALTH CHECK

### Search Strategy:
Query 1: "{stockName} balance sheet profit loss"
Query 2: "{stockName} valuation ratio vs sector"
Query 3: "{stockName} debt equity ratio"
Query 4: "{stockName} revenue profit growth"

### Analysis Framework:

#### 1. Valuation Metrics:
- P/E, P/B, EV/EBITDA vs Sector.
- Status: [Undervalued/Fair/Overvalued].

#### 2. Financial Stability:
- Debt/Equity (<1?), Current Ratio (>1.5?), Interest Coverage (>3?).

#### 3. Growth Trajectory (Last 3 Years):
- Revenue & Profit CAGR vs Sector.
- Margin Trend: [Expanding/Stable/Contracting].

#### 4. Earnings Quality:
- OCF vs Net Profit (>1?).
- Receivables/Inventory Days trend.

#### 5. Peer Comparison:
- Rank {stockName} vs competitors on key metrics.

### Fundamental Verdict:
**Overall Rating:** [🟢 Strong / 🟡 Moderate / 🔴 Weak]
**Fair Value Estimate:** ₹[Value]
**Support for Trade?** [✅ YES / ⚠️ CONDITIONAL / ❌ NO]

---

## SECTION 4: SECTOR & MARKET CONTEXT

### Search Strategy:
Query 1: "Nifty Healthcare index trend"
Query 2: "FII DII flows current month"
Query 3: "Macro economic factors India 2025"

### Analysis Framework:
1. **Sector Deep Dive:** Performance vs Nifty, Outperformance/Underperformance.
2. **Broader Market:** Nifty Trend, Breadth, VIX.
3. **FII/DII Flows:** Net buying/selling in market and sector.
4. **Macro:** Interest rates, Currency, Commodity prices.

### Market Context Verdict:
**Overall Rating:** [🟢 Favorable / 🟡 Neutral / 🔴 Unfavorable]
**Timing Assessment:** [Good/Mixed/Poor Time to Trade]

---

## SECTION 5: INSTITUTIONAL & SMART MONEY ANALYSIS

### Search Strategy:
Query 1: "{stockName} shareholding pattern"
Query 2: "{stockName} bulk deals"
Query 3: "{stockName} insider trading"

### Analysis Framework:
1. **Promoter Activity:** Holding change, Pledge change.
2. **Institutional Holdings:** FII/DII/MF trends.
3. **Bulk Deals:** Buying or Selling pressure?
4. **Insider Transactions:** Director buying/selling.

### Smart Money Verdict:
**Status:** [Accumulation / Distribution / Neutral]
**Does This Support HOLD?** [✅ YES / ⚠️ MIXED / ❌ NO]

---

## SECTION 6: RISK ANALYSIS & FINAL VERDICT

### Comprehensive Risk Assessment:
- **Technical Risks:** Low conviction, whipsaw risk.
- **Liquidity Risks:** Execution, slippage.
- **Fundamental Risks:** Debt, growth, quality.
- **Market/Sector Risks:** Trend, flows.
- **Event Risks:** Earnings, news.

### Scenario Analysis:
- **Base Case (50%):** Sideways movement.
- **Bull Case (25%):** Positive surprise → Target hit.
- **Bear Case (25%):** Negative news → Stop hit.

---

## 🎯 FINAL CONSOLIDATED VERDICT

### Multi-Factor Scorecard:
| Dimension | Score/100 | Weight | Weighted |
|-----------|-----------|--------|----------|
| Technical Strength | [XX] | 25% | [X.XX] |
| Liquidity | [XX] | 15% | [X.XX] |
| News & Sentiment | [XX] | 10% | [X.XX] |
| Fundamentals | [XX] | 25% | [X.XX] |
| Market/Sector | [XX] | 10% | [X.XX] |
| Smart Money | [XX] | 10% | [X.XX] |
| Risk-Reward | [XX] | 5% | [X.XX] |
| **TOTAL** | | **100%** | **[XX.XX]** |

### Decision Matrix Application:
- **75-100:** ✅ **STRONG BUY** (Override HOLD).
- **60-74:** ✅ **BUY** (Override HOLD).
- **50-59:** ⚠️ **CONDITIONAL** (Reduce Size).
- **40-49:** ⚠️ **HOLD/WAIT** (Confirm HOLD).
- **<40:** ❌ **SKIP/SELL** (Downgrade).

### FINAL RECOMMENDATION:
\`\`\`
┌────────────────────────────────────────────────────────────┐
│                                                             │
│  VERDICT: [✅ EXECUTE / ⚠️ EXECUTE WITH CAUTION / ❌ SKIP]  │
│                                                             │
│  Confidence Level: [🟢 HIGH / 🟡 MEDIUM / 🔴 LOW]           │
│                                                             │
└────────────────────────────────────────────────────────────┘
\`\`\`

**Action Plan:**
- **Entry:** ₹{entry}.
- **Stop Loss:** ₹{stopLoss} (Strict).
- **Target:** ₹{target}.
- **Position Size:** [Adjusted based on score].
- **Monitoring:** [Daily checks required].

**Executive Summary:**
[Clear, actionable summary synthesizing all factors.]
`;
