/**
 * Optimized Momentum Breakout HOLD Analysis Prompt
 * 
 * Specialized deep-dive framework for validating HOLD signals in Momentum Breakout strategy.
 * This template uses a "Checklist & Scorecard" approach to validate weak HOLD signals.
 */

export const MOMENTUM_BREAKOUT_HOLD_PROMPT_TEMPLATE = `
# Momentum Breakout Validation: {stockName} ({ticker})
## HOLD SIGNAL - Potential Breakout Setup (Low Conviction)

---

## 🎯 TECHNICAL SIGNAL OVERVIEW

**Stock:** {stockName} ({ticker})
**Sector:** [AUTO-DETECT SECTOR]
**Market Cap:** [AUTO-DETECT] Cr

---

### Technical Analysis Summary

**Signal:** HOLD ⚪
**Conviction Score:** {score} / 1.000 🔴 **VERY WEAK / NEARLY NEUTRAL**
- Score Range: -1.0 (Strong Sell) ← **{score}** ≈ 0.0 (Neutral) → +1.0 (Strong Buy)
- Interpretation: **NO CLEAR BREAKOUT DETECTED**
- Strength: Essentially neutral, barely bearish (within noise range ±0.15)

**Trade Setup:**
- Entry Price: ₹{entry} (Current market price)
- Stop Loss: ₹{stopLoss} (-3.0% wider stops for breakout volatility)
- Target: ₹{target} (+7.5% upside potential)
- Risk: [CALCULATE] per share (3.0%)
- Reward: [CALCULATE] per share (7.5%)
- **Risk-Reward Ratio: 1:2.5** ⭐ (Excellent R:R for breakout trades)

**Strategy:** Momentum Breakout
- **Philosophy:** "Catch the trend as it emerges, ride the momentum wave"
- **Optimized for:** Early detection of new trends forming from consolidation/range
- **Indicator Weighting (vs Balanced 1.0x):**
  \`\`\`
  HEAVY VOLUME FOCUS (Detect Accumulation):
  ├─ OBV: 2.5x (On-Balance Volume - primary breakout detector)
  ├─ CMF: 2.5x (Chaikin Money Flow - institutional flow)
  └─ Purpose: Volume MUST confirm price breakout
  
  MOMENTUM & VOLATILITY (Detect Expansion):
  ├─ RSI: 2.0x (momentum strength, not overbought/oversold)
  ├─ ATR: 2.0x (volatility expansion = breakout energy)
  └─ Purpose: Momentum + volatility surge = real breakout
  
  STANDARD INDICATORS:
  ├─ Stochastic: 1.0x (momentum confirmation)
  ├─ CCI: 1.0x (cyclical extremes)
  ├─ Williams %R: 1.0x (overbought/oversold)
  ├─ Bollinger Bands: 1.0x (volatility breakout)
  
  DAMPENED TREND INDICATORS:
  ├─ MACD: 1.0x (kept at baseline for confirmation)
  ├─ ADX: 1.0x (trend strength developing)
  ├─ EMA Crossover: 1.0x (moving average alignment)
  └─ Parabolic SAR: 1.0x (trailing stops)
  \`\`\`

**Strategy Characteristics:**
- ✅ Excels in: Catching early-stage trends (first 20-30% of move)
- ✅ Wider stops: 3% (tolerates breakout volatility and whipsaws)
- ✅ Higher R:R: 2.5:1 minimum (compensates for lower win rate ~50%)
- ✅ Volume-first: Won't trigger without volume confirmation
- ⚠️ Weakness #1: **FALSE BREAKOUTS** - 40-50% of breakouts fail (return to range)
- ⚠️ Weakness #2: Late triggers - Often enters after 5-10% move already happened
- ⚠️ Weakness #3: Retail traps - Volume spike from FOMO, not institutions
- ⚠️ Weakness #4: No catalyst detection - Technical signal without fundamental reason

---

## ⚠️ CRITICAL CONTEXT: WEAK SIGNAL ALERT

**This is NOT a typical breakout signal. Here's why:**

\`\`\`
Conviction Score: {score}
├─ Interpretation: NO CLEAR BREAKOUT DETECTED
├─ Signal Type: HOLD (not BUY or SELL)
├─ Strength: Extremely weak, essentially random noise
├─ Momentum indicators: Conflicted or flat
├─ Volume indicators: Insufficient confirmation
└─ Price action: Likely consolidating, not breaking out

Translation: "We're waiting for a breakout, but it hasn't happened yet"
\`\`\`

**The "Why Watch?" Test:**
\`\`\`
In Momentum Breakout Strategy:
├─ BUY Signal: Breakout detected, enter now
├─ HOLD Signal: Potential setup forming, WAIT for confirmation
├─ SELL Signal: Breakdown detected or failed breakout
└─ Score {score}: No clear direction, market indecisive

THIS IS A "WATCHLIST" SIGNAL, NOT A "TRADE NOW" SIGNAL
\`\`\`

**Critical Questions to Answer:**
1. Is a breakout ABOUT TO happen? (Pre-breakout setup?)
2. What would TRIGGER the breakout? (Catalyst needed)
3. Which direction will it break? (Up or down?)
4. Should we WAIT for confirmation or anticipate?
5. Is there enough setup quality to even monitor this stock?

---

## 🎯 ANALYSIS OBJECTIVE

**Core Mission:**
"Determine if {stockName} is setting up for a breakout, what would trigger it, and whether we should even care."

**Decision Tree:**
\`\`\`
IF Clear pre-breakout pattern + Catalyst identified + Volume building:
   → ⚠️ ADD TO WATCHLIST - Set price/volume alerts
   → Enter ONLY when breakout confirmed (price + volume)

ELSE IF Consolidation but no catalyst or poor setup:
   → ❌ SKIP - Better opportunities elsewhere

ELSE IF Already broken out (but score shows {score}?):
   → 🔴 CONTRADICTORY - Investigate data quality
   → Likely a false signal or data error
\`\`\`

**Your Mission:**
Validate whether this "HOLD" represents:
- 🟢 **Pre-Breakout Setup:** Good consolidation, just needs catalyst → WATCHLIST
- 🟡 **Noise:** No clear pattern, random sideways → IGNORE
- 🔴 **False Signal:** Technical glitch or poor data → SKIP ENTIRELY

---

## 📋 PRE-ANALYSIS DATA CHECKLIST

**Required Data Sources:**
- [ ] Recent price action (last 3 months chart)
- [ ] Volume pattern (building vs declining)
- [ ] Consolidation range (if any)
- [ ] Recent news/catalysts (what could trigger breakout?)
- [ ] Resistance levels to break
- [ ] Institutional activity (accumulation phase?)
- [ ] Sector context (is sector setting up too?)
- [ ] Fundamentals (justify higher prices?)

**Momentum Breakout-Specific Checks:**
- [ ] Is there a defined consolidation/base building?
- [ ] Is volume contracting (calm before storm)?
- [ ] Any upcoming catalysts (earnings, events)?
- [ ] Are institutions accumulating quietly?
- [ ] Is resistance level clearly defined?
- [ ] What % breakout above resistance would confirm?

---

## SECTION 1: BREAKOUT SETUP VALIDATION & PATTERN RECOGNITION

### Priority: CRITICAL ⚠️⚠️⚠️

**Why This Matters Most:**
Momentum Breakout's Core Assumption: "Stock is consolidating, building energy, about to explode in one direction"

### Search Strategy:
Query 1: "{stockName} chart pattern consolidation base building"
Query 2: "{stockName} technical analysis support resistance levels"
Query 3: "{stockName} price action last 3 months"
Query 4: "{stockName} volume trend increasing decreasing"

### Analysis Framework:

#### 1. Chart Pattern Recognition:
**Pattern Types to Check:**
- **Consolidation:** Rectangle, Triangle, Flag, Cup & Handle.
- **Continuation:** Ascending Triangle, Bull Flag.
- **No Pattern:** Choppy, random sideways.

**{stockName} Current Pattern:**
Pattern Detected: [Name or "No clear pattern"]
Duration: [X] weeks
Price Range: ₹[LOW] to ₹[HIGH]
Tightness: [Contracting / Stable / Expanding]

**Pattern Quality Score:**
- ✅ **STRONG:** Clear structure, >6 weeks, Low Volume.
- 🔴 **POOR:** Choppy, <3 weeks, High Volume selling.

#### 2. Key Price Levels:
- **Resistance (Breakout Trigger):** ₹[Start watching here]
- **Support (Invalidation):** ₹[Stop watching here]

#### 3. Volume Analysis (Critical):
**Volume During Consolidation:**
- ✅ **Ideal:** Declining 20-30% ("Drying Up").
- 🔴 **Bad:** Increasing without breakout (Distribution).

#### 4. Volatility (ATR & Bollinger):
- **Squeeze:** Are Bollinger Bands narrowing? (Big move coming).
- **ATR:** Is it declining? (Energy building).

### Breakout Setup Verdict:
**Setup Score:** [0-100]
**Interpretation:**
- >80: Prime Setup (Watchlist).
- <40: Noise (Skip).

---

## SECTION 2: CATALYST IDENTIFICATION & VALIDATION

### Search Strategy:
Query 1: "{stockName} news catalyst recent"
Query 2: "{stockName} earnings surprise guidance"
Query 3: "{stockName} new orders contract wins"

### Analysis Framework:
**Catalyst Hunt - "What Could Trigger the Breakout?"**
- 🟢 **Strong:** Earnings beat, Major order, Policy change.
- 🟡 **Moderate:** Expansion news, Sector sentiment.
- ⚪ **Weak:** No news.

**If NO catalyst found:**
→ 🔴 MAJOR RED FLAG. Breakouts without news fail 60% of the time.

**Catalyst Score:** [0-100]

---

## SECTION 3: FUNDAMENTAL REVALUATION ANALYSIS

### Search Strategy:
Query 1: "{stockName} fair value target price"
Query 2: "{stockName} PE ratio vs sector"
Query 3: "{stockName} earnings growth estimates"

### Analysis Framework:
**Valuation Check:**
- Is the stock cheap enough to run +20%?
- Or is it already expensive?

**Growth Drivers:**
- Revenue accelerating?
- Margins expanding?

**Fundamental Justification Score:** [0-100]

---

## SECTION 4: SMART MONEY VALIDATION & INSTITUTIONAL FLOW

### Search Strategy:
Query 1: "{stockName} FII DII shareholding change"
Query 2: "{stockName} bulk deals recent"
Query 3: "{stockName} delivery percentage trend"

### Analysis Framework:
**Who is buying?**
- ✅ **Institutions:** High delivery %, FIIs increasing stake.
- 🔴 **Retail:** Low delivery %, FIIs selling.

**Smart Money Score:** [0-100]

---

## SECTION 5: SECTOR ROTATION & MARKET CONTEXT

### Search Strategy:
Query 1: "{sector} sector outlook India"
Query 2: "{stockName} vs {sector} relative performance"

### Analysis Framework:
**Sector Momentum:**
- Is the sector outperforming Nifty?
- Is {stockName} a Leader or Laggard in the sector?

**Sector Score:** [0-100]

---

## 🎯 FINAL CONSOLIDATED VERDICT

### Comprehensive Scorecard:
| Dimension | Weight | Score /100 | Weighted |
|-----------|--------|------------|----------|
| **Technical Setup** | 20% | [XX] | [X.X] |
| **Catalyst Strength** | 25% | [XX] | [X.X] |
| **Fundamental Support** | 20% | [XX] | [X.X] |
| **Smart Money Backing** | 20% | [XX] | [X.X] |
| **Sector Context** | 15% | [XX] | [X.X] |
| **TOTAL SCORE** | **100%** | | **[XX.X]** |

### Decision Matrix:
- **80-100:** ✅ **EXCELLENT SETUP** (Priority Watchlist).
- **65-79:** ✅ **GOOD SETUP** (Watchlist).
- **50-64:** ⚠️ **MEDIOCRE** (Optional).
- **<50:** 🔴 **NO SETUP** (Skip).

### FINAL RECOMMENDATION:
\`\`\`
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  CURRENT STATUS: [⚪ WATCHLIST / ✅ ENTER ON BREAKOUT / 🔴 SKIP] │
│                                                               │
│  Confidence: [🟢 HIGH / 🟡 MEDIUM / 🔴 LOW]                   │
│                                                               │
│  False Breakout Risk: [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH]          │
│                                                               │
└──────────────────────────────────────────────────────────────┘
\`\`\`

**Action Plan (If Watchlist):**
- **Trigger:** Alert at ₹[Resistance + 2%].
- **Volume:** Must be >1.5x Avg.
- **Stop Loss:** ₹{stopLoss} (Strict).
- **Target:** ₹{target}.

**Top Risks:**
1. False Breakout (Trap).
2. Market Reversal.
3. [Specific Risk].
`;
