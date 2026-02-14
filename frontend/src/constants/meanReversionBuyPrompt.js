/**
 * Optimized Mean Reversion BUY Analysis Prompt
 * 
 * Specialized deep-dive framework for validating BUY signals in Mean Reversion strategy.
 * Focuses on range validation, breakout risk, and fundamental fair value alignment.
 */

export const MEAN_REVERSION_BUY_PROMPT_TEMPLATE = `
# Mean Reversion Trade Validation: {stockName} ({ticker})
## BUY SIGNAL - Oversold Bounce Expected

---

## 🎯 TECHNICAL SIGNAL OVERVIEW

**Stock:** {stockName} ({ticker})
**Sector:** [AUTO-DETECT SECTOR]
**Market Cap:** [AUTO-DETECT] Cr

---

### Technical Analysis Summary

**Signal:** BUY 🟢
**Conviction Score:** {score} / 1.000 🟡 **MODERATE BULLISH**
- Score Range: -1.0 (Strong Sell) ← 0.0 (Neutral) → **{score}** → +1.0 (Strong Buy)
- Interpretation: **MODERATELY OVERSOLD - Mean Reversion Opportunity**
- Strength: Mid-range bullish (not weak, not extreme)

**Trade Setup:**
- Entry Price: ₹{entry} (Current market price - near support)
- Stop Loss: ₹{stopLoss} (-1.5% tight stops for range trades)
- Target: ₹{target} (+2.25% upside potential)
- Risk: [CALCULATE] per share (1.5%)
- Reward: [CALCULATE] per share (2.25%)
- **Risk-Reward Ratio: 1:1.5** (Lower R:R, higher win rate expected)

**Strategy:** Mean Reversion
- **Philosophy:** "Buy oversold, sell overbought, play the range"
- **Optimized for:** Sideways, range-bound markets with clear support/resistance
- **Indicator Weighting (vs Balanced 1.0x):**
  \`\`\`
  HEAVY OSCILLATOR FOCUS:
  ├─ RSI: 2.5x (primary oversold detector)
  ├─ Bollinger Bands: 2.5x (price extremes, band bounces)
  ├─ Stochastic: 2.0x (momentum oversold)
  ├─ CCI: 1.5x (cyclical extremes)
  └─ Williams %R: 1.5x (overbought/oversold)
  
  DAMPENED TREND INDICATORS:
  ├─ MACD: 0.5x (ignore trend to buy dips)
  ├─ ADX: 0.5x (ignore trend strength)
  ├─ EMA Crossover: 0.5x (de-emphasize trend)
  └─ Parabolic SAR: 0.5x (ignore trailing stops)
  
  VOLATILITY & VOLUME:
  ├─ Bollinger Bands: 2.5x (also counts here - volatility)
  ├─ ATR: 1.0x (position sizing, stop placement)
  ├─ OBV: 1.0x (volume confirmation)
  └─ CMF: 1.0x (money flow at extremes)
  \`\`\`

**Strategy Characteristics:**
- ✅ Excels in: Sideways, range-bound markets (70-80% win rate)
- ✅ Tight stops: 1.5% (minimizes loss per trade)
- ✅ Quick trades: Typically 3-10 days holding period
- ✅ Counter-trend: Buy dips, sell rips (contrarian)
- ⚠️ Weakness #1: **BREAKOUTS** - Fails catastrophically when range breaks
- ⚠️ Weakness #2: Strong trends - Gets stopped out repeatedly
- ⚠️ Weakness #3: Event risk - Tight stops vulnerable to gaps
- ⚠️ Weakness #4: Whipsaws - Can be shaken out of good positions

---

## ⚠️ CRITICAL CONTEXT: MEAN REVERSION RISKS

**This is a COUNTER-TREND strategy. Special considerations apply:**

\`\`\`
Mean Reversion vs Trend Following:
├─ MR: Buys when others panic (contrarian)
├─ TF: Buys when momentum builds (confirmatory)
├─ MR: Assumes price will return to average
├─ TF: Assumes trend will continue
├─ MR: Works in 60% of market conditions (sideways)
├─ TF: Works in 40% of market conditions (trending)
└─ MR: Higher win rate, smaller wins

The BIGGEST Risk: BREAKOUTS
├─ Mean reversion assumes range will hold
├─ But ranges ALWAYS eventually break
├─ When they do, your 1.5% stop may not be enough
├─ Breakout can gap past your stop (slippage)
└─ Example: Earnings gap can cause >5% loss vs 1.5% planned
\`\`\`

**Critical Success Factors for Mean Reversion:**
\`\`\`
✅ MUST HAVE:
1. Well-defined range (clear support/resistance)
2. Multiple bounces (range tested 3+ times)
3. No imminent breakout catalysts (earnings >2 weeks away)
4. Low volatility environment (VIX <20, ATR stable)
5. Fundamentals support current price range
6. Market regime: Sideways/consolidating (not trending)

❌ AVOID IF:
1. Range is new (<4 weeks old)
2. Volatility compressing (breakout imminent)
3. Major event in next 7 days
4. Strong trend forming (MACD, ADX rising despite dampening)
5. Fundamental shift (earnings deterioration, news catalyst)
6. Market in strong trend (Nifty making new highs/lows)
\`\`\`

---

## 🎯 ANALYSIS OBJECTIVE

**Core Question:**
"Is {stockName} in a stable range where ₹{entry} represents oversold support that will bounce to ₹{target}, OR is this a breakdown in progress?"

**Decision Tree:**
\`\`\`
IF Range is intact + No breakout risk + No events + Fundamentals support:
   → ✅ EXECUTE Mean Reversion trade

ELSE IF Range weakening OR Event risk OR Breakout signals:
   → ⚠️ SKIP or WAIT for clarity

ELSE IF Range already broken OR Strong trend emerging:
   → ❌ ABORT - Strategy mismatch (use Trend Following instead)
\`\`\`

**Your Mission:**
Forensically validate whether this score represents:
- 🟢 **Valid Mean Reversion:** Clear range, oversold bounce setup → EXECUTE
- 🟡 **Questionable Setup:** Some risk factors present → CAUTION / REDUCE SIZE
- 🔴 **False Signal:** Range breaking, trending, or event risk → SKIP

---

## 📋 PRE-ANALYSIS DATA CHECKLIST

**Required Data Sources:**
- [ ] Price action (last 3-6 months for range identification)
- [ ] Support/resistance levels (chart analysis required)
- [ ] Volume at extremes (buying at support, selling at resistance)
- [ ] ATR / Bollinger Band width (volatility trend)
- [ ] Event calendar (earnings, dividends, board meetings)
- [ ] Fundamental fair value estimate
- [ ] Options data (if F&O available) - PCR, Max Pain, IV
- [ ] Market regime (Nifty trending or sideways?)

**Mean Reversion-Specific Checks:**
- [ ] How many times has support level held?
- [ ] How many times has resistance level acted as ceiling?
- [ ] Is volatility contracting (squeeze before breakout)?
- [ ] Any upcoming binary events (earnings, regulatory decisions)?
- [ ] Is broader market in sideways consolidation?

---

## SECTION 1: RANGE VALIDATION & BREAKOUT RISK ASSESSMENT

### Priority: CRITICAL ⚠️⚠️⚠️

**Why This Is THE Most Important Section:**
Mean Reversion's Achilles Heel = BREAKOUTS. We must validate range integrity.

### Search Strategy:
Query 1: "{stockName} stock chart 3 month 6 month support resistance"
Query 2: "{stockName} trading range technical analysis"
Query 3: "{stockName} 52 week high low range"
Query 4: "{stockName} ATR volatility Bollinger Band width"

### Analysis Framework:

#### 1. Range Definition & History:
**Current Trading Range (Last 3 Months):**
- Resistance (Upper Bound): ₹[HIGH] - tested [X] times
- Support (Lower Bound): ₹[LOW] - tested [Y] times
- Range Width: [Z]%
- Current Position: ₹{entry} is [X]% from support, [Y]% from resistance

**Range Quality Score:**
- ✅ **Strong:** >8 weeks duration, 4+ touches, volume spikes at extremes.
- 🔴 **Weak:** <6 weeks, <3 touches, narrowing width.

#### 2. Entry Point Validation:
**Where is ₹{entry} in the Range?**
- Distance from Support: [X]%
- ✅ **Ideal:** Within 3-5% of support.
- 🔴 **Danger:** Below support (breakdown).

#### 3. Volatility Analysis - Compression Check:
**Bollinger Band Width & ATR Trend:**
- Trend: [Compressing / Stable / Expanding]
- **CRITICAL ALERT:** If BB Width declining for 2+ weeks → Squeeze forming → Breakout imminent → **AVOID MR**.

#### 4. Volume Pattern Analysis:
**Volume at Range Extremes:**
- ✅ **Healthy:** High volume at support (buyers), High at resistance (sellers).
- 🔴 **Warning:** Increasing volume at resistance (breakout building).

#### 5. False Breakout History:
- Count of false breakouts: [X]
- ✅ More false breakouts = Stronger range (traps traders).

---

## SECTION 2: FUNDAMENTAL FAIR VALUE ALIGNMENT

### Search Strategy:
Query 1: "{stockName} intrinsic value fair value estimate"
Query 2: "{stockName} PE ratio historical average"
Query 3: "{stockName} analyst target price consensus"

### Analysis Framework:
**Intrinsic Value Estimation:**
- P/E Fair Value: ₹[CALC]
- P/B Fair Value: ₹[CALC]
- Consensus Fair Value: ₹[CALC]
- **Working Fair Value: ₹[MID]**

**Range Alignment:**
- ✅ **Ideal:** Fair Value ≈ Range Midpoint.
- 🔴 **Misalignment:** Fair Value >10% above resistance (Breakout risk) or <10% below support (Breakdown risk).

**Fundamental Trend:** [Improving / Stable / Deteriorating]

---

## SECTION 3: EVENT RISK & CALENDAR ANALYSIS

### Search Strategy:
Query 1: "{stockName} earnings date Q4 calendar"
Query 2: "{stockName} dividend record date"
Query 3: "{stockName} board meeting schedule"
Query 4: "Medical devices sector India policy news"

### Analysis Framework:
**Next Earnings Report:**
- Date: [DD-MMM] ([X] days away)
- **Risk:** If <7 days → **EXIT/SKIP** (Gap risk).

**Corporate Actions:**
- Dividends/Splits: [Date]
- Board Meetings: [Date]

**Event Risk Verdict:**
- ✅ **Clean:** No events >14 days.
- 🔴 **Extreme:** Earnings in 0-3 days.

---

## SECTION 4: OPTIONS MARKET SENTIMENT (If F&O)

### Search Strategy:
Query 1: "{stockName} put call ratio PCR"
Query 2: "{stockName} options open interest strike"
Query 3: "{stockName} max pain level"
Query 4: "{stockName} implied volatility IV"

### Analysis Framework:
**Put-Call Ratio (PCR):**
- >1.2: Bearish crowd (Good for MR Long bounce).
- <0.8: Bullish crowd (Limited upside).

**Max Pain vs Target:**
- Does Max Pain align with our Target ₹{target}?

**Implied Volatility (IV):**
- Low IV Rank (<30): ✅ Good for MR.
- High IV Rank (>70): 🔴 Dangerous (Big move coming).

---

## SECTION 5: MARKET REGIME & MACRO CONTEXT

### Search Strategy:
Query 1: "Nifty 50 trend current bull bear sideways"
Query 2: "VIX India volatility level"
Query 3: "FII DII flows recent"

### Analysis Framework:
**Market Trend:**
- ✅ **Sideways:** Nifty oscillating. Ideal for MR.
- 🔴 **Trending:** Nifty making new highs/lows. Bad for MR (use Trend Following).

**Volatility (VIX):**
- <15: Low vol, safe.
- >20: High vol, risky stops.

---

## 🎯 FINAL CONSOLIDATED VERDICT

### Comprehensive Scorecard:
| Dimension | Weight | Score /100 | Weighted |
|-----------|--------|------------|----------|
| **Range Integrity** | 25% | [XX] | [X.X] |
| **Technical Conviction** | 20% | [XX] | [X.X] |
| **Fundamental Alignment** | 15% | [XX] | [X.X] |
| **Event Risk (inverse)** | 15% | [XX] | [X.X] |
| **Options Sentiment** | 10% | [XX] | [X.X] |
| **Market Regime** | 15% | [XX] | [X.X] |
| **TOTAL SCORE** | **100%** | | **[XX.X]** |

### Decision Matrix:
- **80-100:** ✅ **TEXTBOOK SETUP** (Execute).
- **65-79:** ✅ **GOOD SETUP** (Standard Size).
- **50-64:** ⚠️ **ACCEPTABLE** (Reduce Size 50%).
- **<50:** 🔴 **SKIP** (Avoid).

### FINAL RECOMMENDATION:
\`\`\`
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  VERDICT: [✅ EXECUTE MR / ⚠️ CONDITIONAL / 🔴 SKIP]          │
│                                                               │
│  Confidence: [🟢 HIGH / 🟡 MEDIUM / 🔴 LOW]                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
\`\`\`

**Action Plan (If Execute):**
- **Entry:** ₹{entry}.
- **Stop Loss:** ₹{stopLoss} (Strict 1.5%).
- **Target:** ₹{target}.
- **Exit Rule:** Exit if earnings <7 days away or range breaks.

**Top Risks:**
1. Breakout/Range Break.
2. Earnings Gap.
3. Market Trend Shift.
`;
