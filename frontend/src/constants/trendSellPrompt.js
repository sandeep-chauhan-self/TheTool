/**
 * Trend Following Strategy Analysis Prompt - SELL Signals
 * Version: 2.0 - Dynamic Template
 * 
 * Optimized for SELL signals in trending markets.
 * Focuses on downtrend validation, catalyst identification, and smart money exits.
 * 
 * Variables:
 * @param {string} stockName - Company name (e.g., "SOMATEX Medical Polymers")
 * @param {string} ticker - Stock symbol (e.g., "SOMATEX.NS")
 * @param {string} verdict - Signal type: "Sell" expected
 * @param {number} score - Conviction score (-1.0 to 0.0 for SELL)
 * @param {number} entry - Entry price in ₹
 * @param {number} stopLoss - Stop loss price in ₹
 * @param {number} target - Target price in ₹
 * @param {string} strategyName - "Trend Following"
 * @param {string} date - Current date
 */

export const TREND_FOLLOWING_PROMPT = `
# Trend-Following Trade Validation: {stockName} ({ticker})
## {verdict} SIGNAL - Downtrend Confirmation Required

---

## 🎯 TECHNICAL SIGNAL OVERVIEW

**Stock:** {stockName} ({ticker})
**Sector:** [AUTO-DETECT via web search]
**Market Cap:** ₹[AUTO-DETECT via web search] Cr
**Analysis Date:** {date}

---

### Technical Analysis Summary

**Signal:** {verdict} 🔴
**Conviction Score:** {score} / 1.000 ${
  Math.abs(parseFloat('{score}')) > 0.70 
    ? '🔴🔴 **STRONG BEARISH**' 
    : Math.abs(parseFloat('{score}')) > 0.50 
      ? '🔴 **MODERATE BEARISH**'
      : Math.abs(parseFloat('{score}')) > 0.30
        ? '🟡 **WEAK BEARISH**'
        : '⚪ **BARELY BEARISH**'
}

**Score Interpretation:**
\`\`\`
Score Range: -1.0 (Strong Sell) ← {score} → 0.0 (Neutral) → +1.0 (Strong Buy)

Position on Scale:
│────────────────────┼─────────┼─────────┼─────────┼
-1.0              -0.5      0.0      0.5      1.0
${parseFloat('{score}') < -0.70 ? '▼' :
  parseFloat('{score}') < -0.50 ? '    ▼' :
  parseFloat('{score}') < -0.30 ? '         ▼' :
  '              ▼'}

Current: {score}
Assessment: ${
  Math.abs(parseFloat('{score}')) > 0.70 
    ? 'STRONG DOWNTREND DETECTED - High conviction'
    : Math.abs(parseFloat('{score}')) > 0.50
      ? 'MODERATE DOWNTREND DETECTED - Mid-range bearish'
      : Math.abs(parseFloat('{score}')) > 0.30
        ? 'WEAK DOWNTREND - Low conviction'
        : 'BARELY BEARISH - Nearly neutral, questionable trade'
}
\`\`\`

**Trade Setup:**
- **Entry Price:** ₹{entry} (Current market price)
- **Stop Loss:** ₹{stopLoss}
  - Risk: ₹${Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')).toFixed(2)}
  - Risk %: ${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(2)}%
- **Target:** ₹{target}
  - Reward: ₹${Math.abs(parseFloat('{entry}') - parseFloat('{target}')).toFixed(2)}
  - Reward %: ${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(2)}%
- **Risk-Reward Ratio:** 1:${(Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}'))).toFixed(2)} ${
  (Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}'))) >= 3.0 
    ? '⭐ (Excellent for trend trades)'
    : (Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}'))) >= 2.0
      ? '✅ (Good)'
      : '⚠️ (Marginal - requires high conviction)'
}

**Strategy:** {strategyName}
- **Philosophy:** "Trust the trend, ignore oscillator warnings, ride winners"
- **Optimized for:** Capturing sustained directional moves (down in this case)
- **Indicator Weighting (vs Balanced 1.0x):**
\`\`\`
  HEAVY TREND FOCUS:
  ├─ MACD: 2.5x (primary trend confirmation)
  ├─ ADX: 2.5x (trend strength measurement)
  ├─ EMA Crossover: 2.0x (moving average alignment)
  └─ Parabolic SAR: 1.5x (trailing stop system)
  
  DAMPENED OSCILLATORS (intentionally muted):
  ├─ RSI: 0.5x (avoid premature exits on "oversold")
  ├─ Stochastic: 0.5x (ignore overbought/oversold)
  ├─ CCI: 1.0x (kept at baseline)
  └─ Williams %R: 1.0x (kept at baseline)
  
  VOLUME & VOLATILITY:
  ├─ OBV: 1.0x (volume confirmation)
  ├─ CMF: 1.0x (money flow direction)
  ├─ Bollinger Bands: 1.0x (volatility context)
  └─ ATR: 1.0x (position sizing based on volatility)
\`\`\`

**Strategy Characteristics:**
- ✅ Excels in: Strong trending markets (up or down)
- ✅ Wider stops: ${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}% - Avoids getting shaken out of trend
- ✅ Higher R:R: ${(Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}'))).toFixed(1)}:1 (Minimum 3:1 target for trend trades)
- ⚠️ Weakness: Choppy/sideways markets cause whipsaws
- ⚠️ Entry timing: Often enters after trend has begun (misses early move)
- ⚠️ Reversal risk: Can hold too long if trend breaks unexpectedly

---

## ⚠️ CRITICAL CONTEXT: SELL TRADE CONSIDERATIONS

**This is a SHORT/SELL position. Special risks apply:**
\`\`\`
SELL Trade Risks vs BUY Trade:
├─ Unlimited upside risk (stop loss is CRITICAL - NEVER widen it)
├─ Lower circuit limits upside, but you're on wrong side
├─ Short squeeze risk if unexpected positive news
├─ Borrowing costs (if actual short vs just avoiding long)
├─ Sentiment bias: Markets have long-term upward drift
└─ Psychological difficulty: Harder to profit from others' pain

For Indian markets specifically:
├─ T+1 settlement makes intraday short selling complex
├─ Delivery-based short selling requires stock borrowing
├─ Most retail traders can only "avoid buying" not "short"
├─ Limited stocks have F&O (futures & options) for shorting
└─ SEBI restrictions on naked short selling

**Recommended Interpretation:**
IF you own {stockName}:
   → Analysis helps decide: HOLD vs SELL existing position
   → Focus on: "Should I exit my holdings now?"

IF you don't own {stockName}:
   → Analysis helps decide: AVOID or SHORT via Derivatives
   → Focus on: "Is this worth shorting, and how?"

IF shorting via derivatives:
   → Ensure liquidity in F&O segment (check separately)
   → Understand margin requirements and mark-to-market
   → Options (Put buying) limits risk vs Futures short
\`\`\`

---

## 🎯 ANALYSIS OBJECTIVE

**Core Question:**
"Is the detected downtrend strong enough, backed by fundamentals/catalysts, and likely to continue to ₹{target}?"

**Critical Success Factors for SELL Trend:**
1. **Catalyst:** What negative news/event is driving the fall? (MOST IMPORTANT)
2. **Fundamentals:** Are deteriorating metrics justifying lower prices?
3. **Smart Money:** Are institutions exiting? Is delivery % falling?
4. **Sector Weakness:** Is the sector dragging {stockName} down?
5. **Trend Health:** Is momentum accelerating or decelerating?
6. **Reversal Risk:** Any upcoming positive catalysts that could reverse trend?

${Math.abs(parseFloat('{score}')) < 0.30 ? `
⚠️ **SPECIAL ALERT: WEAK SELL SIGNAL**

Score {score} is BARELY bearish. For SELL trades, this is VERY risky:
- Need EXCEPTIONAL catalysts and deterioration to justify
- Reversal probability is HIGH (>50%)
- Default stance: SKIP unless overwhelming evidence

Weak SELL signals have 60-70% failure rate in backtests.
Proceed ONLY if analysis reveals strong fundamental reasons.
` : Math.abs(parseFloat('{score}')) < 0.50 ? `
**Moderate SELL Signal Alert:**

Score {score} shows moderate downtrend. This requires:
- Clear catalysts (not just "falling because falling")
- Fundamental confirmation (margins/growth deteriorating)
- Smart money exit (FII/DII selling)

Without these, risk of reversal is 40-50%.
` : `
**Strong SELL Signal:**

