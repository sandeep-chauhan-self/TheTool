/**
 * Optimized Trend Following SELL Analysis Prompt
 * 
 * Specialized deep-dive framework for validating SELL signals in Trend Following strategy.
 * Focuses on catalyst verification, liquidity risks for shorting, and smart money exit.
 */

export const TREND_SELL_PROMPT_TEMPLATE = `
# Trend-Following Trade Validation: {stockName} ({ticker})
## SELL SIGNAL - Downtrend Confirmation Required

---

## 🎯 TECHNICAL SIGNAL OVERVIEW

**Stock:** {stockName} ({ticker})
**Sector:** [AUTO-DETECT SECTOR]
**Market Cap:** [AUTO-DETECT] Cr

---

### Technical Analysis Summary

**Signal:** SELL 🔴
**Conviction Score:** {score} / 1.000 🟡 **MODERATE BEARISH**
- Score Range: -1.0 (Strong Sell) ← **{score}** → 0.0 (Neutral) → +1.0 (Strong Buy)
- Interpretation: **MODERATE DOWNTREND DETECTED**
- Strength: Mid-range bearish conviction (not weak, not extreme)

**Trade Setup:**
- Entry Price: ₹{entry} (Current market price)
- Stop Loss: ₹{stopLoss} (+2.5% wider stops for trend trades)
- Target: ₹{target} (-7.5% downside potential)
- Risk: [CALCULATE] per share (2.5%)
- Reward: [CALCULATE] per share (7.5%)
- **Risk-Reward Ratio: 1:3.0** ⭐ (Excellent for trend trades)

**Strategy:** Trend Following
- **Philosophy:** "Trust the trend, ignore oscillator warnings, ride winners"
- **Optimized for:** Capturing sustained directional moves
- **Indicator Weighting (vs Balanced 1.0x):**
  \`\`\`
  HEAVY TREND FOCUS:
  ├─ MACD: 2.5x (primary trend confirmation)
  ├─ ADX: 2.5x (trend strength measurement)
  ├─ EMA Crossover: 2.0x (moving average alignment)
  └─ Parabolic SAR: 1.5x (trailing stop system)
  
  DAMPENED OSCILLATORS:
  ├─ RSI: 0.5x (avoid premature exits)
  ├─ Stochastic: 0.5x (ignore overbought/oversold)
  ├─ CCI: 1.0x (kept at baseline)
  └─ Williams %R: 1.0x (kept at baseline)
  
  VOLUME & VOLATILITY:
  ├─ OBV: 1.0x (volume confirmation)
  ├─ CMF: 1.0x (money flow)
  ├─ Bollinger Bands: 1.0x (volatility context)
  └─ ATR: 1.0x (position sizing)
  \`\`\`

**Strategy Characteristics:**
- ✅ Excels in: Strong trending markets (up or down)
- ✅ Wider stops: Avoids getting shaken out of trend
- ✅ Higher R:R: 3:1 minimum (vs 2:1 for balanced)
- ⚠️ Weakness: Choppy/sideways markets cause whipsaws
- ⚠️ Entry timing: Often enters after trend has begun (misses early move)
- ⚠️ Reversal risk: Can hold too long if trend breaks

---

## ⚠️ CRITICAL CONTEXT: SELL TRADE CONSIDERATIONS

**This is a SHORT/SELL position. Special risks apply:**

\`\`\`
SELL Trade Risks vs BUY Trade:
├─ Unlimited upside risk (stop loss is CRITICAL)
├─ Lower circuit limits upside, but you're on wrong side
├─ Short squeeze risk if unexpected positive news
├─ Borrowing costs (if actual short vs just avoiding long)
└─ Sentiment bias: Market has long-term upward drift

For Indian markets specifically:
├─ T+1 settlement makes intraday short selling complex
├─ Delivery-based short selling requires stock borrowing
├─ Most retail traders can only "avoid buying" not "short"
└─ This analysis assumes: Sell existing holdings OR derivative short
\`\`\`

**Recommended Interpretation:**
\`\`\`
IF you own {stockName}:
   → Analysis helps decide: HOLD vs SELL existing position

IF you don't own {stockName}:
   → Analysis helps decide: AVOID or SHORT via Futures/Options

IF shorting via derivatives:
   → Ensure liquidity in F&O segment (check separately)
\`\`\`

---

## 🎯 ANALYSIS OBJECTIVE

**Core Question:**
"Is the detected downtrend strong enough, backed by fundamentals/catalysts, and likely to continue to ₹{target}?"

**Critical Success Factors for SELL Trend:**
1. **Catalyst:** What negative news/event is driving the fall?
2. **Fundamentals:** Are deteriorating metrics justifying lower prices?
3. **Smart Money:** Are institutions exiting? Is delivery % falling?
4. **Sector Weakness:** Is the sector dragging {stockName} down?
5. **Trend Health:** Is momentum accelerating or decelerating?
6. **Reversal Risk:** Any upcoming positive catalysts that could reverse trend?

**Your Mission:**
Perform forensic analysis to determine if this {score} score represents:
- 🟢 **Confirmed Downtrend:** Clear catalysts + weak fundamentals + institutional exit → EXECUTE SELL
- 🟡 **Questionable Downtrend:** Mixed signals, risky to bet on continuation → CAUTION
- 🔴 **False Breakdown:** Technical dip without substance, reversal likely → SKIP SELL

---

## 📋 PRE-ANALYSIS DATA CHECKLIST

**Required Data Sources:**
- [ ] Current stock price & volume (within 24 hours)
- [ ] Recent negative news (past 7-14 days) - **CRITICAL for SELL**
- [ ] Latest financial results (check for deterioration)
- [ ] FII/DII selling data (smart money exit?)
- [ ] Sector performance (is sector weak?)
- [ ] Delivery percentage trend (falling = weak holders)
- [ ] Short interest data (if available via F&O)

**Red Flags to Check:**
- [ ] Earnings miss or guidance cut
- [ ] Promoter selling/pledge increase
- [ ] Regulatory penalties (CDSCO for medical devices)
- [ ] Customer loss or order cancellation
- [ ] Quality issues/product recalls
- [ ] Margin compression
- [ ] Debt covenant breach

**Data Quality Requirement:**
\`\`\`
For SELL signals, data quality is MORE critical than BUY:
- Need confirmation of negative catalysts (can't short on hope)
- Must verify smart money exit (institutions selling)
- Require sector context (isolated weakness vs sector-wide)

If <70% data available → Reduce confidence significantly
\`\`\`

---

## SECTION 1: LIQUIDITY & SHORT EXECUTION FEASIBILITY

### Priority: CRITICAL ⚠️⚠️

**Why This Matters MORE for SELL Trades:**
\`\`\`
Illiquid stocks + Short positions = DISASTER SCENARIO
├─ Can't exit short if stock gaps up on news
├─ Wide spreads = high slippage on entry AND exit
├─ Low delivery % = volatile, manipulation prone
└─ Circuit limits can trap you in losing position

SELL trades require HIGHER liquidity than BUY trades
\`\`\`

### Search Strategy:

Query 1: "{stockName} NSE volume February 2025"
Query 2: "{stockName} delivery percentage"
Query 3: "{stockName} bid ask spread volatility"
Query 4: "{stockName} upper circuit lower circuit hits"
Query 5: "{stockName} futures options liquidity"

### Analysis Tasks:

#### 1. Cash Market Liquidity:

\`\`\`
| Metric | Value | Benchmark for SELL | Status |
|--------|-------|-------------------|---------|
| Avg Daily Value (20D) | ₹[X] Lakhs | >₹1 Cr (REQUIRED) | [✅/⚠️/❌] |
| Avg Daily Volume | [X] shares | >50,000 shares | [✅/⚠️/❌] |
| Delivery % (avg) | [X]% | >50% for safety | [✅/⚠️/❌] |
| Bid-Ask Spread | [X]% | <0.5% (tight) | [✅/⚠️/❌] |
| Free Float | ₹[X] Cr | >₹200 Cr preferred | [✅/⚠️/❌] |
\`\`\`

#### 2. Volatility & Circuit Risk:

\`\`\`
| Risk Indicator | Last 30 Days | Assessment |
|----------------|--------------|------------|
| Upper Circuit Hits | [X] times | [✅ 0 / ⚠️ 1-2 / 🔴 >2] |
| Lower Circuit Hits | [X] times | [Shows selling pressure] |
| Intraday Volatility | [X]% avg | [✅ <5% / ⚠️ 5-10% / 🔴 >10%] |
| Gap Ups (>3%) | [X] times | [🔴 Risk of stop hit] |
| Gap Downs (>3%) | [X] times | [🟢 Confirms downtrend] |
\`\`\`

#### 3. Derivative Market Check (if shorting via F&O):

\`\`\`
IF {stockName} has F&O:
| F&O Metric | Value | Status |
|------------|-------|--------|
| Futures OI | [X] lots | [Adequate/Low] |
| Options OI (PE/CE) | [X] / [Y] | [Put/Call ratio] |
| Futures Spread | ₹[X] | [Wide/Tight] |
| Rollover % | [X]% | [Healthy >70%] |

IF NO F&O:
   → Must sell existing holdings only
   → Cannot actively short this stock
   → Analysis becomes "Hold vs Sell" decision
\`\`\`

### Liquidity Decision Matrix for SELL:

\`\`\`
MANDATORY SKIP if ANY:
├─ Avg Daily Value <₹50 Lakhs → 🔴 TOO ILLIQUID FOR SHORT
├─ Delivery % <30% → 🔴 MANIPULATED, AVOID SHORT
├─ Upper circuits >3 in 30 days → 🔴 TOO VOLATILE, SKIP
└─ No F&O + Don't own stock → ⚪ CANNOT SHORT (not applicable)

PROCEED WITH CAUTION if:
├─ Avg Daily Value ₹50L-₹1Cr → ⚠️ Micro position only (<0.5%)
├─ Delivery % 30-50% → ⚠️ Watch for short squeeze
└─ Wide spreads >1% → ⚠️ Account for 1-2% slippage

SAFE TO SHORT if:
├─ Avg Daily Value >₹1 Cr → ✅ Good liquidity
├─ Delivery % >50% → ✅ Genuine holders
├─ Tight spreads <0.5% → ✅ Efficient execution
└─ Active F&O (if using) → ✅ Multiple exit routes
\`\`\`

**Liquidity Verdict:** [EXECUTE / CAUTION / SKIP]

---

## SECTION 2: NEWS & CATALYST ANALYSIS - "Why Is It Falling?"

### Search Strategy:
Query 1: "{stockName} news negative February 2025"
Query 2: "{stockName} earnings miss profit warning"
Query 3: "{stockName} management resignation issue"
Query 4: "{stockName} penalty regulatory action"

### Analysis Framework:

#### 1. Catalyst Hunt - "What Started the Downtrend?"

**Primary Negative Catalysts (Last 30 Days):**

\`\`\`
Check for these SELL catalysts:
├─ 🔴 Earnings Miss: Results below estimates
├─ 🔴 Guidance Cut: Management lowers forecast
├─ 🔴 Order Cancellation: Key client loss
├─ 🔴 Regulatory Action: SEBI/CDSCO penalty
├─ 🔴 Management Exit: CEO/CFO resignation
├─ 🔴 Margin Compression: Cost pressure announced
├─ 🔴 Debt Concerns: Credit downgrade, covenant breach
├─ 🔴 Quality Issue: Product recall, FDA warning
├─ 🔴 Competitive Loss: Market share decline
└─ 🔴 Sector Headwind: Policy change hurting industry
\`\`\`

**Catalyst Quality:**
- **Primary Catalyst:** [Describe]
- **Duration:** [Short/Medium/Long-term]

#### 2. Catalyst Sustainability - "Will It Keep Falling?"

\`\`\`
🟢 Long-term structural issues → Supports trend to ₹{target}
🟡 Medium-term concerns → Trend may stall
🔴 Short-term noise → Likely reversal before target
\`\`\`

---

## SECTION 3: FUNDAMENTAL DETERIORATION CHECK

### Search Strategy:
Query 1: "{stockName} quarterly results trend"
Query 2: "{stockName} profit margins declining"
Query 3: "{stockName} debt increased balance sheet"

### Analysis Framework:

#### 1. Earnings Trajectory - "Is Profit Story Broken?"

\`\`\`
| Quarter | Revenue (₹Cr) | YoY Growth | EBITDA (₹Cr) | PAT (₹Cr) | YoY Growth | EPS (₹) | Status |
|---------|---------------|------------|--------------|-----------|------------|---------|--------|
| Latest | [X] | [+/-Y%] | [X] | [X] | [+/-Y%] | [X] | [✅/⚠️/❌] |
| Previous | [X] | [+/-Y%] | [X] | [X] | [+/-Y%] | [X] | [✅/⚠️/❌] |
\`\`\`

#### 2. Margin Compression Check:
- Gross Margin Trend: [Expanding/Stable/Contracting]
- Verdict: [🔴 Margins compressing = Bearish / ⚪ Stable / 🟢 Expanding = Contradicts SELL]

#### 3. Debt & Leverage:
- Debt/Equity Trend: [Rising/Stable/Falling]
- **Red Flag:** Rising debt with falling revenue.

#### 4. Valuation - "Has It Become Cheap?"
- P/E Ratio vs Historical Avg: [Premium/Discount]
- **Critical Question:** At ₹{entry}, is stock still overvalued?

### Fundamental Deterioration Verdict:
**Score:** [X/100]
**Interpretation:** [Fundamentally broken (Strong SELL) / Deteriorating / Healthy (Avoid SELL)]

---

## SECTION 4: SMART MONEY FLOW - "Who's Selling?"

### Search Strategy:
Query 1: "{stockName} FII DII selling shareholding pattern"
Query 2: "{stockName} promoter holding change"
Query 3: "{stockName} mutual fund exit"
Query 4: "{stockName} bulk deals selling"

### Analysis Framework:

#### 1. Institutional Exodus Check:
- FII Holding: [Rising/Falling]
- DII Holding: [Rising/Falling]
- **Signal:** [Mass Exodus / Rotation / Accumulation]

#### 2. Promoter Behavior:
- Promoter Holding: [Rising/Stable/Falling]
- Pledged Shares: [Rising/Stable/Falling]
- **Red Flag:** Promoter selling stake or increasing pledge.

#### 3. Volume & Delivery:
- Start of downtrend volume: [High/Low]
- Delivery % trend: [Rising/Falling]
- **Signal:** High volume on down days = Distribution.

### Smart Money Verdict:
**Score:** [X/100]
**Trend Driver:** [Institutional Selling / Retail Panic / Opportunistic Buying]

---

## SECTION 5: SECTOR MOMENTUM & RELATIVE WEAKNESS

### Analysis:
- **Sector Trend:** [Bull/Bear/Sideways]
- **Relative Strength:** Is {stockName} weaker than sector?
- **Sector Rank:** [Top/Mid/Bottom tier]

**Verdict:**
Does Sector Context Support SELL? [✅ YES / ⚠️ MIXED / ❌ NO]

---

## SECTION 6: TREND HEALTH & REVERSAL RISK

### Analysis Framework:
- **Trend Stage:** [Early/Mid/Late/Very Late]
- **Volume Confirmation:** [Healthy/Exhaustion]
- **Divergences:** [Bearish/None/Bullish]
- **Oscillator Risk:** (RSI < 25 or Stoch < 10) = High Reversal Risk.

### Scenario Probability:
- **Base Case (50%):** Downtrend continues to intermediate support.
- **Bull Case (30%):** Clean fall to target ₹{target}.
- **Bear Case (20%):** Reversal stops out trade.

---

## 🎯 FINAL CONSOLIDATED VERDICT

### Multi-Dimensional Scorecard:
| Dimension | Weight | Score /100 | Weighted |
|-----------|--------|------------|----------|
| **Technical Conviction** | 20% | [XX] | [X.X] |
| **Liquidity** | 15% | [XX] | [X.X] |
| **Catalyst Strength** | 15% | [XX] | [X.X] |
| **Fundamental Deterioration** | 20% | [XX] | [X.X] |
| **Smart Money Exit** | 15% | [XX] | [X.X] |
| **Sector Weakness** | 10% | [XX] | [X.X] |
| **Trend Health** | 5% | [XX] | [X.X] |
| **TOTAL SCORE** | **100%** | | **[XX.X]** |

### Decision Matrix:
- **75-100:** ✅ **STRONG SELL** (Full Position).
- **60-74:** ✅ **SELL** (Standard Position).
- **50-59:** ⚠️ **CONDITIONAL SELL** (Reduce Size 50%).
- **<50:** ❌ **SKIP** (Reversal Risk).

### FINAL RECOMMENDATION:
\`\`\`
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  VERDICT: [✅ EXECUTE SELL / ⚠️ CONDITIONAL / ❌ SKIP]        │
│                                                               │
│  Confidence: [🟢 HIGH / 🟡 MEDIUM / 🔴 LOW]                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
\`\`\`

**Action Plan (If Execute):**
- **Entry:** ₹{entry}.
- **Stop Loss:** ₹{stopLoss} (Strict).
- **Target:** ₹{target}.
- **Exit Strategy:** Cover on first sign of sharp reversal or hitting Target.

**Top Risks:**
1. [Highest Risk]
2. [Second Risk]
3. [Third Risk]
`;
