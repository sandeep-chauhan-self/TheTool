/**
 * Optimized Weekly 4% Target HOLD Analysis Prompt
 * 
 * Specialized deep-dive framework for validating HOLD (or weak BUY) signals in Weekly 4% Target strategy.
 * This template uses the FULL "Deep Dive" structure with 5 sections, search queries, and rigorous probability assessment.
 */

export const WEEKLY_TARGET_HOLD_PROMPT_TEMPLATE = \`
# Swing Trade Validation: {stockName} ({ticker})
## HOLD SIGNAL - 4% Target in 3 Weeks (Low Conviction)

---

## 🎯 TECHNICAL SIGNAL OVERVIEW

**Stock:** {stockName} ({ticker})
**Sector:** [AUTO-DETECT SECTOR]
**Market Cap:** [AUTO-DETECT] Cr

---

### Technical Analysis Summary

**Signal:** HOLD ⚪
**Conviction Score:** {score} / 1.000 🔴 **VERY WEAK / BARELY BULLISH**
- Score Range: -1.0 (Strong Sell) ← 0.0 (Neutral) → **{score}** → +1.0 (Strong Buy)
- Interpretation: **MINIMAL BULLISH BIAS - ESSENTIALLY NEUTRAL**
- Strength: Extremely weak, barely out of noise range (±0.15)

**Trade Setup:**
- Entry Price: ₹{entry} (Current market price)
- Stop Loss: ₹{stopLoss} (-4.0% dynamic ATR-based)
- Target: ₹{target} (+4.0% profit target)
- Risk: ~4.0% per share
- Reward: ~4.0% per share
- **Risk-Reward Ratio: 1:1** (Break-even R:R - relies on win rate)
- **Maximum Holding Period: 15 bars (~3 weeks / 15 trading days)**
- **Time Decay Pressure: YES** (must hit target within 3 weeks or exit)

**Strategy:** Weekly 4% Target (Swing Trading)
- **Philosophy:** "Capture short-term momentum swings with defined profit targets and strict time limits"
- **Optimized for:** 1-3 week swing trades in stocks showing momentum convergence
- **Position Sizing:** Up to 35% of portfolio (HIGH for swing trades)

**Strategy Characteristics:**
- ✅ Clear profit target: Always 4% (no greed, no hoping)
- ✅ Clear time limit: Max 15 bars (no bag-holding)
- ✅ Intelligent filters: SMA(50) trend + ADX >20 + momentum convergence
- ✅ High position sizing: Up to 35% (concentration on best setups)
- ⚠️ Moderate win rate: 55-65%
- ⚠️ Target hit rate: Only 40-45% (many time exits before target)
- ⚠️ Event vulnerability: 3-week hold = exposed to earnings, news

---

## ⚠️ CRITICAL CONTEXT: WEAK SIGNAL + SHORT TIMEFRAME

**This is NOT a strong setup. Here's why:**
\`\`\`
Conviction Score: {score}
├─ Interpretation: BARELY BULLISH, mostly neutral
├─ Momentum indicators: Slightly positive but not converged
├─ Trend: Probably above SMA(50) but weak
└─ Overall: WEAK SETUP, borderline entry

Translation: "Momentum is barely there, trend is weak, this is a coin flip"
\`\`\`

**The 4% Target Challenge:**
\`\`\`
Target: ₹{target} (4% gain)
Timeframe: Maximum 15 bars (3 weeks)
Current Conviction: {score} (very weak)

Reality Check:
├─ Weak signals have LOWER probability of hitting 4% target
├─ More likely scenario: Small gain (1-2%) → time exit at bar 15
├─ Time decay: Every bar that passes without progress reduces odds
└─ This weak signal likely has <30% chance of hitting full 4%
\`\`\`

**The Position Size Issue:**
\`\`\`
Strategy allows UP TO 35% position.
BUT score {score} = VERY WEAK.

→ Should use 5-10% position MAX, not 35%
→ Or skip and wait for stronger setup
\`\`\`

---

## 🎯 ANALYSIS OBJECTIVE

**Core Mission:**
"Determine if {stockName} can realistically achieve 4% gain within 3 weeks, given the weak technical setup, and assess appropriate position sizing."

**Your Mission:**
Validate whether this {score} score represents:
- 🟢 **Marginal Entry:** Weak but tradeable with reduced size → 10-15% position
- 🟡 **Watchlist:** Wait for improvement to >0.25 → Monitor, don't enter yet
- 🔴 **Skip:** Too many negatives, ignore entirely → Focus elsewhere

---

## 📋 PRE-ANALYSIS DATA CHECKLIST

**Required Data:**
- [ ] Event calendar (next 21 days - earnings, dividends)
- [ ] VIX & market breadth
- [ ] Historical volatility (can {stockName} move 4% in 3 weeks?)
- [ ] Fundamental quick check (earnings, debt)

**Data Quality for Short-Term Trades:**
Swing trading needs CURRENT data. If event calendar incomplete → MANDATORY SKIP.

---

## SECTION 1: EVENT CALENDAR & BINARY RISK ASSESSMENT

### Priority: CRITICAL ⚠️⚠️⚠️

**Why This Is THE Most Important Section:**
For 3-Week Swing Trades, ONE unexpected event can destroy the trade. You cannot afford to hold through earnings with a 3-week time limit.

### Search Strategy:
Query 1: "{stockName} earnings date Q4 FY25 when announcement"
Query 2: "{stockName} dividend ex-date record date"
Query 3: "{stockName} board meeting schedule"
Query 4: "India economic calendar next 21 days"

### Analysis Framework:

#### 1. Earnings Calendar - THE Critical Risk:
**Next Earnings Report:**
- Expected Quarter: Next upcoming quarter
- **Days from Entry:** [X] trading days
- **Falls within 15-bar window? [YES ⚠️⚠️ / NO ✅]**

**MANDATORY ASSESSMENT:**
- **Earnings in bars 1-10:** 🔴🔴 ABORT TRADE (Too early, high gap risk)
- **Earnings in bars 11-15:** 🔴 HIGH RISK (Exit by bar 10 recommended)
- **Earnings >150 bars:** ✅ SAFE

#### 2. Dividend & Corporate Actions:
**Ex-Dividend Date Risk:**
- If Ex-Date within 15 bars, price drops by dividend amount.
- Must adjust target: ₹{target} → New Target.

#### 3. Consolidated Event Risk Score:
| Event Type | Date | Risk Level |
|------------|------|------------|
| Earnings | [Date] | [🔴/🟡/✅] |
| Dividend | [Date] | [🟡/✅] |
| Board Meeting | [Date] | [🔴/🟡/✅] |
| **TOTAL VERDICT** | | **[Safe / Risky / Critical]** |

**Action:**
IF Risk High → SKIP trade or Exit before event.

---

## SECTION 2: MARKET REGIME & SWING TRADE ENVIRONMENT

### Search Strategy:
Query 1: "India VIX current level"
Query 2: "Nifty 50 trend > 50 DMA"
Query 3: "FII DII flows India recent"

### Analysis Framework:

#### 1. Volatility Environment (VIX):
- **Current VIX:** [Value]
- **Zones:**
  - VIX <15: 🟢 Good for swings
  - VIX 15-20: ✅ Acceptable
  - VIX >20: 🔴 Too volatile (Stop run risk)

#### 2. Index Trend Alignment:
- **Nifty 50:** [Above/Below 50 DMA?]
- **Assessment:**
  - If Market Below 50 DMA + Stock Weak Signal = 🔴 HIGH RISK (Fighting the tide)

#### 3. Market Regime Verdict:
**Should 4% Target Swing Trades Be Deployed?**
[✅ YES / ⚠️ CONDITIONAL / 🔴 NO]

---

## SECTION 3: HISTORICAL VOLATILITY & TARGET ACHIEVABILITY

### Search Strategy:
Query 1: "{stockName} historical volatility average weekly move"
Query 2: "{stockName} ATR"
Query 3: "{stockName} price movement last 3 months"

### Analysis Framework:

#### 1. Historical Movement Analysis:
- **Avg 3-Week Move:** [X]%
- **Achievability of 4%:**
  - Avg >5%: ✅ EASY
  - Avg 3-5%: ✅ ACHIEVABLE
  - Avg <3%: 🔴 UNREALISTIC (Stock too quiet)

#### 2. ATR & Stop Loss Check:
- **Current ATR:** ₹[X]
- **Your Stop:** ₹{stopLoss} (-4% distance = ₹[Calc])
- **Ratio:** Stop is [X]x ATR. (Ideal is 2-3x ATR).

#### 3. Target Achievability Verdict:
**Can {stockName} Realistically Move 4% in 15 Bars?**
[✅ YES / ⚪ MAYBE / 🔴 UNLIKELY]

**Realistic Expectation:**
Given weak score {score}, expect: [1-2% gain / Full 4% / Stop check]

---

## SECTION 4: FUNDAMENTAL QUICK SCREEN

### Search Strategy:
Query 1: "{stockName} quarterly results recent"
Query 2: "{stockName} debt equity ratio"
Query 3: "{stockName} promoter holding"

### Analysis Framework (Rapid Assessment):
1.  **Recent Earnings:** [Beat/Miss]
2.  **Debt Health:** [High/Low]
3.  **Promoter:** [Stable/Selling]

**Fundamental Score:** [X]/6 Green Lights
**Verdict:** [✅ Safe / ⚠️ Concerns / 🔴 Unsafe]

---

## 🎯 FINAL CONSOLIDATED VERDICT

### Reconciling Weak {score} Signal:
This is a BORDERLINE signal. Higher probability of time exit with small gain than hitting full 4% target.

### Decision Matrix For Swing Trades:
- 70-100 Score: ✅ HIGH CONVICTION (10-15% size)
- 40-69 Score: ⚠️ LOW CONVICTION (3-5% size or SKIP)
- <40 Score: 🔴 SKIP

### Critical Override Rules:
🔴 **MANDATORY SKIP IF:** Earnings in <10 bars OR VIX >22 OR Fundamentals Poor.

### FINAL RECOMMENDATION:

\`\`\`
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  VERDICT: [✅ EXECUTE / ⚠️ EXECUTE REDUCED / 🔴 SKIP]         │
│                                                               │
│  Position Size: [X]% (Recommended 5-10% for weak signal)     │
│                                                               │
│  4% Target Probability: [🟢 >50% / 🟡 30-50% / 🔴 <30%]      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
\`\`\`

**Execution Plan (If Trading):**
- **Entry:** ₹{entry}
- **Stop Loss:** ₹{stopLoss} (STRICT)
- **Target:** ₹{target} or Time Exit
- **Time Exit:** Bar 15 ([Date]) - **MANDATORY EXIT**

**Top Risk:** [Time Decay / Earnings / Market Chop]
\`;