Score {score} indicates strong downtrend conviction.
Technical setup is solid. Now validate:
- Sustainability (will trend continue to target?)
- Risk management (stop loss placement critical)
- Catalyst strength (what's driving this down?)
`}

**Your Mission:**
Perform forensic analysis to determine if this {score} score represents:
- 🟢 **Confirmed Downtrend:** Clear catalysts + weak fundamentals + institutional exit → EXECUTE SELL
- 🟡 **Questionable Downtrend:** Mixed signals, risky to bet on continuation → CAUTION
- 🔴 **False Breakdown:** Technical dip without substance, reversal likely → SKIP SELL

---

## 📋 PRE-ANALYSIS DATA CHECKLIST

**Required Data Sources:**
- [ ] Current stock price (within 24 hours)
- [ ] Recent negative news (past 7-14 days) - **CRITICAL for SELL**
- [ ] Latest financial results (check for deterioration)
- [ ] FII/DII selling data (smart money exit?)
- [ ] Sector performance (is sector weak?)
- [ ] Delivery percentage trend (falling = weak holders)
- [ ] Short interest data (if available via F&O)
- [ ] Volume patterns during downmove

**{stockName}-Specific Red Flags to Check:**
- [ ] Earnings miss or guidance cut
- [ ] Promoter selling/pledge increase  
- [ ] Regulatory penalties (sector-specific)
- [ ] Customer loss or order cancellation
- [ ] Quality issues/product recalls
- [ ] Margin compression
- [ ] Debt covenant breach
- [ ] Credit rating downgrade

**Data Quality Requirement:**
\`\`\`
For SELL signals, data quality is MORE critical than BUY:
- Need confirmation of negative catalysts (can't short on hope)
- Must verify smart money exit (institutions selling)
- Require sector context (isolated weakness vs sector-wide)
- Historical volatility (can stop loss withstand normal swings?)

If <70% data available → Reduce confidence significantly
If <50% data available → Consider skipping trade entirely
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
├─ Circuit limits can trap you in losing position
└─ Squeeze risk: Low float + short interest = explosive upside

SELL trades require HIGHER liquidity than BUY trades
Minimum: ₹1 Cr daily value (vs ₹50L for BUY trades)
\`\`\`

### Search Strategy:
\`\`\`
Query 1: "{stockName} NSE volume {date}"
Query 2: "{ticker} average daily value traded"
Query 3: "{stockName} delivery percentage trend"
Query 4: "{stockName} bid ask spread liquidity"
Query 5: "{stockName} circuit breaker hits upper lower"
Query 6: "{stockName} futures options F&O liquidity"
Query 7: "{stockName} free float market cap"
\`\`\`

### Analysis Tasks:

#### 1. Cash Market Liquidity:
\`\`\`
| Metric | Value | Benchmark for SELL | Status |
|--------|-------|-------------------|---------|
| Avg Daily Value (20D) | ₹[X] Lakhs/Cr | >₹1 Cr (REQUIRED) | [✅/⚠️/❌] |
| Avg Daily Volume | [X] shares | >100,000 shares preferred | [✅/⚠️/❌] |
| Delivery % (20D avg) | [X]% | >50% for safety | [✅/⚠️/❌] |
| Bid-Ask Spread | [X]% | <0.5% (tight) CRITICAL | [✅/⚠️/❌] |
| Free Float Mcap | ₹[X] Cr | >₹200 Cr preferred | [✅/⚠️/❌] |
| Price Volatility | [X]% avg daily | <5% manageable | [✅/⚠️/❌] |

**Delivery % Trend (Last 10 Days):**
[Plot trend: Increasing/Stable/Declining]

✅ GOOD for SELL: Declining delivery % (weak hands exiting, low conviction)
🔴 BAD for SELL: Increasing delivery % (strong hands buying dip, conviction building)
\`\`\`

#### 2. Volatility & Circuit Risk:
\`\`\`
**Circuit Breaker History (Last 30 Days):**

| Date | Circuit Hit | Reason | Price Impact |
|------|-------------|--------|--------------|
| [DD-MMM] | Upper/Lower | [News/No news] | [+/-X%] |

Summary:
- Upper Circuit Hits: [X] times → 🔴 HIGH RISK for shorts (could gap against you)
- Lower Circuit Hits: [X] times → ⚪ Shows selling pressure but also high volatility
- Total Circuits: [Y] → [✅ 0 ideal / ⚠️ 1-2 manageable / 🔴 3+ too volatile]

**Intraday Volatility:**
- Average daily range: [X]%
- vs Stop Loss distance: ${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}%
- Assessment: [✅ Stop > 2× volatility / ⚠️ Stop = 1-2× / 🔴 Stop < volatility = too tight]

**Gap Risk Analysis:**
| Period | Gap Ups >3% | Gap Downs >3% | Assessment |
|--------|-------------|---------------|------------|
| Last 30 Days | [X] times | [Y] times | [Risk level] |

🔴 CRITICAL: If gap ups > gap downs → Stock prone to positive surprises, risky SELL
✅ GOOD: If gap downs > gap ups → Downtrend confirmed with momentum
\`\`\`

#### 3. Derivative Market Check (F&O Availability):
\`\`\`
**Does {stockName} have F&O segment?**
[YES / NO - Check NSE F&O stocks list]

IF YES - F&O Metrics:
| F&O Metric | Value | Status |
|------------|-------|--------|
| Futures OI (Open Interest) | [X] lots | [✅ Adequate >10K lots / ⚠️ Low <5K / ❌ Illiquid <1K] |
| Put-Call Ratio (PCR) | [X.XX] | [Bullish >1.2 / Neutral 0.8-1.2 / Bearish <0.8] |
| Put OI vs Call OI | [X] puts vs [Y] calls | [Sentiment] |
| Futures Premium/Discount | ₹[X] ([Y]%) | [Contango/Backwardation] |
| Options Spreads | [Wide/Tight] | [Liquidity assessment] |
| Rollover % (latest expiry) | [X]% | [✅ >70% healthy / ⚠️ 50-70% / 🔴 <50% weak] |

**Best Short Method (if F&O exists):**
├─ Futures Short: Direct exposure, margin-efficient, good liquidity
├─ Put Buying: Limited risk (premium), benefits from IV expansion
├─ Bear Call Spread: Lower cost but capped profit
└─ Recommendation: [Specific strategy based on OI, liquidity, volatility]

IF NO F&O:
\`\`\`
🔴 NO DERIVATIVES AVAILABLE

Short Options:
1. ❌ Cannot short via futures
2. ❌ Cannot buy puts
3. ✅ Can SELL existing holdings (if you own)
4. ❌ Cannot actively short this stock

**Implication for Analysis:**
- This becomes a "HOLD vs SELL holdings" decision, not active short
- If you don't own {stockName}, analysis is purely informational
- No way to profit from downtrend unless you own the stock
→ Recommendation: [HOLD EXISTING vs SELL / SKIP if don't own]
\`\`\`
\`\`\`

### Liquidity Decision Matrix for SELL:
\`\`\`
MANDATORY SKIP - DO NOT TRADE if ANY:
├─ Avg Daily Value <₹50 Lakhs → 🔴🔴 TOO ILLIQUID FOR SHORT
├─ Delivery % <30% consistently → 🔴🔴 MANIPULATED, AVOID SHORT  
├─ Upper circuits >3 in 30 days → 🔴🔴 TOO VOLATILE, WILL HIT STOP
├─ Bid-Ask >2% → 🔴🔴 UNACCEPTABLE SLIPPAGE
├─ No F&O + Don't own stock → ⚪ CANNOT SHORT (analysis not applicable)
└─ Recent gap ups >5% multiple times → 🔴 PRONE TO SQUEEZES

PROCEED WITH EXTREME CAUTION if ANY:
├─ Avg Daily Value ₹50L-₹1Cr → ⚠️ Micro position only (<0.5% portfolio)
├─ Delivery % 30-50% → ⚠️ Watch for short squeeze if delivery rises
├─ Circuit hits 1-2 times → ⚠️ Single position entry, quick exit plan
├─ Wide spreads 1-2% → ⚠️ Account for 1-2% slippage both ways
├─ Free float <₹50 Cr → ⚠️ Limited liquidity, easy to manipulate
└─ F&O illiquid (<5K lots OI) → ⚠️ Use cash market instead

SAFE TO SHORT if ALL:
├─ Avg Daily Value >₹1 Cr (₹2 Cr+ preferred) → ✅ Good liquidity
├─ Delivery % >50% and stable/declining → ✅ Genuine selling, not manipulation
├─ No circuit hits OR justified by major negative news → ✅ Rational price action
├─ Bid-Ask <0.5% → ✅ Efficient execution possible
├─ Active F&O segment (>10K lots OI) → ✅ Multiple exit routes available
└─ Free float >₹200 Cr → ✅ Hard to manipulate
→ Standard position sizing applicable (2-5% based on conviction)
\`\`\`

### Liquidity Verdict:

\`\`\`
**Overall Liquidity Score:** [Calculate: X/100]

Component Scores:
├─ Daily Value: [0-25 points]
├─ Delivery %: [0-20 points]
├─ Spread & Slippage: [0-20 points]
├─ Circuit History: [0-15 points]
├─ F&O Availability & Depth: [0-20 points]
└─ TOTAL: [XX/100]

**Interpretation:**
80-100: ✅✅ EXCELLENT - Safe for short selling, good liquidity
65-79: ✅ GOOD - Acceptable for SELL trades, standard sizing
50-64: ⚠️ FAIR - Proceed with caution, reduce size by 50%
35-49: 🔴 POOR - High risk, micro positions only (<1%)
0-34: 🔴🔴 UNACCEPTABLE - SKIP trade entirely, too risky

**{stockName} Liquidity Score:** [XX]/100 → [Rating]

**VERDICT:** [✅ EXECUTE / ⚠️ CAUTION / 🔴 SKIP]

**Recommended Shorting Method:**
${`
IF score >80: [Futures short OR Sell holdings - both viable]
IF score 65-79: [Sell holdings preferred OR small futures short]
IF score 50-64: [Only if holding - sell. Don't initiate new short]
IF score <50: [DO NOT SHORT. Sell holdings if must, but risky]
`}

**Position Size Limit (based on liquidity):**
- Maximum: [X]% of portfolio
- Estimated Slippage: Entry ±[Y]%, Exit ±[Z]%
- Impact Cost: [A]% for ₹[B] Lakh position

**If SKIP due to liquidity:**
🔴 STOP ANALYSIS HERE

Reason: [Primary liquidity issue]
Alternative: [Suggest more liquid stocks in same sector if applicable]
Do not proceed to other sections - liquidity risk overrides all other factors.
\`\`\`

---

## SECTION 2: NEWS & CATALYST ANALYSIS - "Why Is It Falling?"

### Priority: CRITICAL ⚠️⚠️⚠️

**Fundamental Principle for SELL Trades:**
\`\`\`
"Never short a stock just because it's falling"
"Always short a stock because there's a REASON it should fall MORE"

Without a clear catalyst, SELL trades have 60-70% failure rate.
This section is THE most important for SELL signal validation.
\`\`\`

### Search Strategy:
\`\`\`
Query 1: "{stockName} news negative {date}"
Query 2: "{stockName} latest news February 2025"
Query 3: "{stockName} earnings miss profit warning guidance"
Query 4: "{stockName} management resignation issue problem"
Query 5: "{stockName} regulatory action penalty SEBI"
Query 6: "[SECTOR] sector India headwinds challenges 2025"
Query 7: "{stockName} competitor wins market share loss"
Query 8: "{stockName} stock price fall reason today why"
Query 9: "{stockName} downgrade rating analyst"
Query 10: "{stockName} debt problem credit downgrade"
\`\`\`

### Analysis Framework:

#### 1. Catalyst Hunt - "What Started the Downtrend?"

**Check for Primary SELL Catalysts (Last 30 Days):**
\`\`\`
🔴 EARNINGS-RELATED:
- [ ] Earnings miss vs estimates (Revenue/EPS/EBITDA)
- [ ] Guidance cut / Negative outlook statement
- [ ] Margin compression disclosed
- [ ] Order book shrinkage
- [ ] Key customer loss announced

🔴 MANAGEMENT/GOVERNANCE:
- [ ] CEO/CFO/Key management sudden exit
- [ ] Promoter selling stake
- [ ] Promoter pledge increase (financial stress)
- [ ] Auditor resignation or qualification
- [ ] Related party transaction concerns

🔴 REGULATORY/LEGAL:
- [ ] SEBI show-cause notice or penalty
- [ ] Sectoral regulator action (CDSCO for medical devices, etc.)
- [ ] Major litigation filed or lost
- [ ] Product recall or quality issues
- [ ] License suspension or revocation

🔴 BUSINESS/OPERATIONAL:
- [ ] Major contract cancellation or loss
- [ ] Plant shutdown or capacity reduction
- [ ] Raw material cost spike without pricing power
- [ ] Working capital issues disclosed
- [ ] Inventory buildup / Slow moving stock

🔴 FINANCIAL STRESS:
- [ ] Debt covenant breach or risk
- [ ] Credit rating downgrade
- [ ] Delay in debt servicing
- [ ] Rights issue / Dilutive fundraising (desperation)
- [ ] Cash flow problems disclosed

🔴 COMPETITIVE/MARKET:
- [ ] Market share loss to competitors
- [ ] New competitive threat emerged
- [ ] Pricing pressure / Price war
- [ ] Technology obsolescence risk
- [ ] Customer shifting to alternatives

🔴 SECTOR/MACRO:
- [ ] Adverse policy change (tax, duty, regulation)
- [ ] Sector-wide slowdown or headwind
- [ ] Input commodity price spike
- [ ] Forex headwind (for exporters/importers)
- [ ] Demand destruction in end market
\`\`\`

**Catalyst Discovery Output:**
\`\`\`
| Catalyst Type | Date | Specific Event | Magnitude | Duration |
|---------------|------|----------------|-----------|----------|
| [PRIMARY] | [DD-MMM] | [Detailed description] | [🔴🔴 High / 🔴 Med / 🟡 Low] | [Short/Medium/Long-term] |
| [Secondary] | [DD-MMM] | [Description] | [Same] | [Same] |
| [Tertiary] | [DD-MMM] | [Description] | [Same] | [Same] |

**THE Primary Trigger:**
[Single most important reason for the fall - be specific]

Example: "Q3 FY25 earnings missed estimates by 18% (₹45 Cr vs ₹55 Cr expected) due to 340 bps margin compression from raw material inflation, with management guiding for continued pressure in Q4"

NOT acceptable: "Company reported weak results"
NOT acceptable: "General market weakness"  
NOT acceptable: "Technical breakdown" (this is circular reasoning)

**Catalyst Strength Assessment:**
🔴🔴 STRONG (Score 80-100):
   - Clear, specific, verifiable negative event
   - Significant magnitude (>10% earnings impact or >15% stock move justified)
   - Multiple catalysts reinforcing (e.g., earnings miss + guidance cut + margin compression)

🔴 MODERATE (Score 50-79):
   - Identifiable negative but not severe
   - Some uncertainty about magnitude
   - Mixed with occasional neutral/positive news

🟡 WEAK (Score 20-49):
   - Vague or minor negatives
   - Primarily sentiment-driven
   - No fundamental deterioration

⚪ ABSENT (Score 0-19):
   - Technical fall with no identifiable reason
   - "Falling because it's falling"
   → 🔴🔴 RED FLAG: Skip SELL trade

**{stockName} Catalyst Strength:** [XX]/100 → [Rating]
\`\`\`

#### 2. Catalyst Sustainability - "Will It Keep Falling?"

**Duration Analysis:**
\`\`\`
For each identified catalyst, assess sustainability:

**ONE-TIME EVENTS (1-4 weeks impact):**
Examples: Single quarter earnings miss, one-time charge, temporary issue
├─ Impact: Sharp initial fall, then stabilization
├─ Target Implication: May reach ₹{target}? [Unlikely / Possible / Likely]
└─ Recommendation: [Book profits at ₹[LEVEL] vs full target]

**MEDIUM-TERM ISSUES (1-3 months):**
Examples: Management change uncertainty, temporary margin pressure, short-term demand softness
├─ Impact: Sustained weakness for quarter or two
├─ Target Implication: ₹{target} achievable in [X] weeks
└─ Recommendation: [Hold for full target / Partial booking strategy]

**STRUCTURAL PROBLEMS (6+ months):**
Examples: Loss of key customer, competitive displacement, obsolescence, regulatory regime change
├─ Impact: Prolonged downtrend, potential for falling below target
├─ Target Implication: ₹{target} likely undershot, may go to ₹[LOWER]
└─ Recommendation: [Full target + trail stop / Consider lower targets]

**Catalyst-Specific Sustainability Assessment:**

PRIMARY CATALYST: [Description from above]
├─ Nature: [One-time / Medium-term / Structural]
├─ Reversibility: [Can be fixed quickly / Takes time / Irreversible damage]
├─ Management Commentary: [Acknowledged & fixing / Downplaying / Silent = concerning]
├─ Historical Precedent: [Similar issues in past took X months to resolve]
└─ **Sustainability Score:** [🟢 Long-lasting / 🟡 Moderate / 🔴 Short-lived]

**For ₹{entry} → ₹{target} (${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(1)}% fall):**
- Requires [X] weeks of sustained weakness
- Catalyst(s) support this duration? [✅ YES / ⚠️ PARTIALLY / ❌ NO]
\`\`\`

#### 3. Counter-Catalysts - "What Could Reverse This?"

**Positive Surprises That Could Break Downtrend:**
\`\`\`
**UPCOMING EVENTS (Next 30-60 Days) - HIGH REVERSAL RISK:**

| Event | Date | Positive Scenario | Probability | Impact on SELL |
|-------|------|-------------------|-------------|----------------|
| Q[X] FY[YY] Earnings | [DD-MMM or TBD] | Beat estimates, margin recovery | [High/Med/Low] | [🔴 Critical / 🟡 Moderate / 🟢 Low] |
| Product Launch | [DD-MMM or TBD] | Successful market entry | [High/Med/Low] | [Same] |
| Order Announcement | [Expected] | Major contract win (₹X Cr+) | [High/Med/Low] | [Same] |
| Board Meeting | [DD-MMM] | Dividend/Buyback surprise | [High/Med/Low] | [Same] |
| Regulatory Decision | [Expected] | Favorable policy/approval | [High/Med/Low] | [Same] |
| Sector Event | [DD-MMM] | PLI scheme benefit, Budget allocation | [High/Med/Low] | [Same] |

**HIGHEST RISK EVENT:** [Event name] on [Date]
**Probability of Positive Surprise:** [X]%
**Potential Price Impact if occurs:** [Gap up to ₹Y, +Z%]

**Risk Assessment:**
🔴🔴 CRITICAL REVERSAL RISK (Skip SELL):
   - High probability positive event in next 7-14 days
   - Historical pattern of positive surprises from company
   - Sector/market setup favoring bounce
   → Recommendation: SKIP this SELL trade entirely

🔴 HIGH RISK (Reduce size OR plan early exit):
   - Medium probability event in 2-4 weeks
   - Could trigger stop loss
   → Recommendation: Exit before event OR reduce to 50% size

🟡 MODERATE RISK (Monitor closely):
   - Event >4 weeks away OR low probability
   → Recommendation: Trade as planned but watch approach

🟢 LOW RISK (Clear path):
   - No major events OR events likely negative
   → Recommendation: Full target ₹{target} viable

**{stockName} Counter-Catalyst Risk:** [Rating + reasoning]
\`\`\`

**Potential Bottom Formation Signals:**
\`\`\`
Watch for these reversal indicators during trade:
├─ Promoter buying disclosed
├─ Institutional buying (FII/MF increasing stakes)
├─ Analyst upgrades or positive reports
├─ Sector showing signs of bottoming
├─ Stock forming technical base (higher lows)
├─ Delivery % suddenly jumping (conviction buying)
└─ Management buyback announcement

**Current Status:** [Any of these present? Detail]
\`\`\`

#### 4. News Flow Quality & Sentiment Timeline:

**14-Day News Sentiment Analysis:**
\`\`\`
| Week | Positive News | Neutral News | Negative News | Net Sentiment |
|------|---------------|--------------|---------------|---------------|
| Week 1 (Recent) | [X] count | [Y] count | [Z] count | [🔴🔴 Very Bearish / 🔴 Bearish / ⚪ Neutral / 🟢 Bullish] |
| Week 2 | [X] count | [Y] count | [Z] count | [Same] |

**Sentiment Progression:**
├─ Week 1 → Week 2: [Deteriorating further / Stabilizing / Improving]
├─ Pattern: [Consistently negative / Mixed / Turning positive]
└─ **Trend:** [Supports continued fall ✅ / Uncertain ⚪ / Reversal signs 🔴]

**Media Coverage Intensity:**
- Mainstream coverage: [High/Medium/Low]
- Negative tone articles: [X]% of total
- Keywords detected: [Scandal/Crisis/Problems/Headwinds/etc.]
- Social media sentiment: [If measurable - Twitter, forums]

**Sentiment Momentum:**
✅ SUPPORTS SELL: News getting progressively worse, new negatives emerging
⚪ STABLE: Negative but no new information
🔴 WARNING: Negative news flow slowing, sentiment bottoming out
\`\`\`

#### 5. Analyst & Brokerage Actions:

**Recent Analyst Activity:**
\`\`\`
| Date | Brokerage | Action | Target Price | Reasoning |
|------|-----------|--------|--------------|-----------|
| [DD-MMM] | [Name] | Downgrade/Cut | ₹[X] → ₹[Y] | [Brief reason] |

Summary (Last 30 Days):
- Downgrades: [X] instances
- Target cuts: [Y] instances
- Upgrades: [Z] instances (concerning if >0 for SELL)

**Consensus Shift:**
- Previous Avg Target: ₹[X]
- Current Avg Target: ₹[Y]  
- Change: ₹[Z] ([A]%)
- Direction: [Lowering ✅ / Stable ⚪ / Raising 🔴]

**vs Your Target:**
- Your Target: ₹{target}
- Analyst Consensus: ₹[Y]
- Your target is: [More aggressive / In-line / More conservative]

**Analyst Sentiment Score:**
✅ SUPPORTS SELL: Multiple downgrades, target cuts, negative revisions
⚪ MIXED: Some cuts but also stable ratings
🔴 CONTRADICTS: Upgrades, target raises, turning positive
\`\`\`

### Catalyst & Sentiment Verdict:

\`\`\`
**Overall Catalyst Assessment:**

| Component | Score /100 | Weight | Weighted |
|-----------|-----------|--------|----------|
| Primary Catalyst Strength | [XX] | 35% | [X.X] |
| Catalyst Sustainability | [XX] | 25% | [X.X] |
| Counter-Catalyst Risk | [XX] | 20% | [X.X] |
| News Flow Quality | [XX] | 10% | [X.X] |
| Analyst Sentiment | [XX] | 10% | [X.X] |
| **TOTAL CATALYST SCORE** | | **100%** | **[XX.X]** |

**Interpretation:**
75-100: ✅✅ STRONG CATALYSTS - High confidence in continued fall
60-74: ✅ GOOD CATALYSTS - Supports SELL trade
45-59: ⚪ MODERATE - Some concerns, reduce conviction
30-44: 🔴 WEAK - Questionable SELL thesis
0-29: 🔴🔴 ABSENT/CONTRADICTORY - Skip trade

**{stockName} Catalyst Score:** [XX.X]/100 → [Rating]

**Does Catalyst Analysis Support Riding Downtrend to ₹{target}?**
[✅ YES - Strong catalysts support full target]
[⚠️ PARTIAL - Target may be ₹[ADJUSTED] instead of ₹{target}]
[❌ NO - Weak catalysts, skip SELL trade]

**THE Key Insight (2-3 sentences):**
[Synthesize THE single most important finding about why this stock is falling and whether it's sustainable to target]

Example: "Primary catalyst is 340bps margin compression from polymer cost inflation without pricing power, disclosed in Q3 results with management guiding for 2-3 more quarters of pressure. This is structural medium-term issue (6+ months), supporting target ₹{target}. Counter-risk is potential crude oil decline or pricing power recovery, but low probability in next 2-3 months."
\`\`\`

---

## SECTION 3: FUNDAMENTAL DETERIORATION CHECK

**Why This Section Matters:**
\`\`\`
Technical downtrend + Fundamental deterioration = HIGH PROBABILITY SELL
Technical downtrend + Strong fundamentals = DANGEROUS VALUE TRAP

This section validates whether fundamentals justify lower prices.
\`\`\`

### Search Strategy:
\`\`\`
Query 1: "{stockName} quarterly results trend FY24 FY25"
Query 2: "{stockName} profit margins declining compression"
Query 3: "{stockName} debt equity ratio increased"
Query 4: "{stockName} balance sheet deterioration"
Query 5: "{stockName} cash flow problems negative"
Query 6: "{stockName} earnings quality red flags"
Query 7: "{stockName} PE ratio valuation expensive cheap"
Query 8: "{stockName} vs [PEER1] [PEER2] financial comparison"
Query 9: "{stockName} ROE ROCE declining"
Query 10: "{stockName} working capital problems"
\`\`\`

### Analysis Framework:

#### 1. Earnings Trajectory - "Is Profit Story Broken?"

\`\`\`
**Quarterly Performance Trend:**

| Quarter | Revenue (₹Cr) | YoY Δ | EBITDA (₹Cr) | PAT (₹Cr) | PAT YoY Δ | EPS (₹) | vs Est | Status |
|---------|---------------|-------|--------------|-----------|-----------|---------|--------|--------|
| Q2 FY25 | [X] | [+/-Y]% | [X] | [X] | [+/-Y]% | [X] | [Beat/Miss/In-line] | [✅/⚠️/❌] |
| Q1 FY25 | [X] | [+/-Y]% | [X] | [X] | [+/-Y]% | [X] | [Beat/Miss/In-line] | [✅/⚠️/❌] |
| Q4 FY24 | [X] | [+/-Y]% | [X] | [X] | [+/-Y]% | [X] | [Beat/Miss/In-line] | [✅/⚠️/❌] |
| Q3 FY24 | [X] | [+/-Y]% | [X] | [X] | [+/-Y]% | [X] | [Beat/Miss/In-line] | [✅/⚠️/❌] |

**4-Quarter Trend Analysis:**
- Revenue: [🟢 Growing / ⚪ Flat / 🔴 Declining]
  └─ Growth Rate: [Accelerating / Stable / Decelerating]
- Profit (PAT): [🟢 Growing / ⚪ Flat / 🔴 Declining]  
  └─ Growth Rate: [Accelerating / Stable / Decelerating]
- EPS: [🟢 Improving / ⚪ Stable / 🔴 Deteriorating]
  └─ Dilution Impact: [None / Moderate / Significant]

**Earnings vs Price Alignment:**
✅ SUPPORTS SELL:
   - Price falling + Earnings falling → Perfect alignment
   - Price falling faster than earnings → Room to fall more
   - Consecutive earnings misses vs estimates → Broken story

⚪ NEUTRAL:
   - Price falling + Earnings flat → Some justification
   
🔴 VALUE TRAP WARNING:
   - Price falling + Earnings growing → Disconnect
   - Price falling + Earnings beat → Opportunity, not SELL
   → Risky to short when fundamentals improving

**{stockName} Earnings-Price Alignment:** [Rating]
\`\`\`

#### 2. Margin Compression - "Profitability Under Pressure?"

\`\`\`
**Margin Trend (Last 4 Quarters):**

| Metric | Q2 FY25 | Q1 FY25 | Q4 FY24 | Q3 FY24 | Trend | Change | Bearish? |
|--------|---------|---------|---------|---------|-------|--------|----------|
| Gross Margin % | [X]% | [Y]% | [Z]% | [A]% | [↑/↓/→] | [+/-B] bps | [✅/❌] |
| EBITDA Margin % | [X]% | [Y]% | [Z]% | [A]% | [↑/↓/→] | [+/-B] bps | [✅/❌] |
| Operating Margin % | [X]% | [Y]% | [Z]% | [A]% | [↑/↓/→] | [+/-B] bps | [✅/❌] |
| Net Margin % | [X]% | [Y]% | [Z]% | [A]% | [↑/↓/→] | [+/-B] bps | [✅/❌] |

**Margin Pressure Drivers:**
Root Cause Analysis:
├─ Raw Material Costs: [Rising/Stable/Falling] - Impact: [High/Med/Low]
├─ Operating Leverage: [Negative/Neutral/Positive] - Fixed costs vs volume
├─ Pricing Power: [Weak/Moderate/Strong] - Can pass on costs?
├─ Competition: [Intensifying/Stable/Easing] - Price wars?
├─ Product Mix: [Shifting to low-margin/Stable/Improving]
└─ Other: [Forex, Energy, Labor costs]

**Primary Cause:** [Specific driver with data]

**Management Commentary on Margins:**
- Acknowledged issue? [Yes/No - quote from con-call]
- Action plan disclosed? [Cost cuts/Price hikes/Mix improvement]
- Guidance provided? [Margins to improve/stabilize/compress further]
- Credibility: [Track record of delivery on guidance]

**Recovery Probability:**
🔴 LOW (Structural):
   - Competitive intensity increasing permanently
   - Input costs structurally higher (new normal)
   - Lost pricing power, cannot recover
   → SELL thesis strengthened

⚪ MEDIUM (Cyclical):
   - Temporary cost spike (commodity cycle)
   - Will recover in 2-3 quarters
   → Moderate SELL case

🟢 HIGH (One-time):
   - Specific one-time factor
   - Already reversing
   → Weak SELL case, value trap risk

**{stockName} Margin Assessment:**
- Compression Magnitude: [X] bps over 4 quarters
- Primary Cause: [Structural/Cyclical/One-time]
- Recovery Outlook: [Low/Medium/High]
- **Verdict:** [🔴 Margins compressing = Strong SELL signal / ⚪ Stable / 🟢 Expanding = Contradicts SELL]
\`\`\`

#### 3. Debt & Leverage - "Financial Stress Building?"

\`\`\`
**Debt Trend Analysis:**

| Metric | Latest | 1Q Ago | 2Q Ago | 4Q Ago | Trend | Risk Level |
|--------|--------|--------|--------|--------|-------|------------|
| Total Debt (₹Cr) | [X] | [Y] | [Z] | [A] | [↑/↓/→] | [Assessment] |
| Debt/Equity (x) | [X.X] | [Y.Y] | [Z.Z] | [A.A] | [↑/↓/→] | [✅ <1 / ⚠️ 1-2 / 🔴 >2] |
| Net Debt (₹Cr) | [X] | [Y] | [Z] | [A] | [↑/↓/→] | [vs Cash] |
| Net Debt/EBITDA (x) | [X.X] | [Y.Y] | [Z.Z] | [A.A] | [↑/↓/→] | [✅ <2 / ⚠️ 2-4 / 🔴 >4] |
| Interest Coverage (x) | [X.X] | [Y.Y] | [Z.Z] | [A.A] | [↑/↓/→] | [✅ >3 / ⚠️ 2-3 / 🔴 <2] |
| Cash & Equiv (₹Cr) | [X] | [Y] | [Z] | [A] | [↑/↓/→] | [Liquidity] |

**Red Flag Checks:**
🔴🔴 SEVERE STRESS (Strong SELL Signal):
- [ ] Debt increasing while revenue/profit declining (death spiral)
- [ ] Interest coverage <2x (struggling to pay interest)
- [ ] Debt/Equity >3x (overleveraged)
- [ ] Cash declining rapidly (<₹X Cr, burn rate concerning)
- [ ] Covenant breach disclosed or imminent
- [ ] Refinancing difficulties mentioned

🔴 MODERATE STRESS:
- [ ] Debt/Equity 2-3x (elevated leverage)
- [ ] Interest coverage 2-3x (manageable but tight)
- [ ] Working capital financing increasing
- [ ] No debt reduction despite profits

⚪ ACCEPTABLE:
- [ ] Debt/Equity <1x
- [ ] Interest coverage >3x  
- [ ] Stable debt levels
- [ ] Adequate cash buffers

**Debt-Related Catalysts:**
- Credit Rating: [Current rating - any recent changes?]
  └─ Downgrade? [Yes - 🔴 / No - ✅]
- Upcoming Refinancing: [Any large debt maturity in 6-12 months?]
  └─ Risk: [High/Medium/Low]
- Interest Rate Sensitivity: [Impact of rates rising by 50-100 bps]
  └─ Vulnerability: [High/Medium/Low]

**{stockName} Financial Stress Assessment:**
- Debt Trend: [Concerning 🔴 / Stable ⚪ / Improving 🟢]
- **Stress Score:** [High 🔴 / Medium ⚪ / Low ✅]
- **Impact on SELL thesis:** [Strengthens / Neutral / Weakens]
\`\`\`

#### 4. Earnings Quality - "Is Profit Real or Accounting Gimmick?"

\`\`\`
**Cash Flow Reality Check:**

| Metric | FY24 | FY23 | FY22 | Trend | Quality |
|--------|------|------|------|-------|---------|
| Operating Cash Flow (₹Cr) | [X] | [Y] | [Z] | [↑/↓/→] | [Assessment] |
| Net Profit (PAT) (₹Cr) | [X] | [Y] | [Z] | [↑/↓/→] | [Assessment] |
| OCF/PAT Ratio | [X.XX] | [Y.YY] | [Z.ZZ] | [↑/↓/→] | [✅ >1.0 / ⚠️ 0.7-1.0 / 🔴 <0.7] |
| Free Cash Flow (₹Cr) | [X] | [Y] | [Z] | [↑/↓/→] | [Positive/Negative] |
| Capex (₹Cr) | [X] | [Y] | [Z] | [↑/↓/→] | [Growth/Maintenance] |

**Working Capital Efficiency:**
| Metric | Latest | 1Y Ago | Change | Interpretation |
|--------|--------|--------|--------|----------------|
| Receivables Days | [X] | [Y] | [+/-Z] | [↑ 🔴 Customers delaying / ↓ ✅ Improving / → ⚪ Stable] |
| Inventory Days | [X] | [Y] | [+/-Z] | [↑ 🔴 Slow-moving stock / ↓ ✅ Efficient / → ⚪ Stable] |
| Payables Days | [X] | [Y] | [+/-Z] | [↑ Stretching suppliers / ↓ / → ] |
| Cash Conversion Cycle | [X] days | [Y] days | [+/-Z] | [↑ 🔴 Worsening / ↓ ✅ Improving] |

**Quality Red Flags:**
🔴🔴 CRITICAL (Strong SELL Signal):
- [ ] OCF/PAT <0.7 consistently (profit not converting to cash)
- [ ] Negative free cash flow for 2+ years (burning cash)
- [ ] Receivables days increasing sharply (collection issues)
- [ ] Inventory days increasing (demand weakness, obsolescence)
- [ ] Frequent accounting policy changes (manipulation?)
- [ ] Contingent liabilities >50% of net worth

🔴 CONCERNING:
- [ ] OCF/PAT 0.7-0.9 (suboptimal conversion)
- [ ] Working capital days deteriorating
- [ ] Other income >20% of PAT (profit from non-core)
- [ ] Exceptional items every quarter (not so exceptional)

✅ HEALTHY:
- [ ] OCF/PAT >1.1 (excellent cash generation)
- [ ] Working capital improving
- [ ] Clean accounting, no red flags

**{stockName} Earnings Quality:**
- OCF/PAT Ratio: [X.XX] → [Excellent/Good/Poor]
- Working Capital: [Improving/Stable/Deteriorating]
- Red Flags: [X] found → [None ✅ / Minor ⚪ / Major 🔴]
- **Quality Score:** [High ✅ / Medium ⚪ / Low 🔴]
- **SELL Implication:** [Quality issues strengthen SELL / Neutral / Quality contradicts SELL]
\`\`\`

#### 5. Valuation - "Has Stock Become Cheap Enough to Attract Value Buyers?"

\`\`\`
**Valuation Metrics Evolution:**

| Metric | Current (at ₹{entry}) | 6M Ago | 1Y Ago | Historical 3Y Avg | Status |
|--------|----------------------|--------|--------|-------------------|--------|
| P/E (TTM) | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [vs history] |
| P/E (Forward) | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [Same] |
| P/B Ratio | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [Same] |
| EV/EBITDA | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [Same] |
| EV/Sales | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [Same] |
| Dividend Yield | [X.X]% | [Y.Y]% | [Z.Z]% | [A.A]% | [vs yield alternatives] |

**Valuation Trend:** [Falling / Stable / Rising]
**Reason:** [Multiple contraction / Earnings contraction / Both]

**Critical Valuation Questions:**

AT ₹{entry} (Current Entry):
- P/E: [X.X]x → [✅ Reasonable / ⚪ Fair / 🔴 Still expensive]
- vs Historical low P/E: [Y.Y]x → Current is [Z]% [above/below] trough
- Assessment: [More room to fall / Approaching value zone / Already at value levels]

AT ₹{target} (SELL Target):
- Implied P/E: [X.X]x (assuming current earnings)
- vs Historical low: [Comparison]
- Assessment: [✅ Reasonable target / ⚠️ Aggressive / 🔴 Unlikely to reach]

**Value Trap Risk Assessment:**
🔴 HIGH RISK (Avoid SELL):
   - Stock already at historical low valuations (P/E <10x, P/B <1x)
   - Dividend yield >5% (attractive for income investors)
   - Trading below book value with no debt
   → Value buyers likely to emerge, support price

⚪ MODERATE:
   - Valuations in mid-range
   - Some support but not extreme

✅ LOW RISK (Safe to SELL):
   - Still trading at premium to historical average
   - Valuation de-rating has room to run
   - Even at ₹{target}, would be at reasonable valuations

**Sector Valuation Comparison:**
| Metric | {stockName} (₹{entry}) | Sector Median | Premium/Discount |
|--------|------------------------|---------------|------------------|
| P/E | [X.X]x | [Y.Y]x | [+/-Z]% |
| P/B | [X.X]x | [Y.Y]x | [+/-Z]% |
| EV/EBITDA | [X.X]x | [Y.Y]x | [+/-Z]% |

**Relative Valuation:**
- Trading at [premium/discount] to sector
- Justified by: [Superior/Inferior] [quality/growth/margins]
- At ₹{target}: Would trade at [X]% [discount/premium] to sector
- Assessment: [Still overvalued / Fairly valued / Undervalued]

**{stockName} Valuation Verdict:**
- Current Level (₹{entry}): [Still expensive / Fair / Cheap]
- Target Level (₹{target}): [Reasonable / Aggressive / Too low]
- Value Trap Risk: [🔴 High / ⚪ Medium / ✅ Low]
- **Support for SELL:** [✅ Yes, room to fall / ⚠️ Limited / ❌ No, already cheap]
\`\`\`

#### 6. Peer Comparison - "Relative Weakness Confirmation"

\`\`\`
**Identify Comparable Peers:**
Peer 1: [Company Name] ([TICKER])
Peer 2: [Company Name] ([TICKER])
Peer 3: [Company Name] ([TICKER])

**Comparative Fundamental Analysis:**

| Metric | {stockName} | Peer 1 | Peer 2 | Peer 3 | Rank | Relative Position |
|--------|-------------|--------|--------|--------|------|-------------------|
| Mkt Cap (₹Cr) | [X] | [Y] | [Z] | [A] | [1-4] | [Size context] |
| Rev Growth (4Q avg) | [X]% | [Y]% | [Z]% | [A]% | [1-4] | [Leader/Laggard] |
| PAT Growth (4Q avg) | [X]% | [Y]% | [Z]% | [A]% | [1-4] | [Same] |
| EBITDA Margin | [X]% | [Y]% | [Z]% | [A]% | [1-4] | [Efficiency] |
| ROE | [X]% | [Y]% | [Z]% | [A]% | [1-4] | [Returns] |
| ROCE | [X]% | [Y]% | [Z]% | [A]% | [1-4] | [Returns] |
| Debt/Equity | [X.X] | [Y.Y] | [Z.Z] | [A.A] | [1-4] | [Leverage] |
| P/E Ratio | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [1-4] | [Valuation] |
| Price Performance (3M) | [-X]% | [+/-Y]% | [+/-Z]% | [+/-A]% | [1-4] | [Momentum] |

**Relative Standing:**
- Overall Rank: [1st/2nd/3rd/4th] among 4 companies
- Classification: [LEADER / MID-TIER / LAGGARD]

✅ SUPPORTS SELL:
   - {stockName} ranks 3rd or 4th (weakest in peer group)
   - Underperforming on most metrics (growth, margins, returns)
   - Falling more than peers (stock-specific weakness)
   → Justified underperformance, room to fall more

⚪ NEUTRAL:
   - Mid-pack performer
   - Falling in-line with peers

🔴 CONTRADICTS SELL:
   - {stockName} ranks 1st or 2nd (leader)
   - Outperforming peers fundamentally
   - But falling more than peers → Oversold, value opportunity

**Key Differentiators:**
What makes {stockName} weaker than peers:
1. [Specific weakness - e.g., "Lower margins by 300 bps"]
2. [Another - e.g., "Higher debt at 1.8x vs peer avg 0.9x"]
3. [Third - e.g., "Market share declining while peers gaining"]

**{stockName} Peer Position:**
- Relative Strength: [Weak 🔴 / In-line ⚪ / Strong 🟢]
- **SELL Justification:** [Underperformance justified / Not justified]
\`\`\`

### Fundamental Deterioration Verdict:

\`\`\`
**Overall Fundamental Health Score:**

| Dimension | Assessment | Score /100 | Weight | Weighted |
|-----------|-----------|-----------|--------|----------|
| Earnings Trajectory | [Growing/Flat/Declining] | [XX] | 25% | [X.X] |
| Margin Trend | [Expanding/Stable/Compressing] | [XX] | 20% | [X.X] |
| Debt & Leverage | [Improving/Stable/Stressed] | [XX] | 20% | [X.X] |
| Earnings Quality | [High/Medium/Low] | [XX] | 15% | [X.X] |
| Valuation | [Expensive/Fair/Cheap] | [XX] | 10% | [X.X] |
| Peer Comparison | [Leader/Mid/Laggard] | [XX] | 10% | [X.X] |
| **TOTAL FUNDAMENTAL SCORE** | | | **100%** | **[XX.X]** |

**INVERT THE SCORE (for SELL trades):**
- High Score (70-100) = Strong Fundamentals = 🔴 CONTRADICTS SELL
- Medium Score (40-69) = Moderate Fundamentals = ⚪ NEUTRAL
- Low Score (0-39) = Weak Fundamentals = ✅ SUPPORTS SELL

**For SELL Trade Assessment:**
100 - [XX.X] = **[YY.Y] Deterioration Score**

**Deterioration Score Interpretation:**
75-100: ✅✅ SEVERE DETERIORATION - Fundamentals justify much lower prices
60-74: ✅ SIGNIFICANT DETERIORATION - Supports SELL to target
40-59: ⚪ MODERATE DETERIORATION - Some justification but not strong
25-39: 🔴 MILD DETERIORATION - Weak SELL case
0-24: 🔴🔴 NO DETERIORATION - Value trap, avoid SELL

**{stockName} Deterioration Score:** [YY.Y]/100 → [Rating]

**Risk of Fundamental-Driven Reversal Before ₹{target}:**
[🟢 LOW / 🟡 MEDIUM / 🔴 HIGH]

**Key Finding (3-4 sentences):**
[Synthesize whether fundamentals justify continued fall to ₹{target}, or if stock is approaching value zone where buyers will emerge. Be specific about deterioration drivers and sustainability.]

**Example:**
"Fundamentals show clear deterioration: Revenue growth decelerated from 18% to 6%, EBITDA margins compressed 340 bps due to input cost inflation, and debt increased by ₹45 Cr while profits fell. OCF/PAT ratio at 0.68 indicates earnings quality concerns. However, at ₹{entry}, P/E of X.Xx is already 25% below 3-year average, suggesting limited further multiple compression. Target ₹{target} implies P/E of Y.Yy, which is at historical trough levels - value buyers may emerge before reaching target."
\`\`\`

---

## SECTION 4: SMART MONEY FLOW - "Who's Selling & Why?"

**Fundamental Principle:**
\`\`\`
"Follow the smart money" - Institutions sell before retail realizes problems

For SELL trades, institutional exit is CRITICAL confirmation:
- If FII/DII selling: Validates downtrend
- If FII/DII buying: 🔴 RED FLAG - They see value you don't
\`\`\`

### Search Strategy:
\`\`\`
Query 1: "{stockName} FII DII selling shareholding pattern latest"
Query 2: "{stockName} promoter holding {date}"
Query 3: "{stockName} mutual fund exit holdings reduced"
Query 4: "{stockName} bulk deals selling block deals {date}"
Query 5: "{stockName} delivery percentage declining trend"
Query 6: "{stockName} insider selling director selling"
Query 7: "{stockName} institutional investors selling list"
Query 8: "{ticker} short interest data futures"
\`\`\`

### Analysis Framework:

#### 1. Institutional Exodus Check - "Are Smart Investors Running?"

\`\`\`
**Quarterly Shareholding Pattern:**

| Category | Q3 FY25 | Q2 FY25 | Q1 FY25 | Q4 FY24 | QoQ Δ | 4Q Trend | Signal |
|----------|---------|---------|---------|---------|-------|----------|--------|
| FII Holding % | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [+/-B.BB]% | [↑/↓/→] | [Assess] |
| DII Holding % | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [+/-B.BB]% | [↑/↓/→] | [Assess] |
| Mutual Funds % | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [+/-B.BB]% | [↑/↓/→] | [Assess] |
| Insurance % | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [+/-B.BB]% | [↑/↓/→] | [Assess] |
| Total Institutional | [XX.XX]% | [YY.YY]% | [ZZ.ZZ]% | [AA.AA]% | [+/-BB.BB]% | [↑/↓/→] | [Assess] |

**Institutional Flow Signals:**

✅✅ STRONG SELL CONFIRMATION:
   - FII reduced stake by >1.5% QoQ (major exit)
   - DII also selling (not offsetting FII)
   - Multiple MF exits (consensus negative)
   - Total institutional down >2% in 2 quarters

✅ SELL CONFIRMATION:
   - FII reduced 0.5-1.5% QoQ
   - DII stable or slight selling
   - Some MF exits

⚪ MIXED SIGNALS:
   - FII selling but DII buying (offsetting)
   - Marginal changes (<0.5%)
   - Some exits, some entries

🔴 CONTRADICTS SELL:
   - FII increasing stake (seeing value)
   - DII/MF both buying
   - New institutional entry
   → Value trap warning, institutions buying dip

🔴🔴 STRONG CONTRADICTION:
   - FII+DII both increasing >1%
   - Multiple new MF entries
   - HNI/Institutional buying spike
   → SKIP SELL - smart money disagrees with you

**Magnitude Analysis:**
Total Institutional Stake Change (2 Quarters):
- Absolute: [+/-X]%
- In shares: [Y] lakh shares sold/bought
- In value: ₹[Z] Cr sold/bought

**Intensity:** [Marginal / Moderate / Significant / Massive]

**{stockName} Institutional Signal:**
- FII: [🔴 Selling / ⚪ Neutral / 🟢 Buying]
- DII: [🔴 Selling / ⚪ Neutral / 🟢 Buying]
- Overall: [✅ Confirms SELL / ⚪ Mixed / 🔴 Contradicts SELL]
\`\`\`

**Specific Institutional Movements:**
\`\`\`
**Mutual Funds - Complete Exits (Red Flag):**
Funds that EXITED completely in recent quarter(s):
1. [Fund Name] - Was [X.XX]% (₹Y Cr), Now 0% - Quarter: [QX FYXX]
2. [Fund Name] - Was [X.XX]% (₹Y Cr), Now 0% - Quarter: [QX FYXX]

**Interpretation:**
- [X] funds exited completely → [Minor concern / Significant exodus / Mass exit]

**Mutual Funds - Significant Reductions:**
Funds that CUT stake by >25% of their holding:
1. [Fund Name] - [X.XX]% → [Y.YY]% (reduced [Z]%)
2. [Fund Name] - [X.XX]% → [Y.YY]% (reduced [Z]%)

**Mutual Funds - Still Holding (Contrarian View?):**
Largest MF holders remaining:
1. [Fund Name] - [X.XX]% ([Increased/Stable/Reduced marginally])
2. [Fund Name] - [X.XX]% ([Same])

**Analysis:**
- If major funds still holding with conviction → ⚪ Not everyone bearish
- If only small funds holding → ✅ Big players have exited

**Foreign Institutional Investors:**
Notable FII movements (if identifiable):
- [FII Name]: [Bought/Sold] [X] shares worth ₹[Y] Cr
- Trend: [Systematic exit / Opportunistic / Entry]
\`\`\`

#### 2. Promoter Behavior - "Are Insiders Losing Faith?"

\`\`\`
**Promoter Holding Trend:**

| Metric | Q3 FY25 | Q2 FY25 | Q1 FY25 | Q4 FY24 | Change (2Q) | Signal |
|--------|---------|---------|---------|---------|-------------|--------|
| Promoter % | [XX.XX]% | [YY.YY]% | [ZZ.ZZ]% | [AA.AA]% | [+/-BB.BB]% | [Assess] |
| Pledged Shares % | [XX.XX]% | [YY.YY]% | [ZZ.ZZ]% | [AA.AA]% | [+/-BB.BB]% | [Assess] |
| Promoter Group % | [XX.XX]% | [YY.YY]% | [ZZ.ZZ]% | [AA.AA]% | [+/-BB.BB]% | [Assess] |

**Critical Red Flags for SELL:**

🔴🔴 SEVERE (Strong SELL Signal):
   - [ ] Promoter selling stake during downtrend
     └─ Magnitude: [X]% sold = ₹[Y] Cr value
     └─ Reason disclosed: [Personal/Undisclosed]  
     └─ **Interpretation: Insider selling into weakness = NO confidence in recovery**
   
   - [ ] Pledge increasing sharply
     └─ Current pledge: [X]% of promoter holding
     └─ Increased by: [Y]% in last quarter
     └─ **Interpretation: Financial stress, margin call risk, forced selling ahead**
   
   - [ ] Promoter holding fallen below critical levels
     └─ Current: [X]% (vs [Y]% a year ago)
     └─ Risk: Loss of control if falls below 26%/51%

🔴 MODERATE RED FLAGS:
   - [ ] Promoter holding declining gradually
   - [ ] Pledge 50-75% (elevated but not critical)
   - [ ] No open market purchases despite fall

⚪ NEUTRAL:
   - [ ] Promoter holding stable
   - [ ] Pledge stable or decreasing
   - [ ] No unusual activity

🟢 CONTRADICTS SELL (Insider Confidence):
   - [ ] Promoter buying more shares during fall (signaling bottom)
   - [ ] Pledge decreasing (reducing stress)
   - [ ] Promoter holding increasing
   → **If promoter buying aggressively: 🔴 SKIP SELL - Insider sees value**

**Promoter Quality Assessment:**
- Track Record: [Clean / Some concerns / Poor governance history]
- Related Party Transactions: [Minimal <5% revenue / Moderate 5-15% / High >15%]
- Corporate Governance: [Strong / Average / Weak]

**{stockName} Promoter Signal:**
- Holding Trend: [🔴 Declining / ⚪ Stable / 🟢 Increasing]
- Pledge Status: [🔴 High/Rising / ⚪ Moderate / ✅ Low/Falling]
- **Overall:** [✅ Confirms SELL / ⚪ Neutral / 🔴 Contradicts SELL]
\`\`\`

#### 3. Insider Transactions (Director-Level):

\`\`\`
**Director/Key Management Transactions (Last 90 Days):**

| Date | Insider | Designation | Action | Shares | Price (₹) | Value (₹L) | Context |
|------|---------|-------------|--------|--------|-----------|------------|---------|
| [DD-MMM] | [Name] | [CMD/MD/CFO/Dir] | Sold | [X] | [Y] | [Z] | [Personal/Exit/Disclosed reason] |

**Summary:**
- Total Insider Sales: ₹[X] Lakhs ([Y] transactions by [Z] insiders)
- Total Insider Buys: ₹[A] Lakhs ([B] transactions)
- Net: [Heavy Selling / Balanced / Net Buying]

**Insider Selling Context:**
✅ SUPPORTS SELL:
   - Multiple insiders selling during downtrend
   - Large quantities relative to their holdings (>10%)
   - Undisclosed reasons or vague "personal reasons"
   - Pattern: Consistent selling, no buying
   → Insiders lack confidence in recovery

🔴 CONTRADICTS SELL:
   - Insider buying during fall (seeing value)
   - Director purchases disclosed prominently
   - Key management acquiring stake
   → Skip SELL - insiders disagree

**Specific Concerns:**
- CEO/CFO selling? [Yes/No - very bearish if yes]
- Founder selling? [Yes/No - especially concerning]
- Independent directors selling? [Unusual, governance concern]

**{stockName} Insider Signal:**
- Pattern: [🔴 Systematic selling / ⚪ Minimal activity / 🟢 Buying on dip]
- Magnitude: [Small / Moderate / Large]
- **Assessment:** [Confirms SELL / Neutral / Contradicts SELL]
\`\`\`

#### 4. Volume, Delivery & Retail vs Institution:

\`\`\`
**Volume Analysis During Downtrend:**

| Period | Avg Volume (Shares) | vs 3M Avg | Delivery % | Interpretation |
|--------|-------------------|-----------|------------|----------------|
| Last 5 Days | [X] | [+/-Y]% | [Z]% | [Assessment] |
| Last 10 Days | [X] | [+/-Y]% | [Z]% | [Assessment] |
| Last 20 Days | [X] | [+/-Y]% | [Z]% | [Assessment] |

**Delivery % Trend (Daily):**
[Plot Last 10 Days: D1: X%, D2: Y%, D3: Z%...]

Trend: [↑ Increasing / → Stable / ↓ Declining]

✅ HEALTHY SELL CONFIRMATION:
   - Volume INCREASING as price falls (distribution, not exhaustion)
   - Delivery % DECLINING (weak hands panic selling, low conviction)
     └─ From [X]% to [Y]% over 10 days
   - High volume on down days, low volume on up days
   → Confirms seller dominance, downtrend healthy

⚪ MIXED:
   - Volume steady
   - Delivery % unchanged
   → Normal downtrend, no strong signal

🔴 WARNING - Potential Reversal:
   - Volume DECLINING on down days (exhaustion, sellers drying up)
   - Delivery % INCREASING (conviction buyers accumulating dip)
     └─ From [X]% to [Y]% - strong hands entering
   - High volume on up days (accumulation)
   → Downtrend losing momentum, reversal risk HIGH

**{stockName} Volume Pattern:**
- During Fall: [Healthy distribution ✅ / Mixed ⚪ / Exhaustion signs 🔴]
- Delivery Trend: [Declining ✅ / Stable ⚪ / Rising 🔴]
- **Signal:** [Confirms continued fall / Uncertain / Reversal warning]
\`\`\`

#### 5. Bulk & Block Deals:

\`\`\`
**Large Transactions (Last 30 Days):**

| Date | Client Name | Type | Buy/Sell | Quantity | Price (₹) | Value (₹L) | % of Eq |
|------|-------------|------|----------|----------|-----------|------------|---------|
| [DD-MMM] | [Buyer/Seller Name] | Bulk/Block | Sell | [X] | [Y] | [Z] | [A]% |

**Summary:**
- Total Bulk/Block SELLS: ₹[X] Lakhs ([Y] instances)
- Total Bulk/Block BUYS: ₹[Z] Lakhs ([A] instances)
- Net: ₹[B] Lakhs [SELLING/BUYING] pressure

**Notable Participants:**
Sellers (Concerning if known investors):
- [Name] - [Institution/HNI/Fund] sold ₹[X] L on [Date]
  └─ Reason: [Known investor exiting = bearish signal]

Buyers (Positive or Contrarian?):
- [Name] - [Institution/HNI] bought ₹[Y] L on [Date]
  └─ Risk: Value buyers emerging = reversal risk

**Pattern Analysis:**
✅ SUPPORTS SELL:
   - Consistent bulk selling, minimal buying
   - Known long-term holders selling
   - Institutional names in seller list

🔴 CONTRADICTS SELL:
   - Bulk buying increasing
   - Opportunistic investors accumulating
   - Value-focused funds entering

**{stockName} Bulk Deal Signal:**
- Pattern: [🔴 Heavy distribution / ⚪ Mixed / 🟢 Accumulation on dip]
- Quality of participants: [Known smart money selling ✅ / Mixed / Buying 🔴]
\`\`\`

#### 6. Short Interest (if F&O available):

\`\`\`
**Futures & Options Data:**

IF {stockName} has F&O:

**Futures Open Interest:**
- Current Futures OI: [X] lots
- Change from previous week: [+/-Y] lots ([+/-Z]%)
- Long Buildup / Short Buildup: [Assessment from Price + OI change]

**Logic:**
- Price ↓ + OI ↑ = Short Buildup ✅ (Bearish, supports SELL)
- Price ↓ + OI ↓ = Long Unwinding ⚪ (Selling but shorts not adding)
- Price ↓ + OI → = Spot selling (no futures activity)

**Put-Call Ratio (PCR):**
- Current PCR: [X.XX]
- Interpretation:
  └─ PCR >1.3: More puts (bearish bets) than calls = Bearish sentiment
  └─ PCR 0.7-1.3: Neutral
  └─ PCR <0.7: More calls (bullish bets) = Bullish sentiment (risk for SELL)

**Options Open Interest:**
- Strike with Max Put OI: ₹[X] ([Y] lots) - Likely support
- Strike with Max Call OI: ₹[Z] ([A] lots) - Likely resistance
- Max Pain: ₹[B] - Price where option sellers win

**Implication for ₹{entry} → ₹{target}:**
- Support at: ₹[X] (Max Put OI) - May face buying here
- Target ₹{target} is [above/below/at] key support
- Probability: [Assessment based on OI structure]

**{stockName} F&O Sentiment:**
- Positioning: [Bearish ✅ / Neutral ⚪ / Bullish 🔴]
- Supports SELL? [Yes/Uncertain/No]

IF NO F&O:
"No derivatives available - cannot assess short interest or options positioning. Relying solely on cash market signals."
\`\`\`

### Smart Money Verdict:

\`\`\`
**Smart Money Flow Scorecard:**

| Component | Assessment | Score /100 | Weight | Weighted |
|-----------|-----------|-----------|--------|----------|
| FII/DII Activity | [Selling/Neutral/Buying] | [XX] | 25% | [X.X] |
| Promoter Behavior | [Selling/Stable/Buying] | [XX] | 20% | [X.X] |
| Insider Transactions | [Selling/Neutral/Buying] | [XX] | 15% | [X.X] |
| Volume & Delivery Pattern | [Distribution/Mixed/Accumulation] | [XX] | 20% | [X.X] |
| Bulk Deals | [Selling/Mixed/Buying] | [XX] | 10% | [X.X] |
| F&O Positioning | [Bearish/Neutral/Bullish] | [XX] | 10% | [X.X] |
| **TOTAL SMART MONEY SCORE** | | | **100%** | **[XX.X]** |

**Interpretation (for SELL trades):**
75-100: ✅✅ MASS EXODUS - Smart money running, strong SELL confirmation
60-74: ✅ DISTRIBUTION - Significant selling, supports SELL
40-59: ⚪ MIXED - Some selling, some buying, uncertain
25-39: 🔴 ACCUMULATION - Smart money buying dip, risky SELL
0-24: 🔴🔴 AGGRESSIVE BUYING - Institutions loading, SKIP SELL

**{stockName} Smart Money Status:** [XX.X]/100 → [Rating]

**Trend Driver Analysis:**
Primary Sellers: [🔴 Institutional exodus / ⚪ Retail panic / Mixed]
Primary Buyers: [Retail catching falling knife / Value institutions / Mixed]

**Most Important Finding:**
[Highlight THE most significant smart money signal - e.g., "FII cut stake from 8.2% to 4.1% over 2 quarters (₹180 Cr sold) while promoters also sold 1.8% - coordinated exit by those with inside knowledge signals deep fundamental concerns beyond quarterly volatility"]

**Does Smart Money Support SELL to ₹{target}?**
[✅ YES - Clear institutional exit validates downtrend]
[⚠️ MIXED - Some exit but also value buying emerging]
[❌ NO - Institutions actually accumulating, skip SELL]

**Reversal Risk from Smart Money:**
[🟢 LOW - Continued selling expected]
[🟡 MEDIUM - Stabilizing, monitor]
[🔴 HIGH - Institutions turning buyers, exit SELL]
\`\`\`

---

## SECTION 5: SECTOR MOMENTUM & RELATIVE WEAKNESS

**Why This Matters for SELL:**
\`\`\`
Stock falling in rising sector = Stock-specific problem = Good SELL
Stock falling in falling sector = Sector-wide issue = All boats sinking

If sector is weak AND stock is weakest in sector = Best SELL candidate
If sector is strong but stock falling = Isolated weakness = High conviction SELL
If stock falling inline with sector = Sector bet, not stock bet = Lower conviction
\`\`\`

### Search Strategy:
\`\`\`
Query 1: "[SECTOR] sector India performance February 2025"
Query 2: "Nifty [SECTOR] index trend {date}"
Query 3: "[SECTOR] stocks performance ranking India"
Query 4: "FII DII selling [SECTOR] sector India"
Query 5: "Sector rotation India money flow {date}"
Query 6: "{stockName} vs competitors performance comparison"
Query 7: "[SECTOR] sector headwinds India 2025"
\`\`\`

### Analysis Framework:

#### 1. Sector Classification & Trend:

\`\`\`
**Sector Identification:**
- Primary Sector: [AUTO-DETECT from stock nature]
- Sub-Sector: [Specific niche]
- Benchmark Index: [Nifty Sector Index or BSE Sectoral]

**Sector Performance vs Nifty:**

| Period | [SECTOR] Index | Nifty 50 | Relative Perf | Sector Trend |
|--------|----------------|----------|---------------|--------------|
| 1 Week | [+/-X]% | [+/-Y]% | [+/-Z]% | [Bull/Bear/Sideways] |
| 2 Weeks | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| 1 Month | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| 3 Months | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| 6 Months | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| YTD 2025 | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |

**Sector Status Assessment:**

✅ STRONGLY SUPPORTS SELL:
   - Sector in clear downtrend (negative across all periods)
   - Underperforming Nifty significantly (>5% relative weakness)
   - Sector momentum deteriorating (recent weakness worse)
   - Money rotating OUT of sector
   → All boats sinking, amplifies individual stock weakness

✅ SUPPORTS SELL (Stock-specific weakness):
   - Sector sideways or modestly positive
   - BUT {stockName} falling sharply
   → Isolated weakness = Stock has unique problems = Good SELL

⚪ NEUTRAL:
   - Sector mildly negative, stock in-line
   → Sector-driven fall, not stock-specific

🔴 CONTRADICTS SELL:
   - Sector in strong uptrend
   - Outperforming Nifty
   - BUT {stockName} falling
   → Stock falling in rising sector = Either opportunity OR temporary issue
   → Risky SELL, high reversal probability

**{stockName}'s Sector Status:**
- Trend: [Strong Down ✅✅ / Down ✅ / Sideways ⚪ / Up 🔴]
- Relative to Nifty: [Underperforming / Inline / Outperforming]
- **SELL Implication:** [Tailwind / Neutral / Headwind]
\`\`\`

#### 2. Sector Ranking & Money Rotation:

\`\`\`
**Nifty Sectoral Performance Ranking ({date} - Last 1 Month):**

Rank | Sector | 1M Return | Status
-----|--------|-----------|--------
1 | [Sector Name] | [+X]% | 🔥 Hot sector
2 | [Sector Name] | [+X]% | 🔥
3 | [Sector Name] | [+X]% | 🔥
... | ... | ... | ...
X | **[{stockName}'s Sector]** | **[+/-X]%** | **← {stockName} is here**
... | ... | ... | ...
10 | [Sector Name] | [-X]% | ❄️
11 | [Sector Name] | [-X]% | ❄️ Cold sector
12 | [Sector Name] | [-X]% | ❄️

**Sector Rank:** [X]/12

✅ SUPPORTS SELL:
   - Sector in bottom 3 (Rank 10-12) = Sector out of favor
   - Money rotating OUT = All sector stocks under pressure
   → Confirms broad-based sector weakness

⚪ NEUTRAL:
   - Middle tier (Rank 4-9)
   → Some sectors worse, some better

🔴 RISKY SELL:
   - Top 3 sectors (Rank 1-3) = Sector in favor
   - {stockName} falling in hot sector = Isolated weakness OR value trap
   → Risky SELL if sector has strong momentum

**{stockName} Sector Rank Impact:**
- Rank [X]/12: [Analysis]
- Money Flow: [Rotating OUT ✅ / Balanced ⚪ / Rotating IN 🔴]
\`\`\`

**Sector-Specific Money Flows:**
\`\`\`
**[SECTOR] Sector FII/DII Activity:**

| Period | FII (₹Cr) | DII (₹Cr) | Net (₹Cr) | Signal |
|--------|-----------|-----------|-----------|--------|
| Last Week | [+/-X] | [+/-Y] | [+/-Z] | [Selling/Buying] |
| Last Month | [+/-X] | [+/-Y] | [+/-Z] | [Same] |
| Last Quarter | [+/-X] | [+/-Y] | [+/-Z] | [Same] |

**Flow Assessment:**
✅ SUPPORTS SELL:
   - Net outflows from sector (FII+DII both selling)
   - Accelerating outflows (recent > previous)
   → Sector being abandoned

⚪ MIXED:
   - Balanced or marginal flows

🔴 CONTRADICTS:
   - Net inflows (institutions buying sector)
   → Even if {stockName} weak, sector strength may support recovery

**Current Flow Status:** [Outflow ✅ / Balanced ⚪ / Inflow 🔴]
\`\`\`

#### 3. Relative Strength - {stockName} vs Sector:

\`\`\`
**{stockName} Performance vs Sector Benchmark:**

| Period | {stockName} | [SECTOR] Index | Relative Performance | Assessment |
|--------|-------------|----------------|---------------------|------------|
| 1 Week | [+/-X]% | [+/-Y]% | [Z]% | [Weaker/Stronger/Inline] |
| 1 Month | [+/-X]% | [+/-Y]% | [Z]% | [Same] |
| 3 Months | [+/-X]% | [+/-Y]% | [Z]% | [Same] |
| 6 Months | [+/-X]% | [+/-Y]% | [Z]% | [Same] |

**Relative Strength Signal:**

✅✅ STRONGEST SELL CONFIRMATION:
   - {stockName} falling MORE than sector across ALL periods
   - Consistent underperformance (not just recent)
   - Widening gap (underperformance accelerating)
   → Stock-specific issues AMPLIFYING sector weakness = Best SELL candidate

✅ STRONG SELL:
   - Underperforming sector significantly (>5% relative weakness)
   → Clear stock-specific problem

⚪ SECTOR-DRIVEN:
   - Falling IN-LINE with sector (±2% relative)
   → Sector weakness, not unique to stock
   → Lower conviction SELL

🔴 RELATIVE STRENGTH (Warning):
   - Falling LESS than sector (relative outperformance)
   - Or sector down but stock down less
   → Could outperform on sector recovery
   → Risky SELL

**{stockName} Relative Strength:**
- Short-term (1M): [Weaker by X% / Inline / Stronger]
- Medium-term (3M): [Same]
- **Pattern:** [Consistent underperformance ✅ / Mixed ⚪ / Relative strength 🔴]
\`\`\`

#### 4. Sector Leaderboard - Where Does {stockName} Rank?

\`\`\`
**[SECTOR] Top & Bottom Performers (3 Months):**

**Top 5 Outperformers:**
Rank | Stock | 3M Return | Why Outperforming
-----|-------|-----------|------------------
1 | [Stock Name] | [+X]% | [Reason - new orders, margin expansion, etc.]
2 | [Stock Name] | [+X]% | [Reason]
3 | [Stock Name] | [+X]% | [Reason]
4 | [Stock Name] | [+X]% | [Reason]
5 | [Stock Name] | [+X]% | [Reason]

**Bottom 5 Underperformers:**
Rank | Stock | 3M Return | Why Underperforming
-----|-------|-----------|--------------------
[Y-4] | [Stock Name] | [-X]% | [Reason]
[Y-3] | [Stock Name] | [-X]% | [Reason]
[Y-2] | **{stockName}** | **[-X]%** | **← TARGET STOCK**
[Y-1] | [Stock Name] | [-X]% | [Reason]
[Y] | [Stock Name] | [-X]% | [Reason - worst in sector]

**{stockName} Position:** Rank [X]/[Y total stocks] in sector

✅ IDEAL SELL CANDIDATE:
   - Bottom 3 in sector (among worst performers)
   - Specific reasons identifiable (not random)
   → Justified underperformance = Can fall further

⚪ MID-PACK:
   - Middle of sector
   → Average, neither best nor worst

🔴 WARNING:
   - Among top performers despite recent fall
   - OR was leader, now correcting
   → May be temporary dip in otherwise strong stock

**Analysis:**
{stockName} ranks [X]/[Y] because: [Specific reason - margins worst, growth slowest, debt highest, etc.]
Peers outperforming because: [Contrast - they have pricing power, better product mix, etc.]
\`\`\`

**Peer Group Direct Comparison (Similar Size/Niche):**
\`\`\`
| Stock | Mkt Cap | 3M Return | YTD | Key Strength/Weakness |
|-------|---------|-----------|-----|----------------------|
| {stockName} | ₹[X]Cr | [-Y]% | [-Z]% | [Why falling - specify] |
| Peer 1 | ₹[X]Cr | [+/-Y]% | [+/-Z]% | [Why better/worse] |
| Peer 2 | ₹[X]Cr | [+/-Y]% | [+/-Z]% | [Same] |
| Peer 3 | ₹[X]Cr | [+/-Y]% | [+/-Z]% | [Same] |

**Key Differentiator:**
{stockName} is worst because: [THE specific competitive disadvantage or problem]
\`\`\`

#### 5. Sector-Specific Headwinds/Tailwinds:

\`\`\`
**Current Sector Dynamics for [SECTOR]:**

🔴 **HEADWINDS (Support SELL if {stockName} exposed):**
Check which apply to {stockName}:
- [ ] Regulatory tightening (price controls, compliance costs)
- [ ] Demand slowdown (end-market weakness)
- [ ] Input cost inflation (raw materials, energy)
- [ ] Competition intensifying (pricing pressure, margin squeeze)
- [ ] Technology disruption (obsolescence risk)
- [ ] Import competition (low-cost alternatives)
- [ ] Policy changes (adverse tax, duty, subsidies removed)
- [ ] Environmental/ESG pressures
- [ ] Forex headwinds (for exporters: ₹ appreciation / for importers: ₹ depreciation)
- [ ] Working capital pressure (receivables days increasing sector-wide)

**{stockName} Exposure:** [High/Medium/Low to these headwinds]

🟢 **TAILWINDS (Risk to SELL if {stockName} benefits):**
- [ ] Government support (PLI scheme, subsidies)
- [ ] Demand recovery (end-market improving)
- [ ] Favorable policy (import duty changes, tax benefits)
- [ ] Technology adoption (digitization, new products)
- [ ] Pricing power (scarcity, consolidation)
- [ ] Input cost decline
- [ ] China+1 sourcing shift (for Indian manufacturers)
- [ ] Export opportunities (global demand)

**{stockName} Exposure:** [High/Medium/Low to these tailwinds]

**Net Sector Outlook:**
- Headwinds: [X] factors identified
- Tailwinds: [Y] factors identified
- Balance: [🔴 Net Negative ✅ / ⚪ Neutral / 🟢 Net Positive 🔴 risky for SELL]

**Specific to {stockName}:**
Most affected by: [#1 headwind that impacts this stock most]
Could benefit from: [#1 tailwind if any]
**Net Impact:** [Strengthens SELL case / Neutral / Weakens SELL case]
\`\`\`

### Sector Context Verdict:

\`\`\`
**Sector Analysis Scorecard:**

| Factor | Assessment | Score /100 | Weight | Weighted |
|--------|------------|-----------|--------|----------|
| Sector Trend | [Down/Sideways/Up] | [XX] | 30% | [X.X] |
| Sector Rank (vs Other Sectors) | [Bottom 3/Mid/Top 3] | [XX] | 20% | [X.X] |
| Relative Weakness ({stockName} vs Sector) | [Weaker/Inline/Stronger] | [XX] | 25% | [X.X] |
| Sector Money Flows | [Outflow/Balanced/Inflow] | [XX] | 15% | [X.X] |
| Headwinds vs Tailwinds | [Net negative/Neutral/Net positive] | [XX] | 10% | [X.X] |
| **TOTAL SECTOR SCORE** | | | **100%** | **[XX.X]** |

**Interpretation (for SELL trades):**
75-100: ✅✅ STRONG SECTOR WEAKNESS - Amplifies SELL case
60-74: ✅ SECTOR SUPPORTS SELL - Favorable environment
40-59: ⚪ NEUTRAL - Stock-specific factors dominate
25-39: 🔴 SECTOR STRENGTH - Headwind for SELL
0-24: 🔴🔴 STRONG SECTOR - Avoid SELL, sector will lift stock

**{stockName} Sector Context:** [XX.X]/100 → [Rating]

**Is {stockName}'s Downtrend Sector-Driven or Stock-Specific?**

Analysis:
- Sector Performance: [Weak ✅ / Neutral ⚪ / Strong 🔴]
- {stockName} vs Sector: [Falling MORE (stock-specific) / INLINE (sector-driven) / LESS (relative strength)]

**Classification:**
[✅ STOCK-SPECIFIC WEAKNESS - Best SELL candidate]
[✅ SECTOR-DRIVEN with STOCK AMPLIFICATION - Strong SELL]
[⚪ PURE SECTOR-DRIVEN - Moderate SELL]
[🔴 STOCK WEAK in STRONG SECTOR - Risky, may reverse]

**Does Sector Context Support SELL to ₹{target}?**
[✅ YES - Sector weakness amplifies individual stock problems]
[⚪ NEUTRAL - Sector not a factor, stock-specific]
[❌ NO - Sector strength will support recovery]

**Key Insight (2-3 sentences):**
[Synthesize whether sector dynamics support continued fall, or if sector recovery will drag {stockName} up despite stock-specific issues. Be specific about sector's role in the SELL thesis.]

**Example:**
"Healthcare sector ranks 9/12, underperforming Nifty by 8% over 3 months with FII outflows of ₹2,400 Cr - clear sector weakness. However, {stockName} has underperformed sector by additional 12%, falling 20% vs sector's 8% decline. This stock-specific weakness (margin compression + order loss) amplifies sector-wide pressure, validating SELL case to ₹{target}."
\`\`\`

---

// Continuing from previous message...

---

## SECTION 6: TREND HEALTH & REVERSAL RISK

**Critical for SELL Trades:**
\`\`\`
Unlike BUY trades where "buy and hold" works, SELL trades have TIME DECAY:
- Downtrends exhaust faster than uptrends
- Oversold bounces are sharp and violent
- Dead cat bounces can hit stop loss quickly
- Market has upward bias long-term

Must assess: Is downtrend EARLY (safe to ride) or LATE (exhausted, reversal imminent)?
\`\`\`

### Search Strategy:
\`\`\`
Query 1: "{stockName} technical analysis support resistance"
Query 2: "{stockName} RSI oversold stochastic levels"
Query 3: "{stockName} moving average 50 DMA 200 DMA"
Query 4: "{stockName} downtrend started when how long"
Query 5: "Nifty market trend bull bear {date}"
Query 6: "India VIX volatility index {date}"
Query 7: "{stockName} volume pattern distribution exhaustion"
Query 8: "{stockName} price action lower lows highs"
\`\`\`

### Analysis Framework:

#### 1. Trend Stage & Maturity - "How Old Is This Downtrend?"

\`\`\`
**Downtrend Timeline:**

Peak Price: ₹[X] on [DD-MMM-YYYY]
Current Price: ₹{entry}
Days Since Peak: [X] days ([Y] weeks)
Total Decline: [Z]% from peak

**Visual Timeline:**
Peak ₹[X] ──────▼─────────▼──────── Current ₹{entry} ────?───▼ Target ₹{target}
         [Date]              [Date]              [Today]              [Future]
         
**Trend Stage Classification:**

EARLY STAGE (Days 1-15 / Decline 0-15%):
├─ Characteristics: Fresh breakdown, momentum building
├─ Volume: Increasing on down days
├─ Sentiment: Denial phase, "it will bounce back"
├─ Probability of continuation: HIGH (70-80%)
└─ **SELL Risk:** LOW - Plenty of room to fall ✅

MID STAGE (Days 15-45 / Decline 15-30%):
├─ Characteristics: Established downtrend, sustained selling
├─ Volume: Heavy but not exhausting
├─ Sentiment: Acceptance, capitulation starting
├─ Probability of continuation: MODERATE-HIGH (55-70%)
└─ **SELL Risk:** MODERATE - Still viable but watch for exhaustion ✅

LATE STAGE (Days 45-90 / Decline 30-50%):
├─ Characteristics: Extended move, oversold conditions
├─ Volume: May be declining (exhaustion)
├─ Sentiment: Full capitulation, panic selling
├─ Probability of continuation: LOW-MODERATE (35-55%)
└─ **SELL Risk:** HIGH - Reversal imminent ⚠️

VERY LATE / EXHAUSTED (>90 days / >50% decline):
├─ Characteristics: Extreme oversold, washout
├─ Volume: Very low, no sellers left
├─ Sentiment: Maximum pessimism
├─ Probability of continuation: VERY LOW (<35%)
└─ **SELL Risk:** VERY HIGH - Skip SELL, reversal due 🔴

**{stockName} Current Stage:**
- Age: [X] days = [EARLY / MID / LATE / VERY LATE]
- Decline: [Y]% = [Classification]
- **Assessment:** [Safe to ride ✅ / Monitor closely ⚠️ / Too late 🔴]

**Additional Fall Required to Target:**
From ₹{entry} to ₹{target} = [Z]% additional decline
vs Already fallen: [A]% from peak
Ratio: Asking for [Z/A]× the decline already seen
**Realistic?** [Yes ✅ / Maybe ⚠️ / Unlikely 🔴]
\`\`\`

#### 2. Volume Confirmation - "Is Selling Accelerating or Exhausting?"

\`\`\`
**Volume Analysis During Downmove:**

| Period | Avg Volume | vs Baseline | Volume on Down Days | Volume on Up Days | Pattern |
|--------|------------|-------------|---------------------|-------------------|---------|
| Week 1 (Most Recent) | [X]M shares | [+/-Y%] | [High/Low] | [High/Low] | [Assess] |
| Week 2 | [X]M shares | [+/-Y%] | [High/Low] | [High/Low] | [Assess] |
| Week 3 | [X]M shares | [+/-Y%] | [High/Low] | [High/Low] | [Assess] |
| Week 4 | [X]M shares | [+/-Y%] | [High/Low] | [High/Low] | [Assess] |

**Volume Trend:** [↑ Increasing / → Stable / ↓ Declining]

**Healthy Downtrend Volume Pattern:**
✅✅ IDEAL:
   - Volume INCREASING as price falls (fresh selling)
   - HIGH volume on down days (2-3× average)
   - LOW volume on up days (weak bounces)
   - Rising volume = Rising conviction to sell
   → Distribution phase intact, trend has legs

✅ ACCEPTABLE:
   - Volume steady to slightly increasing
   - Consistent participation
   → Normal downtrend

⚠️ WARNING:
   - Volume DECLINING on down moves (sellers drying up)
   - Equal or higher volume on up days (buyers entering)
   → Exhaustion signs, reversal risk elevated

🔴🔴 EXHAUSTION:
   - Volume very low on down days (no sellers left)
   - Volume spikes on up days (short covering, buying)
   - Extreme low volume = Washout complete
   → SKIP SELL - Reversal imminent

**{stockName} Volume Pattern:**
- Trend: [Healthy distribution ✅ / Mixed ⚪ / Exhaustion 🔴]
- Down day volume: [Increasing ✅ / Stable ⚪ / Declining 🔴]
- Up day volume: [Low ✅ / Medium ⚪ / High 🔴]
- **Signal:** [Supports continued fall / Uncertain / Reversal warning]

**Volume-Price Divergence Check:**
- Price making new lows? [Yes/No]
- Volume increasing on new lows? [Yes ✅ / No 🔴]
- If NO: 🔴 Bearish divergence exhausted, reversal risk
\`\`\`

#### 3. Technical Divergence Analysis:

\`\`\`
**Divergence Checks (Uses dampened oscillators from strategy):**

**Bearish Divergences (Support continued fall):**
- [ ] Lower lows in price, RSI also making lower lows ✅ (Bearish confirmed)
- [ ] MACD histogram declining, making new lows ✅
- [ ] OBV (On-Balance Volume) falling faster than price ✅ (Heavy distribution)
- [ ] CMF (Chaikin Money Flow) deeply negative and staying negative ✅
- [ ] ADX rising (trend strengthening) ✅

**Bullish Divergences (Reversal WARNING - Critical for SELL):**
- [ ] Price making lower lows, BUT RSI making HIGHER lows 🔴🔴 (Positive divergence)
- [ ] Price new low, BUT MACD histogram rising 🔴 (Momentum loss)
- [ ] OBV rising while price falls 🔴 (Accumulation despite fall)
- [ ] CMF turning positive despite price fall 🔴 (Money flowing in)
- [ ] Stochastic forming bullish crossover in oversold zone 🔴

**{stockName} Divergence Status:**

Bearish Divergences Found: [X] signals → [Strong/Moderate/Weak confirmation]
Bullish Divergences Found: [Y] signals → [None ✅ / Warning ⚠️ / Critical 🔴]

**Most Critical Finding:**
[Identify THE most important divergence signal, if any]

IF Bullish Divergence Present:
🔴🔴 HIGH REVERSAL RISK
- RSI/MACD showing positive divergence = Momentum exhausted
- Recommendation: [Skip SELL / Exit if already short / Reduce target to ₹[X]]

IF No Divergences:
✅ CLEAR - Trend intact, no reversal signals from momentum
\`\`\`

#### 4. Key Support & Resistance Levels:

\`\`\`
**Price Levels Between ₹{entry} and ₹{target}:**

**ABOVE (Resistance if price bounces):**
- R1: ₹{stopLoss} ([Our stop loss - CRITICAL])
- R2: ₹[X] ([20 DMA / Previous support turned resistance])
- R3: ₹[Y] ([50 DMA / Psychological level])
- R4: ₹[Z] ([Major resistance if trend breaks])

**BELOW (Support levels toward target):**
- S1: ₹[A] ([Minor support / Recent low])
- S2: ₹[B] ([Psychological level - e.g., ₹100])
- S3: ₹{target} ([Our target - is this major support?])
- S4: ₹[C] ([Next support if target breaks])

**Path Analysis from ₹{entry} to ₹{target}:**

Required Move: ₹{entry} → ₹{target} = ${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(1)}%

**Obstacles En Route:**
1. **₹[LEVEL 1] Support:**
   - Nature: [Psychological / Technical / Historical]
   - Strength: [Weak / Moderate / Strong]
   - Tests: [X] times in past [Y] months
   - Likely Action: [Break through / Temporary hold / Major support]
   - Probability of breaking: [High >70% / Medium 40-70% / Low <40%]

2. **₹[LEVEL 2] Support (if applicable):**
   - [Same analysis]

3. **₹{target} Target Level:**
   - Is this historical support? [Yes/No - Details]
   - If YES: Strong support = May not reach, adjust target to ₹[X]
   - Last time at this level: [Date - X months ago]
   - What happened then: [Bounced/Broke through]

**Cumulative Probability:**
- Reach ₹[LEVEL 1]: [X]% probability
- Break ₹[LEVEL 1] and reach ₹[LEVEL 2]: [Y]% probability  
- Reach final target ₹{target}: [Z]% probability

**Conviction for Full Target:**
[🟢 HIGH >60% / 🟡 MEDIUM 40-60% / 🔴 LOW <40%]

IF LOW: Consider adjusted target: ₹[LEVEL] instead of ₹{target}
\`\`\`

#### 5. Oscillator Extremes - "How Oversold Is Too Oversold?"

\`\`\`
**Current Oscillator Readings:**

| Indicator | Current Level | Zone | Interpretation |
|-----------|--------------|------|----------------|
| RSI (14) | [X] | [>70 OB / 30-70 Normal / <30 OS] | [Assessment] |
| Stochastic | [X] | [>80 OB / 20-80 Normal / <20 OS] | [Assessment] |
| Williams %R | [X] | [>-20 OB / -20 to -80 Normal / <-80 OS] | [Assessment] |
| CCI | [X] | [>100 OB / -100 to 100 Normal / <-100 OS] | [Assessment] |

**IMPORTANT CONTEXT:**
Trend Following strategy DAMPENS oscillators (0.5× weight for RSI/Stoch)
- Philosophy: "Oversold can stay oversold in downtrends"
- Ignores typical mean-reversion signals
- BUT: Extreme oversold still matters for REVERSAL RISK

**Oversold Bounce Risk Assessment:**

✅ LOW RISK (Safe to SELL):
   - RSI >35 (Not oversold yet, room to fall)
   - Stochastic >25
   - No extreme readings
   → Can fall further before bounce risk

⚠️ MODERATE RISK:
   - RSI 25-35 (Oversold but not extreme)
   - Stochastic 10-25
   → Dead cat bounce possible, but trend can resume

🔴 HIGH RISK:
   - RSI 20-25 (Very oversold)
   - Stochastic 5-10
   - Multiple indicators extreme
   → Bounce likely, may hit stop loss

🔴🔴 EXTREME RISK (SKIP SELL):
   - RSI <20 (Extreme oversold, <10 = washout)
   - Stochastic <5
   - All oscillators at multi-month lows
   → Bounce imminent, high probability of stop loss hit
   → Recommendation: SKIP or wait for bounce to re-short

**{stockName} Oscillator Risk:**
- RSI at [X]: [Safe ✅ / Caution ⚠️ / Extreme 🔴]
- Overall Oversold Level: [Not/Moderately/Very/Extremely Oversold]
- **Bounce Risk:** [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH / 🔴🔴 EXTREME]

**Historical Bounce Patterns:**
When {stockName} reached similar RSI levels in past:
- Typical bounce magnitude: [X]% (from low to high of bounce)
- Duration: [Y] days before downtrend resumed (if it did)
- vs Our Stop Loss: ₹{stopLoss} = ${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}% buffer
- Risk: [Bounce could hit stop ⚠️ / Stop should hold ✅]
\`\`\`

#### 6. Market Regime - "Is Broader Market Supportive?"

\`\`\`
**Broader Market Context for SELL Trades:**

| Index | Current | 20 DMA | 50 DMA | 200 DMA | Position | Trend |
|-------|---------|--------|--------|---------|----------|-------|
| Nifty 50 | [X] | [Y] | [Z] | [A] | [Above all/Mixed/Below] | [🟢 Bull / ⚪ Neutral / 🔴 Bear] |
| Nifty Midcap 100 | [X] | [Y] | [Z] | [A] | [Same] | [Same] |
| Nifty Smallcap 100 | [X] | [Y] | [Z] | [A] | [Same] | [Same] |
| Bank Nifty | [X] | [Y] | [Z] | [A] | [Same] | [Same] |

**Market Regime for SELL Trades:**

✅ IDEAL FOR SELL:
   - Nifty in downtrend (below 50 DMA, declining)
   - All indices weak
   - Broad market selling
   → Tailwind for individual stock shorts

✅ ACCEPTABLE:
   - Market sideways/choppy
   - Mixed signals
   → Stock-specific factors dominate

🔴 CHALLENGING FOR SELL:
   - Nifty in strong uptrend (above all DMAs, rising)
   - Broad market rally
   - Risk-on sentiment
   → Even weak stocks get lifted, shorts get squeezed

**Current Nifty Status:**
- Position: [Above/Below key averages]
- Trend: [Up 🔴 / Sideways ⚪ / Down ✅]
- **SELL Environment:** [Favorable ✅ / Neutral ⚪ / Challenging 🔴]

**Market Breadth:**
- Advance/Decline: [X]:[Y] → [More declining ✅ / Balanced ⚪ / More advancing 🔴]
- New 52W Lows: [X] stocks (High ✅ / Normal ⚪ / Low 🔴)
- New 52W Highs: [Y] stocks (Low ✅ / Normal ⚪ / High 🔴)

**India VIX:**
Current VIX: [X]
Assessment:
├─ <15: Low volatility, calm market (easier SELL execution)
├─ 15-20: Normal volatility (manageable)
├─ 20-25: Elevated volatility (choppy, risky for SELL)
└─ >25: High volatility (very risky, panic, unpredictable)

**VIX Level [X]:** [✅ Favorable / ⚪ Acceptable / 🔴 Too volatile]

**Risk-On vs Risk-Off:**
Global sentiment: [Risk-off ✅ (defensive, good for shorts) / Risk-on 🔴 (aggressive, shorts risky)]
FII activity: [Selling ✅ / Neutral ⚪ / Buying 🔴]
**Overall:** [Supportive ✅ / Neutral ⚪ / Headwind 🔴]
\`\`\`

#### 7. Event Risk Calendar - "Surprises That Could Break Thesis"

\`\`\`
**Upcoming Events (Next 30-60 Days):**

| Date | Event | Potential Impact | Positive Surprise Probability | Risk to SELL |
|------|-------|------------------|------------------------------|--------------|
| [DD-MMM] | Q[X] FY[YY] Earnings | Could beat, reverse trend | [High/Med/Low] | [🔴 Critical / 🟡 Moderate / 🟢 Low] |
| [DD-MMM] | Board Meeting | Unknown agenda, surprise? | [High/Med/Low] | [Same] |
| [DD-MMM] | RBI Policy | Rate cut = market positive | [High/Med/Low] | [Same] |
| [DD-MMM] | Sector Event | PLI benefit, budget allocation | [High/Med/Low] | [Same] |

**Highest Risk Event:** [Event Name] on [Date]
**Days from Now:** [X] days
**If Positive Surprise:**
- Potential gap up: [+Y%]
- vs Stop Loss: ₹{stopLoss} = ${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}% buffer
- Can stop protect? [Yes ✅ / No - gap through 🔴]

**Risk Mitigation Plan:**

IF Event in next 7-14 days with HIGH positive surprise risk:
→ 🔴 Consider SKIPPING trade entirely
→ OR reduce position to 50% and exit before event
→ OR use options (Put buying) for defined risk

IF Event 14-30 days away with MEDIUM risk:
→ ⚠️ Monitor approach closely
→ Plan to exit 1-2 days before if uncertainty high

IF Event >30 days away OR LOW risk:
→ ✅ Trade as planned, reassess as date approaches

**{stockName} Event Risk:** [🔴 HIGH - Adjust plan / 🟡 MODERATE - Monitor / 🟢 LOW - Proceed]
\`\`\`

### Trend Health & Reversal Risk Verdict:

\`\`\`
**Comprehensive Trend Health Assessment:**

| Risk Factor | Status | Score /20 | Trend Health |
|-------------|--------|-----------|--------------|
| Trend Maturity | [Early/Mid/Late/Exhausted] | [X] | [Fresh ✅ / Mature ⚪ / Old 🔴] |
| Volume Pattern | [Accelerating/Stable/Exhausting] | [X] | [Healthy ✅ / Mixed ⚪ / Weak 🔴] |
| Technical Divergence | [None/Bearish/Bullish] | [X] | [Clear ✅ / Warning ⚠️ / Alert 🔴] |
| Support Levels | [Clear path/Some/Strong] | [X] | [Room to fall ✅ / Obstacles ⚪ / Major support 🔴] |
| Oscillator Extremes | [Normal/Oversold/Extreme] | [X] | [Safe ✅ / Caution ⚠️ / Danger 🔴] |
| Market Regime | [Bear/Neutral/Bull] | [X] | [Supportive ✅ / Neutral ⚪ / Challenging 🔴] |
| Event Risk | [Low/Medium/High] | [X] | [Clear ✅ / Some ⚠️ / Critical 🔴] |
| **TOTAL TREND HEALTH** | | **[XXX]/140** | |

**Interpretation:**
105-140: ✅ HEALTHY DOWNTREND - Low reversal risk, full target viable
80-104: ✅ ACCEPTABLE - Some caution but tradeable
60-79: ⚠️ MODERATE RISK - Consider reduced target or size
40-59: ⚠️ HIGH RISK - Late stage, bounce likely
0-39: 🔴 EXHAUSTED - Skip SELL, reversal imminent

**{stockName} Trend Health:** [XXX]/140 → [Rating]

**Reversal Risk Assessment:**
- Short-term (<1 week): [🟢 LOW / 🟡 MEDIUM / 🔴 HIGH]
- Medium-term (1-4 weeks to target): [Same]
- Factors: [Most critical reversal risks identified]

**Target Achievability:**
Given trend health score of [XXX]/140:
- Probability of reaching ₹{target}: [X]%
- Expected outcome: [Full target / Partial to ₹[Y] / Time/stop exit]
- Timeframe: [X weeks if successful]
\`\`\`

### Scenario Probability Analysis:

\`\`\`
**Probabilistic Outcome Modeling:**

**BASE CASE ([X]% Probability):**
Scenario: Downtrend continues but stalls before full target
- Price Movement: ₹{entry} → ₹[PARTIAL TARGET ~80% of way]
- Return: [-A]% (vs -${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(1)}% target)
- Timeline: [Y] weeks
- Exit Reason: [Support holds / Momentum fades / Time decay]
- Action Plan: Book partial profits at ₹[LEVEL], exit before exhaustion

**BULL CASE for SELL ([Y]% Probability):**
Scenario: Clean fall to full target or below
- Price Movement: ₹{entry} → ₹{target} or lower
- Return: [-${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(1)}]% or better
- Timeline: [Z] weeks
- Catalysts Needed: [Specific negative developments]
- Action Plan: Full target achieved, book profits

**BEAR CASE for SELL ([Z]% Probability):**
Scenario: Reversal, stop loss hit
- Price Movement: ₹{entry} → ₹{stopLoss}
- Loss: [+${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}]%
- Timeline: [A] days (quick)
- Triggers: [Oversold bounce / Positive surprise / Market rally]
- Action Plan: Accept stop loss, don't chase or re-short immediately

**EXPECTED VALUE CALCULATION:**

EV = (P_BullCase × Return_BullCase) + (P_BaseCase × Return_BaseCase) + (P_BearCase × Return_BearCase)

EV = ([Y]% × [-${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(1)}]%) + ([X]% × [-A]%) + ([Z]% × [+${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}]%)

**EV = [CALCULATED: -B.B]%**

**Risk-Adjusted Return:**
- Expected Value: [-B.B]%
- Capital at risk: [X]% of portfolio (planned position size)
- Time horizon: [Y] weeks
- Annualized return (if EV positive): [Calculation]

**Assessment:**
├─ EV >-5%: ✅ ATTRACTIVE - Good risk-reward for SELL trade
├─ EV -3% to -5%: ✅ ACCEPTABLE - Viable trade
├─ EV -1% to -3%: ⚠️ MARGINAL - Consider reducing size
├─ EV 0% to -1%: ⚠️ POOR - Better opportunities exist
└─ EV >0%: 🔴 NEGATIVE - Skip trade

**{stockName} Expected Value: [-B.B]%** → [Rating]
**Worth Trading?** [✅ YES / ⚠️ CONDITIONAL / ❌ NO]
\`\`\`

---

## 🎯 FINAL CONSOLIDATED VERDICT

### Multi-Dimensional Scorecard:

\`\`\`
**Comprehensive SELL Trade Assessment:**

| Dimension | Assessment | Score /100 | Weight | Weighted | Impact |
|-----------|-----------|-----------|--------|----------|--------|
| **Technical Conviction** | Score {score} = ${Math.abs(parseFloat('{score}')) > 0.70 ? 'Strong' : Math.abs(parseFloat('{score}')) > 0.50 ? 'Moderate' : Math.abs(parseFloat('{score}')) > 0.30 ? 'Weak' : 'Very Weak'} | ${Math.abs(parseFloat('{score}')) * 100} | 20% | [X.X] | [Baseline] |
| **Liquidity & Execution** | [From Section 1] | [XX] | 15% | [X.X] | [Critical for SELL] |
| **Catalyst Strength** | [From Section 2] | [XX] | 15% | [X.X] | [PRIMARY for SELL] |
| **Fundamental Deterioration** | [From Section 3] | [XX] | 20% | [X.X] | [Justification] |
| **Smart Money Exit** | [From Section 4] | [XX] | 15% | [X.X] | [Validation] |
| **Sector Weakness** | [From Section 5] | [XX] | 10% | [X.X] | [Context] |
| **Trend Health** | [From Section 6] | [XX] | 5% | [X.X] | [Reversal Risk] |
|-----------|-----------|-----------|--------|----------|--------|
| **TOTAL SELL SCORE** | | | **100%** | **[XX.X]** | |

**Note on Weighting:**
SELL trades weight Catalyst (15%) higher than typical
- Need REASON to fall, not just "falling because falling"
- Catalyst + Deterioration = 35% combined (highest weight)
\`\`\`

### Decision Matrix Application:

\`\`\`
**Score-Based SELL Recommendation:**

TOTAL SCORE: [XX.X]/100

85-100: ✅✅ STRONG SELL - Execute with high conviction
        - All factors aligned: Catalysts + Deterioration + Smart money exit
        - Position Size: 3-5% portfolio (aggressive for trend trade)
        - Target: Full ₹{target} viable
        - Confidence: HIGH (75-85%)

70-84: ✅ SELL - Execute with standard position
        - Most factors supportive, minor concerns
        - Position Size: 2-3% portfolio
        - Target: ₹{target} or slightly adjusted
        - Confidence: GOOD (60-75%)

55-69: ⚠️ CONDITIONAL SELL - Execute with reduced size
        - Mixed signals, some supporting factors
        - Position Size: 1-2% portfolio
        - Target: May adjust to ₹[REDUCED] vs full ₹{target}
        - Confidence: MODERATE (45-60%)

40-54: ⚠️ WEAK SELL - Consider skipping
        - More negatives than positives
        - Position Size: 0.5-1% (toe in water) IF trading
        - Target: Significantly reduced expectations
        - Confidence: LOW (30-45%)

0-39: ❌ SKIP - Do not trade
        - Insufficient evidence for SELL
        - High reversal risk or value trap
        - Better opportunities exist
        - Confidence: VERY LOW (<30%)

**{stockName} Classification:** [Based on score] → [Recommendation]
\`\`\`

### Override Rules - Mandatory Checks:

\`\`\`
🔴🔴 MANDATORY SKIP - DO NOT SELL if ANY:
- [ ] Illiquid (Avg Daily Value <₹50 Lakhs)
- [ ] Extreme oversold (RSI <20, Stochastic <5)
- [ ] Major positive catalyst in next 7-14 days (earnings beat likely)
- [ ] Promoters aggressively buying during fall
- [ ] FII/DII both increasing stake significantly (smart money sees value)
- [ ] Sector in strong uptrend while stock falling (will get lifted)
- [ ] Stock already fallen >50% from peak (exhaustion)
- [ ] Bullish technical divergences present (RSI higher lows on price lower lows)
- [ ] No identifiable catalyst (just "falling because falling")

⚠️ REDUCE POSITION SIZE 50% if ANY:
- [ ] Moderately oversold (RSI 20-30, approaching bounce zone)
- [ ] Mixed institutional flows (FII selling but DII buying)
- [ ] Sector weakness but stock showing relative strength
- [ ] Approaching major historical support level
- [ ] Late-stage downtrend (>30 days, >30% fall already)
- [ ] High event risk (binary event in 2-4 weeks)
- [ ] Market in strong uptrend (headwind for shorts)

✅ CAN USE STANDARD/FULL SIZE if ALL:
- [ ] Clear catalyst identified and sustainable
- [ ] Fundamentals deteriorating measurably
- [ ] Smart money exiting (FII/DII selling, delivery % falling)
- [ ] Adequate liquidity (>₹1 Cr daily)
- [ ] Not extreme oversold (RSI >30, room to fall)
- [ ] Early to mid-stage downtrend (plenty of life left)
- [ ] No major bullish events imminent
- [ ] Sector supportive or neutral

**{stockName} Override Check:**
[✅ PASSED - All clear to trade]
[⚠️ CONDITIONAL - Triggers: [List] → Adjustments: [Specify]]
[🔴 FAILED - Rule: [Specific override] → SKIP trade]
\`\`\`

### Position Sizing for SELL Trades:

\`\`\`
**Conviction-Based Sizing:**

Base Position Size (from score):
├─ Score >85: 4-5% portfolio (high conviction)
├─ Score 70-85: 2.5-4% (standard)
├─ Score 55-70: 1.5-2.5% (reduced)
├─ Score 40-55: 0.5-1.5% (minimal)
└─ Score <40: 0% (skip)

**SELL Trade Multipliers:**

Signal Strength Adjustment:
├─ Strong SELL ({score} < -0.70): +0% (use full base size)
├─ Moderate SELL ({score} -0.50 to -0.70): -20% (reduce base)
├─ Weak SELL ({score} -0.30 to -0.50): -40% (reduce more)
└─ Very Weak ({score} > -0.30): -60% or skip

Current Signal: {score} = ${Math.abs(parseFloat('{score}')) > 0.70 ? 'Strong' : Math.abs(parseFloat('{score}')) > 0.50 ? 'Moderate' : Math.abs(parseFloat('{score}')) > 0.30 ? 'Weak' : 'Very Weak'}
Multiplier: [X]%

Liquidity Adjustment:
├─ If Daily Value <₹1 Cr: Reduce by 50%
├─ If F&O illiquid: Reduce by 30%
├─ If Wide spreads >1%: Reduce by 20%

Reversal Risk Adjustment:
├─ If Trend Health <60/140: Reduce by 30-50%
├─ If Oversold (RSI <30): Reduce by 40%
├─ If Event risk high: Reduce by 30-50%

**FINAL RECOMMENDED POSITION SIZE:**

Base (from score [XX]): [A]%
× Signal adjustment: [B]%
× Liquidity adjustment: [C]%
× Reversal risk adjustment: [D]%
= **FINAL: [E]% of portfolio**

In absolute terms (₹10L portfolio):
→ Investment: ₹[CALCULATED]
→ Risk (if stop hit): ₹[CALC × stop %]
→ Reward (if target hit): ₹[CALC × target %]
\`\`\`

---

### 🎯 FINAL RECOMMENDATION:

\`\`\`
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  VERDICT: [✅ EXECUTE SELL / ⚠️ CONDITIONAL / 🔴 SKIP]        │
│                                                               │
│  Confidence: [🟢 HIGH 75%+ / 🟡 MEDIUM 50-75% / 🔴 LOW <50%] │
│                                                               │
│  Position Size: [X.X]% of portfolio                          │
│                                                               │
│  Method: [Sell holdings / Futures short / Put buying]        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
\`\`\`

---

### IF ✅ EXECUTE SELL - Detailed Trade Plan:

\`\`\`
📋 **SHORT/SELL EXECUTION PLAN:**

**Entry Strategy:**

Method Selection:
${`
IF you OWN {stockName}:
   → Action: SELL existing holdings
   → Order: [Market/Limit at ₹{entry}]
   → Timing: [Immediate/On bounce to ₹[X]]
   
IF you DON'T own {stockName} AND F&O available:
   → Method 1 (Aggressive): Futures Short
      ├─ Lot Size: [X] lots = [Y] shares
      ├─ Margin Required: ₹[Z]
      ├─ Mark-to-Market: Daily
      └─ Suitable for: High conviction, comfortable with volatility
   
   → Method 2 (Conservative): Put Buying
      ├─ Strike: ₹[CHOOSE - ATM or slightly OTM]
      ├─ Premium: ₹[X] per share
      ├─ Max Loss: Limited to premium paid
      ├─ Benefits from: Price fall + Volatility increase
      └─ Suitable for: Moderate conviction, defined risk

IF No F&O:
   → Cannot actively short this stock
   → Analysis is for "hold vs sell holdings" decision only
`}

**Position Details:**
- Entry Price: ₹{entry}
- Position Size: [E]% portfolio = ₹[AMOUNT] = [SHARES] shares
- Entry Timing: [Immediate / Wait for bounce to ₹[LEVEL] / Staged entry]

**Exit Strategy - STOP LOSS (CRITICAL FOR SHORTS):**

🔴 STOP LOSS: ₹{stopLoss} - NON-NEGOTIABLE

**Stop Loss Rules for SELL Trades:**
1. ✅ SET IMMEDIATELY after entry (stop-loss buy order at ₹{stopLoss})
2. ❌ NEVER WIDEN STOP (unlike longs, shorts need tight discipline)
3. ❌ NEVER "wait to see" if it comes back (shorts can gap against you)
4. ✅ Consider tightening stop if price moves favorably
5. ⚠️ If gap up through stop, EXIT AT MARKET immediately on open

**Stop Loss = ₹{stopLoss}:**
- Distance: ₹${Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')).toFixed(2)}
- Risk: ${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(2)}%
- Total Risk: ₹[AMOUNT] × ${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(2)}% = ₹[CALCULATED]

**IF STOP HIT:**
- Exit entire position, no hesitation
- Do NOT re-short same day (revenge trading)
- Wait minimum [3-5] days before re-evaluating
- Accept loss as part of trading (this trade didn't work)

**Exit Strategy - PROFIT TARGETS:**

**Target Management (Conservative for SELL):**

Given Signal Strength {score} and Total Score [XX]/100:

${Math.abs(parseFloat('{score}')) > 0.70 && '[XX]' > '75' ? `
**STRONG SETUP - Full Target Viable:**
- Target 1: ₹[60% to target] - Book 30-40% position
- Target 2: ₹{target} - Book another 30-40%
- Target 3: Trail remaining 20-30% below ₹{target}
` : Math.abs(parseFloat('{score}')) > 0.50 ? `
**MODERATE SETUP - Balanced Approach:**
- Target 1: ₹[50% to target] - Book 40% position (secure some profit)
- Target 2: ₹{target} - Book 40% position
- Target 3: Trail final 20% with tight stop
` : `
**WEAK SETUP - Take Profits Early:**
- Target 1: ₹[30-40% to target] - Book 50% position (get some money off table)
- Target 2: ₹[70% to target] - Book remaining 50%
- Do NOT hold for full ₹{target} - too risky given weak setup
`}

**Trailing Stop Strategy (as price falls):**
- When reaches [30-40% to target]: Move stop to ₹[BREAKEVEN or small profit]
- When reaches [60-70% to target]: Lock in [X]% profit with tight stop
- When reaches ₹{target}: Trail with stop at ₹[TARGET + 1-2%]

**Time-Based Exit:**
- Maximum Holding: [30-45 days] for SELL trades
  (Downtrends exhaust faster than uptrends)
- Review at [20] days: If minimal progress, consider exit
- Don't let winning trade turn to loser by holding too long

**Event-Based Exit (CRITICAL):**
- IF earnings/major event approaching: Exit 1-2 days before
- IF unexpected positive news breaks: Exit immediately
- IF smart money turns buyers (FII/DII buying disclosed): Reassess, likely exit
- IF sector suddenly reverses to strong uptrend: Reassess urgently

**Execution Details:**

Entry Orders:
- Sell {stockName} at ₹{entry} - [Market/Limit]
- OR Short [X] Futures lots at ₹{entry}
- OR Buy [X] Put options strike ₹[Y] at ₹[Z] premium

Stop Loss Orders (Set Immediately):
- Buy Stop Loss at ₹{stopLoss} (for short position)
- Or Close Futures at ₹{stopLoss}
- Or Put Stop Loss: Accept premium loss if price rallies above ₹{stopLoss}

Target Orders (Can set in advance):
- Buy Limit orders at Target levels
- Or Scale out manually as levels hit

**Monitoring & Review Schedule:**

📅 **DAILY (First 2 Weeks):**
- [ ] Price vs ₹{stopLoss} (stop) and progress toward ₹{target}
- [ ] Volume and delivery % (exhaustion check)
- [ ] Breaking news on {stockName} (positive surprises are deadly for shorts)
- [ ] Smart money activity (any bulk buying?)
- [ ] Sector trend (sudden reversal?)

📅 **EVERY 2-3 DAYS:**
- [ ] RSI/Stochastic levels (bounce imminent if extreme oversold?)
- [ ] Support levels ahead (approaching major support?)
- [ ] Market regime (Nifty still weak or turning?)

📅 **WEEKLY:**
- [ ] Reassess catalyst sustainability (still deteriorating or stabilizing?)
- [ ] FII/DII holdings (if quarter changes, check for institutional buying)
- [ ] Fundamental updates (any positive earnings surprises in sector?)
- [ ] Expected value recalculation (still positive?)

📅 **IMMEDIATE ALERTS:**
Set price/news alerts for:
- Price reaches ₹{stopLoss} → Exit immediately
- Price reaches ₹[TARGET 1] → Book partial profits
- Price reaches ₹{target} → Execute exit plan
- Any news alert on "{stockName}" → Review impact immediately
- Promoter buying disclosed → Reassess thesis urgently
- Major positive sector news → Evaluate continuation

**Critical Checkpoints:**

Day 5-7 (Week 1):
- Progress check: [If gained <2%, reassess viability]
- [If stop approached, consider early exit]
- [If good progress, hold with confidence]

Day 14-15 (Week 2):
- Mid-point assessment
- [If halfway to target, on track]
- [If stalled, consider taking partial profits]
- [If reversing, protect position]

Day 21-25 (Week 3):
- Time decay pressure building
- [Book profits if near target]
- [Exit if minimal progress - downtrend weakening]

Day 30+ (Month mark):
- SELL trades should NOT take this long
- [If still holding, something's wrong]
- [Book whatever gains exist, move on]

**Position Management Table:**

| Scenario | Action | Reasoning |
|----------|--------|-----------|
| Price at ₹{stopLoss} | Exit entire position | Stop hit, thesis invalid |
| Price at ₹[T1] | Book [X]% | Secure partial profit |
| Price at ₹{target} | Book [Y]% | Target achieved |
| RSI drops to <20 | Consider partial exit | Extreme oversold, bounce risk |
| Positive news breaks | Exit [50-100]% | Catalyst invalidated |
| [X] days, no progress | Exit | Time decay, find better opportunity |
| Sector reverses strongly | Reassess/Exit | Headwind emerged |
| FII starts buying | Reassess urgently | Smart money disagrees |
\`\`\`

---

### IF ⚠️ CONDITIONAL SELL - Modified Approach:

\`\`\`
**PROCEED WITH MODIFICATIONS:**

**Primary Concerns Identified:**
1. [Most critical issue - e.g., "Moderately oversold, RSI at 28, bounce risk"]
2. [Second concern - e.g., "Mixed smart money signals - FII selling but DII buying"]
3. [Third concern - e.g., "Earnings in 18 days, binary event risk"]

**Modified Trade Parameters:**

**REDUCED Position Size:**
- Standard recommendation: [A]%
- **ADJUSTED to: [B]% (50-70% of standard)**
- Rationale: Lower conviction due to [specific concerns]

**ADJUSTED Targets:**
- Original Target: ₹{target} (${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(1)}% fall)
- **Revised Target: ₹[CONSERVATIVE]** (${((Math.abs(parseFloat('{entry}') - parseFloat('[CONSERVATIVE]')) / parseFloat('{entry}')) * 100).toFixed(1)}% fall)
- Rationale: [Approach major support / Time constraints / Reversal risk]

**TIGHTER Stop Loss (Optional):**
- Original Stop: ₹{stopLoss} (${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(2)}%)
- **Consider: ₹[TIGHTER]** (${((Math.abs(parseFloat('[TIGHTER]') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(2)}%)
- Rationale: [Lower conviction, don't want large loss]
- Trade-off: Tighter stop = higher probability of being stopped out

**EARLIER Exit Timeline:**
- Standard hold: 30-45 days
- **Revised hold: [15-25] days**
- Rationale: [Event approaching / Late-stage trend / Weak setup]
- Action: If no meaningful progress by day [15], exit

**Alternative Execution:**
Instead of direct short/sell:
→ **Consider Put Option buying** (defined risk)
   - Strike: ₹[CHOOSE]
   - Premium: ₹[X] (max loss)
   - Expiry: [Date]
   - Benefit: Limited downside, still profit from fall

**Conditional Entry:**
Instead of immediate entry:
→ **Wait for confirmation:**
   - Enter only if breaks below ₹[LEVEL]
   - Or wait for bounce to ₹[HIGHER LEVEL], then short
   - Reduces risk of catching falling knife at wrong level

**Enhanced Monitoring:**
- Daily checks MANDATORY (not optional)
- Set tighter alerts (stop loss, minor resistance levels)
- Be prepared to exit on first sign of reversal
- Don't hope or wait - act quickly if thesis breaks

**Upgrade Conditions (to full position):**
IF during trade:
1. [Condition - e.g., "RSI falls below 25 without bounce"] AND
2. [Condition - e.g., "Major negative catalyst emerges"] AND
3. [Condition - e.g., "Volume accelerates on downside"]
→ THEN can add to position, move to full size

**Downgrade Conditions (exit immediately):**
IF during trade:
1. [Condition - e.g., "Price rallies back above ₹[LEVEL]"] OR
2. [Condition - e.g., "Promoter buying disclosed"] OR  
3. [Condition - e.g., "FII turns net buyer"]
→ EXIT regardless of stop loss, thesis invalidated

**Risk-Reward at Modified Levels:**
- Entry: ₹{entry}
- Modified Stop: ₹[ADJUSTED]
- Modified Target: ₹[ADJUSTED]
- Risk: [X]%
- Reward: [Y]%
- R:R: 1:[Z]
- Assessment: [Still acceptable / Marginal / Poor]
\`\`\`

---

### IF 🔴 SKIP - Do Not Trade:

\`\`\`
❌ **RECOMMENDATION: DO NOT EXECUTE SELL TRADE**

**Primary Reasons for Skipping (Top 3):**

1. **[MOST CRITICAL REASON]**
   - Evidence: [Specific data point]
   - Why disqualifying: [Explanation]
   - Example: "No identifiable catalyst - stock just falling on technical breakdown without fundamental deterioration. Catalyst score only 22/100. High probability of reversal/dead cat bounce."

2. **[SECOND REASON]**
   - Evidence: [Specific data point]
   - Why problematic: [Explanation]
   - Example: "Extreme oversold - RSI at 18, Stochastic at 4, lowest levels in 2 years. Historical pattern shows 8-12% bounce when this oversold. Stop loss at ₹{stopLoss} would be hit."

3. **[THIRD REASON]**
   - Evidence: [Specific data point]
   - Impact: [Why this matters]
   - Example: "Smart money accumulating - FII increased stake by 1.8% last quarter, 3 new MF entries. Institutions see value that technical analysis misses. Shorting into institutional buying is dangerous."

**Why These Factors Matter:**

[2-3 sentences explaining how these specific issues make this a poor risk-reward trade, likely to result in loss]

Example: "The combination of absent catalyst, extreme oversold conditions, and institutional accumulation creates a 'perfect storm' for short squeeze. Probability of stop loss hit (>60%) exceeds probability of target hit (<25%). Expected value is negative at -3.2%. This is not a favorable SELL setup."

**What Would Make {stockName} Shortable:**

**For This Stock to Become a Good SELL:**

Technical Improvements Needed:
1. [Specific change - e.g., "Bounce to ₹110-115, then fail again (better entry)"]
2. [Another - e.g., "Volume increases on down days (confirms distribution)"]
3. [Third - e.g., "RSI bounces to 40-50 range (not oversold anymore)"]

Fundamental Deterioration Needed:
1. [Specific catalyst - e.g., "Next quarter earnings miss by 15%+"]
2. [Another - e.g., "Major client loss disclosed (₹50+ Cr annual revenue)"]
3. [Third - e.g., "Credit rating downgrade to sub-investment grade"]

Smart Money Confirmation Needed:
1. [Flow change - e.g., "FII cuts stake by >2% (currently increasing)"]
2. [Another - e.g., "Promoter pledge increases to >75% (financial stress)"]
3. [Third - e.g., "Multiple mutual fund exits in single quarter"]

**Monitoring Plan (If Interested in Future):**

Add {stockName} to watchlist, check:
- Weekly: Price action, volume, news
- Monthly: Quarterly results, shareholding pattern
- Trigger alerts for:
  └─ Price: If bounces to ₹[X-Y range] (better short entry)
  └─ News: "{stockName} earnings" / "{stockName} order" / "{stockName} FII"
  └─ Technical: RSI crosses above 40 (oversold bounce complete)

**Re-evaluation Timeline:**
- Next earnings: [Date] - Check for deterioration
- Next shareholding: [Quarter end] - Check for institutional exit
- Technical reset: [2-4 weeks] - Reassess after bounce completes

**Alternative Opportunities:**

IF interested in shorting this SECTOR:
Better candidates (if identifiable):
- [Stock 1]: [Ticker] - [Why better: worse fundamentals, clearer catalyst, etc.]
- [Stock 2]: [Ticker] - [Why better]

IF interested in SELLING in general:
Look for stocks with:
✅ Clear negative catalyst (earnings miss, guidance cut, major loss)
✅ Strong institutional exit (FII down >2% in 2 quarters)
✅ Early to mid-stage downtrend (not oversold yet)
✅ Sector weakness amplifying individual issues
✅ Deteriorating fundamentals (margins, debt, cash flow)

**Current Market Better Suited For:**
[Long positions in strong sectors / Waiting on sidelines / Sector rotation plays]

**Final Word:**
It's better to skip a marginal SELL setup than force a trade that doesn't meet criteria. SELL trades are inherently riskier than BUY trades - they require higher conviction and clearer evidence. When in doubt, stay out.
\`\`\`

---

### 📊 TOP 3 RISKS (Detailed):

\`\`\`
**Risk Priority Ranking (Specific to {stockName} SELL):**

🔴🔴 **RISK #1: [HIGHEST PRIORITY RISK]**

Description: [Detailed explanation of the most critical risk factor]

Example: "OVERSOLD BOUNCE RISK - RSI at 23, Stochastic at 7, multiple momentum indicators at 2-year lows. Historical analysis shows {stockName} bounces 8-15% within 3-7 days when this oversold."

Probability: [HIGH 60%+ / MEDIUM 30-60% / LOW <30%]
- Calculation: [How this probability was determined]
- Historical precedent: [Data from similar situations]

Impact if Occurs:
- Price could bounce to: ₹[X] ([+Y]% from entry)
- vs Stop Loss at: ₹{stopLoss} ([+${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}]%)
- **Stop would be hit:** [YES, easily / Possibly / No, stop should hold]
- Potential Loss: [Actual loss amount in ₹ and %]

Early Warning Signs:
- [ ] RSI crosses above 25 (momentum shifting)
- [ ] Volume increases on up days (buying pressure)
- [ ] Price closes above ₹[LEVEL] (resistance break)
- [ ] Delivery % suddenly spikes (conviction buying)
- [ ] Sudden positive news (catalyst for bounce)

Mitigation Strategies:
1. [Action - e.g., "Exit 50% of position if RSI crosses 27"]
2. [Action - e.g., "Set tighter stop at ₹[X] if bounce starts"]
3. [Action - e.g., "Use Put options instead of direct short (limited loss)"]
4. [Action - e.g., "Wait for bounce to ₹[X-Y], then re-short"]

---

🔴 **RISK #2: [SECOND PRIORITY]**

Description: [Specific risk factor]

Example: "EARNINGS POSITIVE SURPRISE - Q4 FY25 results on [DATE] in 23 days. Historical pattern shows 3 of last 4 quarters beat estimates. If beats again, stock could gap up 10-15%, blowing through our stop."

Probability: [Assessment]
- Based on: [Reasoning]

Impact if Occurs:
- Gap up potential: [+X]% to ₹[Y]
- Stop loss protection: [Adequate / Inadequate]
- Actual loss if gap: [Calculation]

Early Warning Signs:
- [ ] Positive management commentary (con-call, media)
- [ ] Peer companies beating estimates (sector improvement)
- [ ] Analyst upgrades ahead of results (bullish pre-positioning)
- [ ] Put-Call Ratio falling (options traders turning bullish)

Mitigation:
1. [e.g., "Exit position 2 days before earnings"]
2. [e.g., "Reduce position by 70% before event"]
3. [e.g., "Accept event risk but size position accordingly (1% max)"]
4. [e.g., "Use Put Spreads instead of naked short (cap loss)"]

---

⚠️ **RISK #3: [THIRD CONCERN]**

Description: [Detailed explanation]

Example: "SMART MONEY REVERSAL - While FII reduced stake last quarter, DII actually increased by 0.8%. Some value-focused mutual funds entered. If this is start of institutional accumulation, our SELL thesis is wrong."

Probability: [Assessment]

Impact:
- If institutions are right and we're wrong: [Scenario]
- Potential for prolonged sideways or even reversal
- May not hit stop but may not reach target either (opportunity cost)

Early Warning Signs:
- [ ] Next quarterly holdings show further DII/MF increase
- [ ] Bulk deals show institutional buying
- [ ] Delivery % consistently above 60% (conviction)
- [ ] Price forms higher lows (base building)

Mitigation:
1. [e.g., "Monitor quarterly holdings closely, exit if institutional buying accelerates"]
2. [e.g., "Set price-based stop (if makes higher low above ₹[X], exit)"]
3. [e.g., "Time stop - if no progress in 15 days, exit regardless"]
4. [e.g., "Acknowledge institutions may be right, our time horizon may be too short"]
\`\`\`

---

### ✅ TOP 3 SUPPORTING FACTORS:

\`\`\`
**Factors Supporting SELL Thesis (Ranked by Importance):**

✅✅ **FACTOR #1: [STRONGEST SUPPORT]**

Evidence: [Specific, quantifiable data]

Example: "CLEAR FUNDAMENTAL DETERIORATION - EBITDA margins compressed 420 bps over 3 quarters (from 18.5% to 14.3%) due to raw material inflation without pricing power. Management guided for 'continued pressure for 2-3 quarters.' This is structural, not cyclical."

Why This Matters:
- Justifies lower valuation multiples
- Sustainable negative catalyst (6+ months)
- Not easily reversible (contract lock-ins prevent price hikes)
- Directly impacts bottom line (₹12 Cr annual PAT impact at current run rate)

Strength: [🟢 HIGH / 🟡 MEDIUM / ⚪ LOW]
- HIGH because: Quantifiable, manageable acknowledged, duration specified

Contribution to SELL Thesis: [XX]% weight
- Primary fundamental reason for expected continued fall
- Supports target of ₹{target} where stock would trade at P/E of [Y.Y]x vs current [Z.Z]x

---

✅ **FACTOR #2: [SECOND STRONGEST]**

Evidence: [Specific data]

Example: "INSTITUTIONAL EXODUS - FII stake reduced from 9.2% to 5.1% over 2 quarters (₹240 Cr sold). 4 mutual funds exited completely. Delivery % declined from 58% to 41% over same period. Smart money is running."

Why This Matters:
- Institutions typically have better information than retail
- Large-scale exit creates sustained selling pressure
- Falling delivery % shows conviction weak, holders ready to sell on any bounce
- Creates downward spiral: Lower price → more selling → lower price

Strength: [Assessment]
- HIGH because: Magnitude significant, multiple fund types exiting, sustained over 2 quarters

Contribution: [XX]% weight
- Validates that problems are real (not just technical noise)
- Ensures continued selling pressure toward target
- Reduces probability of short squeeze (fewer strong hands left)

---

✅ **FACTOR #3: [THIRD SUPPORTING]**

Evidence: [Data]

Example: "SECTOR-WIDE WEAKNESS - Healthcare underperforming Nifty by 11% over 3 months with net FII outflows of ₹3,200 Cr. Regulatory uncertainty on price controls dampening entire sector. {stockName} is WORST performer in sector (-22% vs sector -11%), amplifying sector weakness with stock-specific issues."

Why This Matters:
- Macro headwind makes recovery harder
- Even if company-specific issues resolve, sector drag persists
- Money rotating OUT of sector reduces buying interest
- Stock-specific weakness ON TOP OF sector weakness = double negative

Strength: [Assessment]

Contribution: [XX]% weight
- Provides broader context beyond just stock
- Reduces probability of sharp reversal (would need sector AND stock recovery)
- Supports duration of downtrend (sector trends last months, not days)
\`\`\`

---

### 📝 EXECUTIVE SUMMARY (The Bottom Line):

\`\`\`
**{stockName} ({ticker}) SELL TRADE - FINAL ASSESSMENT**

**Technical Setup:**
- Signal: {verdict}
- Conviction: {score}/1.0 = ${Math.abs(parseFloat('{score}')) > 0.70 ? 'STRONG Bearish' : Math.abs(parseFloat('{score}')) > 0.50 ? 'MODERATE Bearish' : Math.abs(parseFloat('{score}')) > 0.30 ? 'WEAK Bearish' : 'BARELY Bearish'}
- Trade: ₹{entry} (Entry) → ₹{stopLoss} (Stop -${((Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(1)}%) | ₹{target} (Target -${((Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / parseFloat('{entry}')) * 100).toFixed(1)}%)
- Risk-Reward: 1:${(Math.abs(parseFloat('{entry}') - parseFloat('{target}')) / Math.abs(parseFloat('{stopLoss}') - parseFloat('{entry}'))).toFixed(2)}

**Comprehensive Score: [XX.X]/100**

**THE 5 Key Findings (One sentence each):**

1. **Catalyst:** [Most important finding on WHY it's falling]
   Example: "Primary catalyst is 420 bps margin compression from polymer cost inflation, guided to persist 2-3 quarters with no pricing power recovery."

2. **Fundamentals:** [Critical fundamental finding]
   Example: "Revenue growth decelerated from 18% to 4% YoY while debt increased 32%, OCF/PAT ratio fell to 0.71 indicating quality concerns."

3. **Smart Money:** [Institutional positioning]
   Example: "FII cut stake from 9.2% to 5.1% (₹240 Cr exit) with 4 mutual funds exiting completely, delivery % collapsed to 41%."

4. **Technical:** [Most important technical finding beyond conviction score]
   Example: "Downtrend is 28 days old with 18% fall already, RSI at 28 (oversold but not extreme), volume healthy but approaching exhaustion zone."

5. **Risk/Opportunity:** [The trade-off]
   Example: "Target ₹{target} represents strong support but achievable given catalysts; main risk is oversold bounce to ₹{stopLoss} (45% probability)."

**THE Critical Insight (2-3 sentences maximum):**

[Synthesize THE most important thing to know about this SELL trade - combining catalyst strength, sustainability, and key risk]

**Example:**
"The margin compression catalyst is structural (6+ months) and management-confirmed, validating technical downtrend. However, at 28 days old and RSI 28, downtrend is mid-to-late stage with elevated bounce risk. Institutional exodus provides confidence, but extreme oversold conditions require either reduced size (1-2% vs 3-5% standard) or waiting for bounce to ₹108-110 before shorting."

**Final Numbers:**
- Expected Value: [-X.X]% (Calculated probability-weighted return)
- Success Probability: [Y]% (reaching ₹{target})
- Stop Probability: [Z]% (hitting ₹{stopLoss})
- Recommended Position: [A]% of portfolio
- Method: [Sell holdings / Futures short / Put buying]

**One-Line Verdict:**
[EXECUTE with [X]% position and target ₹{target}]
OR
[CONDITIONAL - Reduce to [X]%, adjust target to ₹[Y]]
OR
[SKIP - Risk factors [A, B, C] outweigh opportunity]

**If Trading - Watch For:**
[The ONE most critical thing to monitor daily]
Example: "RSI crossing above 30 + volume spike on up day = exit immediately, oversold bounce starting."
\`\`\`

---

## 📊 ANALYSIS METADATA

**Analysis Completed:** {date}
**Analysis Type:** Trend Following SELL Signal Validation
**Signal Strength:** {verdict} ({score}) - ${Math.abs(parseFloat('{score}')) > 0.70 ? 'Strong' : Math.abs(parseFloat('{score}')) > 0.50 ? 'Moderate' : Math.abs(parseFloat('{score}')) > 0.30 ? 'Weak' : 'Very Weak'} Bearish

**Data Freshness:**
- Price Data: [Last updated: Date/Time within 24 hours]
- Financial Data: [Latest quarter available: QX FY25]
- Shareholding: [Latest quarter: QX FY25]
- News: [Scanned through: Date]
- Volume/Delivery: [Current as of: Date]

**Data Quality Score:** [🟢 HIGH >80% / 🟡 MEDIUM 60-80% / 🔴 LOW <60%]
**Confidence Impact:** [How data availability affected analysis quality]

**Critical Data Gaps:**
- [List any missing data that would materially improve analysis]
- [Impact on recommendation]

**Key Assumptions Made:**
1. [Assumption - e.g., "Earnings date estimated as [DATE] based on historical pattern"]
2. [Assumption - e.g., "Institutional holdings assumed stable between quarterly reports"]
3. [Assumption - e.g., "Management guidance accurately reflects future trajectory"]

**Sources Consulted:**
1. NSE/BSE - Price, volume, corporate actions, shareholding
2. [Screener.in/MoneyControl/Trendlyne] - Financials and ratios
3. Google News - Recent developments and catalysts
4. [Company website/investor presentations] - Management commentary
5. [Bloomberg/Reuters] - Peer comparisons and sector data

**Analysis Limitations:**
- [Specific limitations - e.g., "No access to con-call transcript for Q2 FY25"]
- [How this affected conclusions]
- [Areas of uncertainty flagged]

---

**END OF TREND FOLLOWING SELL ANALYSIS FOR {stockName} ({ticker})**
**Strategy: {strategyName} | Signal: {verdict} | Score: {score} | Date: {date}**

---
`;

export default TREND_FOLLOWING_PROMPT;