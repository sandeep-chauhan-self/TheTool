/**
 * Universal Analysis Prompt
 * 
 * Specialized deep-dive framework.
 */

export const UNIVERSAL_PROMPT_TEMPLATE = `
/**
 * Comprehensive Stock Analysis Prompt - Balanced Strategy
 * Version: 2.0 - Dynamic Template
 * 
 * Optimized for "Balanced" or "Hold" signals where directional conviction is low.
 * Focuses on determining if a trade should be taken despite weak technicals,
 * or if it should be skipped/aborted.
 * 
 * Variables:
 * @param {string} stockName - Company name (e.g., "SOMATEX Medical Polymers")
 * @param {string} ticker - Stock symbol (e.g., "SOMATEX.NS")
 * @param {string} verdict - Signal type: "Buy", "Sell", "Hold"
 * @param {number} score - Conviction score (-1.0 to +1.0)
 * @param {number} entry - Entry price in ₹
 * @param {number} stopLoss - Stop loss price in ₹
 * @param {number} target - Target price in ₹
 * @param {string} strategyName - Always "Balanced Analysis" for this template
 */

export const BALANCED_ANALYSIS_PROMPT = \`
# Comprehensive Trade Validation: {stockName} ({ticker})

## 🎯 TECHNICAL SIGNAL OVERVIEW

**Stock:** {stockName} ({ticker})
**Sector:** [AUTO-DETECT via web search]
**Market Cap:** ₹[AUTO-DETECT via web search] Cr

---

### Technical Analysis Summary

**Signal:** {verdict}
**Conviction Score:** {score} / 1.000 \${
  Math.abs(parseFloat('{score}')) < 0.15 
    ? '🔴 **CRITICALLY WEAK - NEARLY NEUTRAL**' 
    : Math.abs(parseFloat('{score}')) < 0.30 
      ? '🟡 **WEAK CONVICTION**'
      : Math.abs(parseFloat('{score}')) < 0.50
        ? '🟢 **MODERATE CONVICTION**'
        : '🟢🟢 **STRONG CONVICTION**'
}

**Score Interpretation:**
\\\`\\\`\\\`
Score Range: -1.0 (Strong Sell) ← 0.0 (Neutral) → +1.0 (Strong Buy)

Position on Scale:
│────────────────────┼─────────┼─────────┼─────────┼
-1.0              -0.5      0.0      0.5      1.0
                              \${'{score}' > 0 ? '       ▲' : '▲'}

Current: {score}
Assessment: \${
  Math.abs(parseFloat('{score}')) < 0.15 
    ? 'ESSENTIALLY NEUTRAL - No clear directional bias'
    : Math.abs(parseFloat('{score}')) < 0.30
      ? 'WEAK SIGNAL - Indicators barely aligned'
      : Math.abs(parseFloat('{score}')) < 0.50
        ? 'MODERATE SIGNAL - Reasonable conviction'
        : 'STRONG SIGNAL - High confidence setup'
}
\\\`\\\`\\\`

**Trade Setup:**
- **Entry Price:** ₹{entry}
- **Stop Loss:** ₹{stopLoss}
  - Risk: ₹\${Math.abs(parseFloat('{entry}') - parseFloat('{stopLoss}')).toFixed(2)}
  - Risk %: \${((Math.abs(parseFloat('{entry}') - parseFloat('{stopLoss}')) / parseFloat('{entry}')) * 100).toFixed(2)}%
- **Target:** ₹{target}
  - Reward: ₹\${Math.abs(parseFloat('{target}') - parseFloat('{entry}')).toFixed(2)}
  - Reward %: \${((Math.abs(parseFloat('{target}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(2)}%
- **Risk-Reward Ratio:** 1:\${(Math.abs(parseFloat('{target}') - parseFloat('{entry}')) / Math.abs(parseFloat('{entry}') - parseFloat('{stopLoss}'))).toFixed(2)}

**Strategy:** {strategyName}
- **12 equally-weighted indicators**
- 4 Trend: MACD, ADX, EMA Crossover, Parabolic SAR
- 4 Momentum: RSI, Stochastic, CCI, Williams %R
- 2 Volatility: Bollinger Bands, ATR
- 2 Volume: OBV, CMF
- **Philosophy:** Comprehensive analysis, no single indicator dominates
- **Timeframe:** Daily/Weekly multi-timeframe alignment

---

## ⚠️ CRITICAL CONTEXT: SIGNAL STRENGTH ALERT

**Understanding Your Signal:**
\\\`\\\`\\\`
Conviction Score: {score}
├─ Interpretation: \${
  Math.abs(parseFloat('{score}')) < 0.15 
    ? 'Market is INDECISIVE - roughly 50% bullish / 50% bearish signals'
    : Math.abs(parseFloat('{score}')) < 0.30
      ? 'WEAK consensus - indicators barely aligned'
      : Math.abs(parseFloat('{score}')) < 0.50
        ? 'MODERATE agreement - decent setup but not strong'
        : 'STRONG consensus - high confidence setup'
}
├─ Technical indicators: \${
  Math.abs(parseFloat('{score}')) < 0.15 
    ? 'Conflicting heavily'
    : Math.abs(parseFloat('{score}')) < 0.30
      ? 'Slight lean in one direction'
      : 'Reasonably aligned'
}
└─ Default Action: \${
  Math.abs(parseFloat('{score}')) < 0.15 
    ? 'WAIT for clearer setup OR find strong fundamental reason'
    : Math.abs(parseFloat('{score}')) < 0.30
      ? 'PROCEED WITH CAUTION - reduce position size'
      : 'PROCEED - standard position sizing appropriate'
}
\\\`\\\`\\\`

**Your Analysis Objective:**

\${Math.abs(parseFloat('{score}')) < 0.30 ? \`
Since technical conviction is WEAK (score {score}), your fundamental/qualitative analysis must be DECISIVE.

You need to determine if there are compelling non-technical reasons to:
1. **Override Weak Signal** → Upgrade to STRONG BUY (if exceptional fundamentals/catalysts)
2. **Override Weak Signal** → Downgrade to SKIP/SELL (if red flags/deterioration)
3. **Confirm Signal** → Accept weak setup with REDUCED position size
4. **Reject Signal** → Wait for better technical setup (score >0.40 for Buy, <-0.40 for Sell)

**Critical Principle for Weak Signals:**
"Default to SKIP unless fundamentals provide strong conviction that technicals currently miss"
\` : \`
Technical conviction is MODERATE to STRONG (score {score}).

Your analysis should:
1. **Validate the signal** - Confirm fundamentals support the technical direction
2. **Identify risks** - What could invalidate this setup?
3. **Optimize sizing** - Adjust position size based on conviction level
4. **Set monitoring** - What metrics to watch during the trade?
\`}

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
- [ ] Liquidity metrics (volume, delivery %)

**Data Quality Baseline:**
\\\`\\\`\\\`
If ≥80% data available → Proceed with HIGH confidence ceiling
If 60-79% data available → Proceed with MEDIUM confidence ceiling  
If <60% data available → FLAG as insufficient and explain gaps
\\\`\\\`\\\`

**Stock-Specific Considerations:**
- Market cap category: [Large-cap/Mid-cap/Small-cap affects data availability]
- Sector specific risks: [Regulatory, Export, Commodity, Technology, etc.]
- Company structure: [Promoter-dominated/MNC/Professional management]
- Liquidity profile: [Actively traded/Illiquid affects execution risk]

---

## SECTION 1: LIQUIDITY & EXECUTION FEASIBILITY

### Priority: CRITICAL ⚠️⚠️⚠️

**Why This Matters:**
\${Math.abs(parseFloat('{score}')) < 0.30 ? 
\`With weak technical conviction ({score}), you CANNOT afford liquidity issues. If you can't exit cleanly when the setup fails, a marginal trade becomes DANGEROUS.\` :
\`Even with \${Math.abs(parseFloat('{score}')) > 0.50 ? 'strong' : 'moderate'} conviction, poor liquidity can destroy an otherwise good trade through slippage and execution failures.\`}

### Search Strategy:
\\\`\\\`\\\`
Query 1: "{stockName} NSE volume average daily"
Query 2: "{ticker} average traded value"
Query 3: "{stockName} delivery percentage"
Query 4: "{ticker} bid ask spread liquidity"
Query 5: "{stockName} circuit breaker hits upper lower"
Query 6: "{stockName} free float market cap"
\\\`\\\`\\\`

### Analysis Tasks:

#### 1. Volume Analysis:
\\\`\\\`\\\`
**Average Daily Metrics (20-day):**
- Traded Value: ₹[X] Lakhs/Cr
- Traded Volume: [X] shares
- Volume Trend: [Increasing ↑ / Stable → / Decreasing ↓]
- Yesterday vs 20D Avg: [+/-X]%

**Volume Quality:**
- Consistent volume: [Yes/No - spikes indicate manipulation risk]
- Volume during market hours: [Evenly distributed/Concentrated at open-close]
\\\`\\\`\\\`

#### 2. Liquidity Metrics:
\\\`\\\`\\\`
| Metric | Value | Benchmark | Status |
|--------|-------|-----------|---------|
| Avg Daily Value (20D) | ₹[X] L/Cr | >₹50L (acceptable) | [✅/⚠️/❌] |
| Market Cap | ₹[X] Cr | Context | [Size] |
| Free Float Mcap | ₹[X] Cr | >₹100 Cr preferred | [✅/⚠️/❌] |
| Delivery % (20D avg) | [X]% | >40% healthy | [✅/⚠️/❌] |
| Typical Bid-Ask Spread | [X]% | <1% ideal | [✅/⚠️/❌] |
| Impact Cost (₹5L order) | [X]% | <0.5% ideal | [✅/⚠️/❌] |
\\\`\\\`\\\`

#### 3. Risk Indicators:
\\\`\\\`\\\`
**Circuit Breaker History (Last 30 Days):**
- Upper Circuit Hits: [X] times
- Lower Circuit Hits: [Y] times
- Total: [X+Y] → [✅ 0 hits / ⚠️ 1-2 hits / 🔴 3+ hits]

**Manipulation Risk Assessment:**
- [ ] Multiple consecutive circuit hits (suspect)
- [ ] Very low delivery % <20% (operators active)
- [ ] Extreme price volatility without news (pump & dump)
- [ ] Sudden volume spikes >5x average (manipulation)
- [ ] Penny stock characteristics (avoid if yes)

**Red Flags:** [List specific concerns OR "None identified"]
\\\`\\\`\\\`

### Liquidity Decision Matrix:

\\\`\\\`\\\`
STOP ANALYSIS - DO NOT TRADE if ANY:
├─ Avg Daily Value <₹25 Lakhs → Too illiquid, skip
├─ Circuit hits >3 in 30 days → Manipulation risk
├─ Delivery % <20% consistently → Operator stock
├─ Bid-ask spread >2% → Unacceptable slippage
└─ Multiple red flags above → High risk, avoid

PROCEED WITH EXTREME CAUTION if ANY:
├─ Avg Daily Value ₹25L-₹50L → Micro position only (<1% portfolio)
├─ Delivery % 20-40% → Monitor closely
├─ Circuit hits 1-2 times → Single position entry, quick exit
├─ Free float <₹50 Cr → Limited liquidity cushion
└─ Recommendation: MAX 0.5-1% position size

ACCEPTABLE FOR TRADING if ALL:
├─ Avg Daily Value >₹50L (₹1 Cr+ preferred)
├─ Delivery % >40%
├─ No circuit hits OR justified by major news
├─ Bid-ask <1%
└─ Free float >₹100 Cr
→ Standard position sizing applicable (2-5% based on conviction)
\\\`\\\`\\\`

### Liquidity Verdict:

\\\`\\\`\\\`
**Overall Liquidity Score:** [X]/100

Calculation:
- Daily Value: [Score 0-30]
- Delivery %: [Score 0-20]
- Spread & Impact: [Score 0-20]
- Circuit History: [Score 0-20]
- Manipulation Risk: [Score 0-10]

**Interpretation:**
80-100: ✅ EXCELLENT - Highly liquid, safe execution
60-79: ✅ GOOD - Acceptable liquidity, standard sizing
40-59: ⚠️ FAIR - Proceed with caution, reduce size
20-39: 🔴 POOR - High risk, micro positions only
<20: 🔴🔴 UNACCEPTABLE - SKIP trade entirely

**{stockName} Liquidity Score:** [XX]/100

**VERDICT:** [✅ EXECUTE / ⚠️ CAUTION / 🔴 SKIP]

**If EXECUTE:**
- Recommended Order Type: [Market/Limit at ₹{entry}]
- Expected Slippage: ±[X]% (₹[Y])
- Position Size Adjustment: \${
  parseFloat('{score}') < 0.30 
    ? 'Already reduced for weak signal; liquidity doesn\\'t further reduce' 
    : 'Standard sizing applies given adequate liquidity'
}

**If CAUTION:**
- Max Position Size: [0.5-1]% of portfolio
- Entry Strategy: [Staged entry, limit orders only]
- Exit Plan: [Pre-place limit sell at target, tight monitoring]

**If SKIP:**
Primary Reason: [Most critical liquidity issue]
STOP ANALYSIS HERE - Do not proceed to other sections.
\\\`\\\`\\\`

---

## SECTION 2: NEWS, SENTIMENT & CATALYST ANALYSIS

### Search Strategy:

\\\`\\\`\\\`
Query 1: "{stockName} news last 14 days"
Query 2: "{stockName} latest quarterly results earnings"
Query 3: "{ticker} corporate announcement NSE BSE"
Query 4: "{stockName} management changes director appointment"
Query 5: "{stockName} dividend bonus split announcement"
Query 6: "{stockName} sector [SECTOR_NAME] news India 2025"
Query 7: "{stockName} analyst rating target price"
Query 8: "{stockName} upcoming events board meeting AGM"
\\\`\\\`\\\`

### Analysis Framework:

#### 1. Recent News Scan (Last 14 Days):

**Corporate Announcements:**
\\\`\\\`\\\`
| Date | Type | Details | Market Reaction | Impact |
|------|------|---------|-----------------|--------|
| [DD-MMM] | [Earnings/Dividend/etc] | [Specifics] | [Price ±X%] | [🟢/🟡/🔴] |
| [DD-MMM] | [Type] | [Details] | [Reaction] | [Impact] |

**Key Findings:**
✅ Positive Developments:
- [List specific positive news with dates]
- [Impact on business/financials]

⚠️ Neutral Developments:
- [Routine announcements]

🔴 Negative Developments:
- [List concerns with dates]
- [Impact assessment]

**No News:** [If quiet period, note this - sometimes bullish]
\\\`\\\`\\\`

**Business Developments:**
\\\`\\\`\\\`
Recent Developments:
├─ New Products/Services: [Details if any]
├─ Client Wins/Losses: [Major contracts, order announcements]
├─ Capacity Expansion: [Capex plans, new facilities]
├─ Partnerships/JVs: [Strategic tie-ups]
├─ R&D Milestones: [Certifications, patents, approvals]
└─ Geographic Expansion: [New markets, export orders]

Most Significant: [Identify the most impactful recent development]
Relevance to Trade: [How this affects ₹{entry} → ₹{target} thesis]
\\\`\\\`\\\`

**Regulatory & Legal:**
\\\`\\\`\\\`
Compliance & Legal Status:
├─ Regulatory Actions: [SEBI, Sectoral regulators]
├─ Litigation Updates: [Court cases, arbitration]
├─ Quality/Safety Issues: [Product recalls, violations]
├─ License/Certification: [Renewals, new approvals]
└─ Environmental/Social: [ESG-related news]

**Red Flags:** [List OR "None identified"]
**Green Flags:** [List OR "None identified"]
\\\`\\\`\\\`

#### 2. Sentiment Analysis:

**Analyst Coverage:**
\\\`\\\`\\\`
| Brokerage | Date | Rating | Target Price | Current View |
|-----------|------|--------|--------------|--------------|
| [Name] | [DD-MMM] | [Buy/Hold/Sell] | ₹[X] | [Upgrade/Maintain/Downgrade] |
| [Name] | [DD-MMM] | [Rating] | ₹[Y] | [Change] |

Consensus (if sufficient coverage):
- Average Target: ₹[X]
- Current Price: ₹{entry}
- Implied Upside: [+/-Y]%
- Buy/Hold/Sell Count: [X]/[Y]/[Z]

**Target vs Your Trade:**
- Your Target: ₹{target} ([Within/Above/Below] consensus)
- Analyst Support: [Strong/Moderate/Weak/Against]
\\\`\\\`\\\`

**Retail Sentiment Proxy:**
\\\`\\\`\\\`
Social/Retail Indicators:
├─ Google Trends: "{stockName} stock" [Trending ↑/→/↓]
├─ Trading Volume Pattern: [Retail rush or steady]
├─ Delivery % Trend: [Increasing = Conviction / Decreasing = Speculation]
├─ Forum Buzz: [MoneyControl, ValueResearch sentiment]
└─ Media Coverage: [Mainstream vs niche]

**Interpretation:**
🔴 FOMO Warning: Extreme retail interest can indicate top
🟢 Accumulation: Steady interest with high delivery % = healthy
⚪ Neutral: Normal levels, no extreme sentiment
\\\`\\\`\\\`

#### 3. Upcoming Events (Next 30 Days):

\\\`\\\`\\\`
**Critical Events Calendar:**

| Date | Event | Expected Outcome | Risk/Opportunity |
|------|-------|-----------------|------------------|
| [DD-MMM or TBD] | Q[X] FY[YY] Earnings | [Beat/Miss/Inline] | [🔴 High volatility / 🟢 Catalyst] |
| [DD-MMM or TBD] | Board Meeting | [Unknown/Routine] | [⚠️ Watch for surprises] |
| [DD-MMM or TBD] | Ex-Dividend Date | ₹[X] per share | [⚪ Price adjustment] |
| [DD-MMM or TBD] | AGM/EGM | [Routine/Special] | [Monitor] |
| [DD-MMM or TBD] | [Other Event] | [Details] | [Assessment] |

**Event Risk Assessment:**
\${parseFloat('{score}') < 0.30 ? 
\`⚠️ With weak signal ({score}), event risk is CRITICAL:
- If major event <7 days: Consider SKIPPING trade entirely
- If event 7-14 days: Plan exit BEFORE event
- If event >14 days: Manageable risk, monitor approach\` :
\`Event risk manageable given \${Math.abs(parseFloat('{score}')) > 0.50 ? 'strong' : 'moderate'} conviction:
- Events can provide catalyst to hit ₹{target}
- Or invalidate setup if negative surprise
- Monitor closely as dates approach\`}

**Nearest Event:** [X] days away → [Action: None/Monitor/Exit before]
\\\`\\\`\\\`

#### 4. Red Flags vs Green Flags:

**🔴 Red Flags Checklist:**
\\\`\\\`\\\`
Critical Concerns (MANDATORY SKIP if found):
- [ ] Auditor resignation/qualification
- [ ] Fraud allegations or accounting irregularities
- [ ] SEBI show-cause notice or exchange penalty
- [ ] Promoter arrest or major legal trouble
- [ ] Product ban or license cancellation

Major Concerns (Reduce confidence significantly):
- [ ] Promoter pledge >75% of holding
- [ ] Credit rating downgrade (especially to sub-investment grade)
- [ ] Loss of major client (>25% revenue)
- [ ] Debt default or restructuring
- [ ] Key management mass exodus

Moderate Concerns (Note and monitor):
- [ ] Increasing promoter pledge (trend)
- [ ] Declining market share
- [ ] Margin pressure without explanation
- [ ] Delayed financial filings
- [ ] Related party transaction concerns

**{stockName} Red Flags:** [List specific findings OR "None identified"]
\\\`\\\`\\\`

**🟢 Green Flags Checklist:**
\\\`\\\`\\\`
Strong Positives:
- [ ] Promoter buying shares in open market
- [ ] Major client wins or long-term contracts
- [ ] Debt reduction or deleveraging
- [ ] Credit rating upgrade
- [ ] Strategic partnership with industry leader
- [ ] Export breakthrough (new geography)
- [ ] Government/PLI scheme benefits

Moderate Positives:
- [ ] Capacity expansion announcements
- [ ] New product launches
- [ ] Margin improvement
- [ ] Consistent dividend policy
- [ ] Strong promoter track record

**{stockName} Green Flags:** [List specific findings OR "None identified"]
\\\`\\\`\\\`

### Sentiment Scoring System:

\\\`\\\`\\\`
**Quantitative Sentiment Score:**

Component Scores:
├─ Recent News Impact: [Score 0-25]
│  ├─ Positive news count: [X]
│  ├─ Negative news count: [Y]
│  └─ Net sentiment: [Calculation]
│
├─ Analyst Sentiment: [Score 0-20]
│  ├─ Target vs entry: [Upside/downside]
│  ├─ Rating distribution: [Buy/Hold/Sell]
│  └─ Recent changes: [Upgrades/downgrades]
│
├─ Upcoming Catalysts: [Score 0-25]
│  ├─ Positive catalysts: [Count & quality]
│  ├─ Negative risks: [Count & severity]
│  └─ Net opportunity: [Assessment]
│
├─ Red Flags: [Score 0-15, deduct for flags]
│  └─ Flags found: [-5 per moderate, -10 per major, -15 per critical]
│
└─ Green Flags: [Score 0-15, add for flags]
   └─ Flags found: [+3 per moderate, +7 per strong]

**TOTAL SENTIMENT SCORE:** [XX]/100

**Interpretation:**
75-100: 🟢🟢 VERY BULLISH - Strong positive sentiment
60-74: 🟢 BULLISH - Net positive
40-59: ⚪ NEUTRAL - Mixed signals
25-39: 🔴 BEARISH - Net negative
0-24: 🔴🔴 VERY BEARISH - Strong concerns

**{stockName} Sentiment:** [XX]/100 → [Rating]
\\\`\\\`\\\`

### Sentiment Verdict:

\\\`\\\`\\\`
**Overall Assessment:** [Rating with emoji]

**Key Insights:**
1. **Most Important Finding:** [1-2 sentences on dominant theme]
2. **Catalyst Assessment:** [What could drive ₹{entry} → ₹{target}?]
3. **Risk Assessment:** [What could cause stop loss hit?]

**Support for {verdict} Signal?**
\${'{verdict}' === 'Hold' ? \`
[✅ YES - Fundamentals support overriding weak technicals]
[⚠️ MIXED - Some support but not compelling]
[❌ NO - Sentiment suggests skipping this trade]
\` : \`
[✅ YES - Sentiment confirms technical direction]
[⚠️ MIXED - Some conflicting signals]
[❌ NO - Sentiment contradicts technical signal]
\`}

**Recommendation Override:**
\${Math.abs(parseFloat('{score}')) < 0.15 ? \`
Given critically weak signal ({score}), sentiment must be DECISIVE:
- If Score >70: Can UPGRADE to BUY despite weak technicals
- If Score <40: Should DOWNGRADE to SKIP
- If Score 40-70: CONFIRM HOLD, wait for better setup
\` : Math.abs(parseFloat('{score}')) < 0.30 ? \`
Given weak signal ({score}), sentiment provides conviction:
- If Score >75: Proceed with confidence
- If Score <30: Skip trade
- If Score 30-75: Reduce position size accordingly
\` : \`
Sentiment validates or challenges \${Math.abs(parseFloat('{score}')) > 0.50 ? 'strong' : 'moderate'} signal:
- Confirming sentiment: Trade with conviction
- Conflicting sentiment: Reduce size or reconsider
\`}

**Final Sentiment Call:** [Specific recommendation based on findings]
\\\`\\\`\\\`

---

## SECTION 3: FUNDAMENTAL HEALTH CHECK

### Search Strategy:

\\\`\\\`\\\`
Query 1: "{stockName} latest quarterly results balance sheet"
Query 2: "{ticker} financial ratios Screener Tijori"
Query 3: "{stockName} debt equity ratio cash flow"
Query 4: "{stockName} revenue profit growth trend"
Query 5: "{stockName} vs peers comparison sector"
Query 6: "{stockName} PE ratio PB ratio valuation"
Query 7: "{stockName} promoter holding pledged shares"
Query 8: "{stockName} ROE ROCE profit margins"
\\\`\\\`\\\`

### Analysis Framework:

#### 1. Valuation Metrics:

\\\`\\\`\\\`
**Current Valuation vs Sector:**

| Metric | {stockName} | Sector Median | Historical 3Y Avg | Status |
|--------|-------------|---------------|-------------------|--------|
| P/E (TTM) | [X.X]x | [Y.Y]x | [Z.Z]x | [✅ Cheap / ⚪ Fair / 🔴 Expensive] |
| P/E (Forward) | [X.X]x | [Y.Y]x | [Z.Z]x | [Same] |
| P/B Ratio | [X.X]x | [Y.Y]x | [Z.Z]x | [Same] |
| EV/EBITDA | [X.X]x | [Y.Y]x | [Z.Z]x | [Same] |
| EV/Sales | [X.X]x | [Y.Y]x | [Z.Z]x | [Same] |
| Dividend Yield | [X.X]% | [Y.Y]% | [Z.Z]% | [Above/Below sector] |
| PEG Ratio | [X.X] | [Y.Y] | - | [✅ <1.5 / ⚪ 1.5-2.5 / 🔴 >2.5] |

**Valuation Summary:**
At ₹{entry}:
- Absolute Assessment: [Cheap/Fairly Valued/Expensive]
- Relative to Sector: Trading at [X]% [premium/discount]
- Relative to History: [Below/At/Above] 3-year average
- Price/Fair Value: [Calculation if data available]

**Interpretation:**
✅ **Undervalued**: Multiple metrics below sector, room for re-rating
⚪ **Fair**: In-line with sector and history, priced reasonably
🔴 **Overvalued**: Above sector on most metrics, downside risk

**{stockName} Valuation:** [Assessment]
\\\`\\\`\\\`

#### 2. Financial Stability:

\\\`\\\`\\\`
**Balance Sheet Strength:**

| Metric | Latest | Previous | 1Y Ago | Trend | Status |
|--------|--------|----------|--------|-------|--------|
| Debt/Equity | [X.X]x | [Y.Y]x | [Z.Z]x | [↑/↓/→] | [✅ <0.5 / ⚪ 0.5-1.0 / ⚠️ 1.0-2.0 / 🔴 >2.0] |
| Current Ratio | [X.X] | [Y.Y] | [Z.Z] | [↑/↓/→] | [✅ >2.0 / ⚪ 1.5-2.0 / ⚠️ 1.0-1.5 / 🔴 <1.0] |
| Interest Coverage | [X.X]x | [Y.Y]x | [Z.Z]x | [↑/↓/→] | [✅ >5 / ⚪ 3-5 / ⚠️ 2-3 / 🔴 <2] |
| Cash & Equivalents | ₹[X] Cr | ₹[Y] Cr | ₹[Z] Cr | [↑/↓/→] | [Strength] |
| Total Debt | ₹[X] Cr | ₹[Y] Cr | ₹[Z] Cr | [↑/↓/→] | [vs Cash] |

**Debt Analysis:**
- Net Debt (Debt - Cash): ₹[X] Cr
- Net Debt/EBITDA: [Y.Y]x ([✅ <2 / ⚪ 2-4 / 🔴 >4])
- Debt Trend: [Increasing 🔴 / Stable ⚪ / Decreasing ✅]
- Ability to Service: [Strong ✅ / Adequate ⚪ / Stressed 🔴]

**Working Capital:**
- Working Capital: ₹[X] Cr
- Working Capital Days: [Y] days
- Trend: [Improving/Stable/Deteriorating]

**Red Flags:**
- [ ] Debt/Equity >2x
- [ ] Current Ratio <1.0 (liquidity crisis)
- [ ] Interest Coverage <2x (struggling to pay interest)
- [ ] Increasing debt + declining revenue (dangerous)
- [ ] Contingent liabilities >50% of net worth

**Financial Stability Score:** [XX]/100
\\\`\\\`\\\`

#### 3. Growth Trajectory (3-Year View):

\\\`\\\`\\\`
**Historical Performance:**

| Period | Revenue (₹Cr) | Rev Growth | EBITDA (₹Cr) | PAT (₹Cr) | PAT Growth | OPM | NPM |
|--------|---------------|-----------|--------------|-----------|------------|-----|-----|
| FY24 | [X] | [+/-Y]% | [Z] | [A] | [+/-B]% | [C]% | [D]% |
| FY23 | [X] | [+/-Y]% | [Z] | [A] | [+/-B]% | [C]% | [D]% |
| FY22 | [X] | [+/-Y]% | [Z] | [A] | [+/-B]% | [C]% | [D]% |
| FY21 | [X] | [+/-Y]% | [Z] | [A] | [+/-B]% | [C]% | [D]% |

**3-Year CAGR:**
- Revenue: [X]% (Sector: [Y]% → [Ahead/Behind] by [Z]%)
- EBITDA: [X]% (Sector: [Y]% → [Ahead/Behind] by [Z]%)
- PAT: [X]% (Sector: [Y]% → [Ahead/Behind] by [Z]%)

**Margin Trend:**
- Operating Margin: [Expanding ✅ / Stable ⚪ / Contracting 🔴]
  └─ FY24: [X]% vs FY21: [Y]% ([Direction])
- Net Margin: [Same analysis]
  └─ FY24: [X]% vs FY21: [Y]% ([Direction])

**Growth Quality:**
✅ **Healthy Growth**: Revenue & Profit growing, margins stable/expanding
⚠️ **Volume Growth**: Revenue growing but margin compression
🔴 **Declining**: Revenue/Profit declining

**{stockName} Growth:** [Assessment]
\\\`\\\`\\\`

#### 4. Earnings Quality:

\\\`\\\`\\\`
**Cash Flow Reality Check:**

| Metric | FY24 | FY23 | FY22 | Assessment |
|--------|------|------|------|------------|
| Operating Cash Flow | ₹[X] Cr | ₹[Y] Cr | ₹[Z] Cr | [Trend] |
| Net Profit (PAT) | ₹[X] Cr | ₹[Y] Cr | ₹[Z] Cr | [Trend] |
| OCF / PAT Ratio | [X.XX] | [Y.YY] | [Z.ZZ] | [✅ >1.0 / ⚠️ 0.7-1.0 / 🔴 <0.7] |
| Free Cash Flow | ₹[X] Cr | ₹[Y] Cr | ₹[Z] Cr | [Available for dividends/debt] |
| Capex | ₹[X] Cr | ₹[Y] Cr | ₹[Z] Cr | [Growth vs Maintenance] |

**Working Capital Efficiency:**
- Receivables Days: [X] days ([↑ 🔴 / ↓ ✅ / → ⚪])
- Inventory Days: [Y] days ([↑ 🔴 / ↓ ✅ / → ⚪])
- Payables Days: [Z] days ([Increasing is good for cash])
- Cash Conversion Cycle: [A] days ([Lower is better])

**Quality Red Flags:**
- [ ] OCF/PAT <0.7 consistently (profit not turning to cash)
- [ ] Increasing receivables (payment delays, collection issues)
- [ ] Increasing inventory (slow-moving stock, demand issue)
- [ ] Frequent accounting policy changes
- [ ] Contingent liabilities >25% of net worth
- [ ] Related party transactions >15% of revenue

**Earnings Quality Score:** [✅ High / ⚪ Medium / 🔴 Low]
\\\`\\\`\\\`

#### 5. Returns & Profitability:

\\\`\\\`\\\`
**Return Metrics:**

| Metric | Latest | 3Y Average | Sector Avg | Status |
|--------|--------|-----------|------------|--------|
| ROE (Return on Equity) | [X]% | [Y]% | [Z]% | [✅ >20% / ⚪ 15-20% / ⚠️ 10-15% / 🔴 <10%] |
| ROCE (Return on Capital) | [X]% | [Y]% | [Z]% | [✅ >18% / ⚪ 12-18% / ⚠️ 8-12% / 🔴 <8%] |
| ROA (Return on Assets) | [X]% | [Y]% | [Z]% | [Efficiency metric] |
| Asset Turnover | [X.X]x | [Y.Y]x | [Z.Z]x | [Asset utilization] |

**DuPont Analysis (ROE Breakdown):**
ROE = Net Margin × Asset Turnover × Equity Multiplier
[X]% = [Y]% × [Z.Z] × [A.A]

Driver: [Margin-driven / Asset-efficiency / Leverage-driven]

**Profitability Assessment:**
✅ **Excellent**: ROE >20%, ROCE >18%, above sector
⚪ **Good**: ROE 15-20%, ROCE 12-18%, in-line with sector
⚠️ **Moderate**: ROE 10-15%, ROCE 8-12%, below sector
🔴 **Poor**: ROE <10%, ROCE <8%, significantly below sector

**{stockName} Returns:** [Assessment]
\\\`\\\`\\\`

#### 6. Peer Comparison:

\\\`\\\`\\\`
**Identify Comparable Companies:**
[List 3-5 peers with similar business model, market cap range]

Peer 1: [Company Name] ([TICKER])
Peer 2: [Company Name] ([TICKER])
Peer 3: [Company Name] ([TICKER])
Peer 4: [Company Name] ([TICKER]) [if applicable]

**Comparative Analysis:**

| Metric | {stockName} | Peer 1 | Peer 2 | Peer 3 | Sector Avg | Rank |
|--------|-------------|--------|--------|--------|------------|------|
| Market Cap (₹Cr) | [X] | [Y] | [Z] | [A] | - | [1-4] |
| P/E Ratio | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [B.B]x | [1-4] |
| P/B Ratio | [X.X]x | [Y.Y]x | [Z.Z]x | [A.A]x | [B.B]x | [1-4] |
| Revenue Growth (3Y) | [X]% | [Y]% | [Z]% | [A]% | [B]% | [1-4] |
| PAT Growth (3Y) | [X]% | [Y]% | [Z]% | [A]% | [B]% | [1-4] |
| ROE | [X]% | [Y]% | [Z]% | [A]% | [B]% | [1-4] |
| ROCE | [X]% | [Y]% | [Z]% | [A]% | [B]% | [1-4] |
| Debt/Equity | [X.X] | [Y.Y] | [Z.Z] | [A.A] | [B.B] | [1-4] |
| OPM | [X]% | [Y]% | [Z]% | [A]% | [B]% | [1-4] |
| Dividend Yield | [X]% | [Y]% | [Z]% | [A]% | [B]% | [1-4] |

**Peer Position:**
- Overall Rank: [1st/2nd/3rd/4th] among peers
- Classification: [LEADER / MID-TIER / LAGGARD]
- Strengths vs Peers: [Specific advantages]
- Weaknesses vs Peers: [Specific disadvantages]

**Key Differentiator:**
[What makes {stockName} better/worse than peers? Why would investor choose this over alternatives?]

**Relative Valuation:**
- {stockName} trades at [X]% [premium/discount] to peer average P/E
- Justified by: [Superior/Inferior] [growth/margins/returns/quality]
- Assessment: [Fairly valued/Undervalued/Overvalued] relative to peers
\\\`\\\`\\\`

### Fundamental Health Scorecard:

\\\`\\\`\\\`
**Component Scores:**

| Dimension | Score /100 | Weight | Weighted | Grade |
|-----------|-----------|--------|----------|-------|
| Valuation | [XX] | 20% | [X.X] | [A/B/C/D] |
| Financial Stability | [XX] | 25% | [X.X] | [A/B/C/D] |
| Growth Trajectory | [XX] | 20% | [X.X] | [A/B/C/D] |
| Earnings Quality | [XX] | 15% | [X.X] | [A/B/C/D] |
| Returns/Profitability | [XX] | 15% | [X.X] | [A/B/C/D] |
| Peer Comparison | [XX] | 5% | [X.X] | [A/B/C/D] |
|-----------|-----------|--------|----------|-------|
| **TOTAL FUNDAMENTAL SCORE** | | **100%** | **[XX.X]** | **[A/B/C/D]** |

**Grading:**
85-100 (A): 🟢🟢 Excellent fundamentals
70-84 (B): 🟢 Strong fundamentals
55-69 (C): ⚪ Adequate fundamentals
40-54 (D): 🔴 Weak fundamentals
<40 (F): 🔴🔴 Poor fundamentals - Avoid

**{stockName} Fundamental Grade:** [X]/100 = [Letter Grade]
\\\`\\\`\\\`

### Fair Value Estimation:

\\\`\\\`\\\`
**Multiple Valuation Approaches:**

1. **P/E Based Fair Value:**
   - {stockName} TTM EPS: ₹[X]
   - Sector Median P/E: [Y.Y]x
   - Fair Value = EPS × Sector P/E = ₹[X] × [Y.Y] = ₹[CALC]

2. **P/B Based Fair Value:**
   - {stockName} Book Value/Share: ₹[X]
   - Sector Median P/B: [Y.Y]x
   - Fair Value = BVPS × Sector P/B = ₹[X] × [Y.Y] = ₹[CALC]

3. **Peer Average Method:**
   - Peer 1 Mcap/Revenue multiple: [X.X]x
   - Peer 2 Mcap/Revenue multiple: [Y.Y]x
   - Average: [Z.Z]x
   - {stockName} Revenue: ₹[A] Cr
   - Implied Mcap: ₹[CALC] Cr
   - Fair Value/Share: ₹[CALC]

4. **Analyst Consensus** (if available):
   - Average Target Price: ₹[X]
   - Range: ₹[LOW] - ₹[HIGH]

**Conservative Fair Value:** ₹[LOWEST of above methods]
**Base Fair Value:** ₹[MEDIAN of above methods]
**Optimistic Fair Value:** ₹[HIGHEST of above methods]

**Working Fair Value: ₹[BASE]**

**Price vs Fair Value:**
Current Price: ₹{entry}
Fair Value: ₹[BASE]
Variance: [+/-X]% ([Undervalued/Overvalued])

**Target Price Validation:**
Your Target: ₹{target}
Fair Value: ₹[BASE]
Assessment: Target is [Below/At/Above] fair value
Achievability: [✅ Reasonable / ⚠️ Aggressive / 🔴 Unrealistic]
\\\`\\\`\\\`

### Fundamental Verdict:

\\\`\\\`\\\`
**Overall Fundamental Rating:** [🟢🟢 Excellent / 🟢 Strong / ⚪ Moderate / 🔴 Weak / 🔴🔴 Poor]

**Top 3 Strengths:**
1. [Specific strength with data]
2. [Specific strength with data]
3. [Specific strength with data]

**Top 3 Weaknesses:**
1. [Specific weakness with data]
2. [Specific weakness with data]
3. [Specific weakness with data]

**Support for {verdict} at ₹{entry} → ₹{target}?**

\${Math.abs(parseFloat('{score}')) < 0.30 ? \`
**Critical Assessment for Weak Signal ({score}):**

[✅ YES - Override weak technicals]
Reasoning: Fundamentals are strong enough (Score >70) to provide conviction that technicals currently miss. [Specific reasons why fundamentals justify entry despite weak technical setup]

[⚠️ CONDITIONAL - Reduce position]
Reasoning: Fundamentals are adequate (Score 50-70) but not compelling enough to fully override weak technicals. Proceed with [X]% position size vs standard.

[❌ NO - Skip trade]
Reasoning: Fundamentals are weak (Score <50), confirming that weak technical signal correctly reflects poor setup. No reason to force this trade.
\` : \`
**Validation for \${Math.abs(parseFloat('{score}')) > 0.50 ? 'Strong' : 'Moderate'} Signal ({score}):**

[✅ YES - Fundamentals confirm]
Reasoning: Strong fundamentals (Score >70) validate the technical signal. Trade with confidence.

[⚠️ MIXED - Some concerns]
Reasoning: Moderate fundamentals (Score 50-70) neither strongly confirm nor contradict. Proceed but monitor.

[❌ NO - Fundamentals contradict]
Reasoning: Weak fundamentals (Score <50) contradict technical signal. Reconsider trade.
\`}

**Final Fundamental Call:** [Specific recommendation]

**Key Insight for Trade Decision:**
[2-3 sentences summarizing whether fundamentals make this a good trade at current levels, considering entry ₹{entry}, target ₹{target}, and stop ₹{stopLoss}]
\\\`\\\`\\\`

---

## SECTION 4: SECTOR & MARKET CONTEXT

### Search Strategy:

\\\`\\\`\\\`
Query 1: "{stockName} sector [SECTOR_NAME] India 2025"
Query 2: "Nifty [SECTOR] index performance trend"
Query 3: "Nifty 50 Sensex market trend February 2025"
Query 4: "FII DII flows India latest"
Query 5: "India VIX volatility index current"
Query 6: "Nifty advance decline ratio breadth"
Query 7: "USD INR exchange rate India"
Query 8: "RBI policy interest rates India 2025"
\\\`\\\`\\\`

### Analysis Framework:

#### 1. Sector Deep Dive:

\\\`\\\`\\\`
**Sector Classification:**
- Primary Sector: [AUTO-DETECT - e.g., Healthcare, IT, Auto, Banking]
- Sub-Sector: [Specific niche - e.g., Medical Devices, Pharma, Hospitals]
- Market Position: [{stockName} is Large-cap/Mid-cap/Small-cap in this sector]

**Sector Performance:**

| Timeframe | Sector Index | Nifty 50 | Relative Performance | Status |
|-----------|--------------|----------|---------------------|--------|
| 1 Week | [+/-X]% | [+/-Y]% | [+/-Z]% | [🟢 Outperform / ⚪ In-line / 🔴 Underperform] |
| 2 Weeks | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| 1 Month | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| 3 Months | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| 6 Months | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |
| YTD 2025 | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |

**Sector Momentum Assessment:**
- Short-term (1-2W): [Hot 🔥 / Warm / Cool / Cold ❄️]
- Medium-term (1-3M): [Same]
- Relative Strength: [Leading sector ✅ / In-line ⚪ / Lagging 🔴]

**{stockName} vs Sector:**

| Timeframe | {stockName} | Sector Index | Outperformance | Status |
|-----------|-------------|--------------|----------------|--------|
| 1 Month | [+/-X]% | [+/-Y]% | [+/-Z]% | [Leader/In-line/Laggard] |
| 3 Months | [+/-X]% | [+/-Y]% | [+/-Z]% | [Same] |

**Position:** [Strong Leader / Leader / In-line / Laggard / Weak Laggard]
**Interpretation:** [What this means for ₹{entry} → ₹{target} trade]
\\\`\\\`\\\`

**Sector Outlook & Themes:**
\\\`\\\`\\\`
Current Sector Drivers:
├─ Positive Themes:
│  ├─ [Policy support, demand growth, export opportunity]
│  ├─ [Technological advancement, PLI benefits]
│  └─ [Specific sector tailwinds]
│
├─ Challenges:
│  ├─ [Regulatory hurdles, competition, margin pressure]
│  ├─ [Import dependency, commodity costs]
│  └─ [Specific sector headwinds]
│
└─ Net Outlook: [🟢 Bullish / ⚪ Neutral / 🔴 Bearish]

**Sector Positioning:**
- In favor: [Yes/No - Is smart money rotating INTO this sector?]
- Institutional interest: [Increasing/Stable/Decreasing]
- Top performers: [List 2-3 best stocks in sector recently]
- Laggards: [List 2-3 worst stocks in sector]

**Where does {stockName} fit:** [Context within sector dynamics]
\\\`\\\`\\\`

#### 2. Broader Market Analysis:

\\\`\\\`\\\`
**Market Trend Assessment:**

| Index | Current | 20 DMA | 50 DMA | 200 DMA | Position | Trend |
|-------|---------|--------|--------|---------|----------|-------|
| Nifty 50 | [X] | [Y] | [Z] | [A] | [Above all/Mixed/Below] | [🟢 Bull / ⚪ Neutral / 🔴 Bear] |
| Nifty Midcap 100 | [X] | [Y] | [Z] | [A] | [Same] | [Same] |
| Nifty Smallcap 100 | [X] | [Y] | [Z] | [A] | [Same] | [Same] |
| Nifty [Sector] | [X] | [Y] | [Z] | [A] | [Same] | [Same] |

**Market Regime Classification:**
├─ STRONG BULL: All indices >20/50/200 DMA, rising
├─ BULL: Above 50/200 DMA, may pullback to 20 DMA
├─ SIDEWAYS: Choppy, oscillating around 50 DMA
├─ BEAR: Below 50 DMA, testing 200 DMA
└─ STRONG BEAR: Below all DMAs, making lower lows

**Current Regime:** [Classification]
**Implication for Trade:** [How this affects success probability]

**Market Breadth:**

| Indicator | Value | Signal |
|-----------|-------|--------|
| Advance/Decline Ratio | [X]:[Y] | [🟢 Bullish >1.5 / ⚪ Neutral 0.7-1.5 / 🔴 Bearish <0.7] |
| % Stocks >20 DMA | [X]% | [🟢 >60% / ⚪ 40-60% / 🔴 <40%] |
| % Stocks >50 DMA | [X]% | [🟢 >55% / ⚪ 35-55% / 🔴 <35%] |
| % Stocks >200 DMA | [X]% | [🟢 >50% / ⚪ 30-50% / 🔴 <30%] |
| New 52W Highs | [X] stocks | [Strength] |
| New 52W Lows | [Y] stocks | [Weakness] |
| High-Low Ratio | [X]:[Y] | [🟢 >2 / ⚪ 0.5-2 / 🔴 <0.5] |

**Breadth Assessment:** [Healthy 🟢 / Mixed ⚪ / Weak 🔴]

**India VIX:**

Current VIX: [X]
20-Day Average: [Y]
Trend: [Falling ✅ / Stable ⚪ / Rising 🔴]

VIX Zones:
├─ <12: Very low volatility (complacency risk)
├─ 12-15: Low volatility (favorable for trades)
├─ 15-20: Normal volatility (manageable)
├─ 20-25: Elevated (caution)
├─ 25-30: High (risky)
└─ >30: Extreme fear (avoid new trades)

**Current VIX [X]:** [Assessment for trade timing]
\\\`\\\`\\\`

#### 3. Institutional Flows (FII/DII):

\\\`\\\`\\\`
**Money Flow Analysis:**

| Period | FII (₹ Cr) | DII (₹ Cr) | Net Flow (₹ Cr) | Market Impact |
|--------|-----------|-----------|----------------|---------------|
| Last Day | [+/-X] | [+/-Y] | [+/-Z] | [Supportive/Neutral/Pressure] |
| Last Week | [+/-X] | [+/-Y] | [+/-Z] | [Same] |
| Last Month | [+/-X] | [+/-Y] | [+/-Z] | [Same] |
| YTD 2025 | [+/-X] | [+/-Y] | [+/-Z] | [Same] |

**Flow Interpretation:**

STRONG BUYING (Net >₹5,000 Cr/month):
└─ 🟢🟢 Very supportive for markets and stocks

MODERATE BUYING (Net ₹2,000-5,000 Cr/month):
└─ 🟢 Supportive backdrop

BALANCED (Net ±₹2,000 Cr/month):
└─ ⚪ Stock-specific factors dominate

MODERATE SELLING (Net -₹2,000 to -₹5,000 Cr/month):
└─ 🔴 Headwind for markets

STRONG SELLING (Net <-₹5,000 Cr/month):
└─ 🔴🔴 Challenging environment

**Current Status:** [Assessment]

**Sector-Specific Flows (if available):**
- FII in [Sector]: [Buying/Selling/Neutral]
- DII in [Sector]: [Same]
- Net Impact on {stockName}: [Favorable/Unfavorable]
\\\`\\\`\\\`

#### 4. Macroeconomic Context:

\\\`\\\`\\\`
**Key Macro Indicators:**

| Factor | Current | Previous | Trend | Impact on {stockName} |
|--------|---------|----------|-------|----------------------|
| RBI Repo Rate | [X]% | [Y]% | [↑/↓/→] | [Cost of capital, demand] |
| CPI Inflation | [X]% | [Y]% | [↑/↓/→] | [Input costs, margins] |
| IIP (Industrial Production) | [X]% | [Y]% | [↑/↓/→] | [Demand proxy] |
| GDP Growth (latest) | [X]% | [Y]% | [↑/↓/→] | [Overall economy] |
| USD-INR Exchange Rate | ₹[X] | ₹[Y] | [↑/↓/→] | [🟢 Export benefit / 🔴 Import cost] |
| Crude Oil (Brent) | $[X] | $[Y] | [↑/↓/→] | [Input costs if applicable] |
| 10Y Govt Bond Yield | [X]% | [Y]% | [↑/↓/→] | [Discount rates, equity flows] |

**Macro Environment:** [🟢 Favorable / ⚪ Mixed / 🔴 Challenging]

**Specific Relevance to {stockName}:**
[Identify 2-3 most relevant macro factors and explain impact]

Example:
- USD-INR at ₹83: [Positive for exports, negative for imports]
- Crude at $75: [Impact on polymer/chemical input costs]
- Interest rates: [Impact on working capital costs]
\\\`\\\`\\\`

### Market Context Scorecard:

\\\`\\\`\\\`
**Component Scores:**

| Dimension | Score /100 | Weight | Weighted | Grade |
|-----------|-----------|--------|----------|-------|
| Sector Trend & Momentum | [XX] | 30% | [X.X] | [A/B/C/D] |
| Market Regime & Breadth | [XX] | 25% | [X.X] | [A/B/C/D] |
| Institutional Flows | [XX] | 20% | [X.X] | [A/B/C/D] |
| Volatility (VIX) | [XX] | 15% | [X.X] | [A/B/C/D] |
| Macroeconomic Factors | [XX] | 10% | [X.X] | [A/B/C/D] |
|-----------|-----------|--------|----------|-------|
| **TOTAL MARKET CONTEXT SCORE** | | **100%** | **[XX.X]** | **[A/B/C/D]** |

**Interpretation:**
75-100: 🟢 Very Favorable - Tailwinds for trade
60-74: 🟢 Favorable - Supportive environment
45-59: ⚪ Neutral - Mixed signals
30-44: 🔴 Unfavorable - Headwinds present
<30: 🔴🔴 Very Unfavorable - Strong headwinds

**{stockName} Market Context:** [XX]/100 = [Rating]
\\\`\\\`\\\`

### Market Verdict:

\\\`\\\`\\\`
**Overall Market/Sector Assessment:** [Rating with emoji]

**Key Findings:**
1. **Sector Position:** [Leading/In-line/Lagging]
2. **Market Regime:** [Bull/Sideways/Bear - implications]
3. **Flow Status:** [Supportive/Neutral/Against]
4. **Timing:** [Good/Mixed/Poor time to initiate trade]

**Timing Assessment for ₹{entry} → ₹{target}:**

\${Math.abs(parseFloat('{score}')) < 0.30 ? \`
With weak technical signal ({score}), market context is CRITICAL:

[✅ GOOD TIMING - Score >70]
Despite weak technicals, favorable market/sector can carry the trade. Strong tailwinds compensate for technical weakness.

[⚠️ MIXED TIMING - Score 45-70]  
Neutral context means stock must perform on own merit. No help from market but no strong headwind either.

[🔴 POOR TIMING - Score <45]
Weak technicals + unfavorable market = SKIP. Fighting both technical AND fundamental headwinds.
\` : \`
Market context \${Math.abs(parseFloat('{score}')) > 0.50 ? 'confirms or challenges strong signal' : 'provides additional conviction or concern'}:

[✅ ALIGNED]
Market/sector support \${'{verdict}'} signal. Trade with confidence.

[⚪ NEUTRAL]
Market neither helps nor hurts. Stock-specific factors will dominate.

[🔴 CONFLICTING]
Market/sector work against signal. Reconsider or reduce size.
\`}

**Final Market Context Call:** [Specific assessment]

**Reasoning:** [2-3 sentences on whether market/sector environment makes this a good time to trade {stockName}]
\\\`\\\`\\\`

---

## SECTION 5: INSTITUTIONAL & SMART MONEY ANALYSIS

### Search Strategy:

\\\`\\\`\\\`
Query 1: "{stockName} shareholding pattern latest quarter"
Query 2: "{stockName} promoter holding trend FII DII"
Query 3: "{ticker} pledged shares promoter pledge"
Query 4: "{stockName} bulk deals NSE BSE recent"
Query 5: "{stockName} insider trading director buying selling"
Query 6: "{stockName} mutual fund holdings increase decrease"
Query 7: "{stockName} institutional investors list"
\\\`\\\`\\\`

### Analysis Framework:

#### 1. Promoter Activity Analysis:

\\\`\\\`\\\`
**Promoter Holding Trend:**

| Quarter | Promoter Holding % | QoQ Change | Pledged Shares % | QoQ Change |
|---------|-------------------|------------|------------------|------------|
| Q3 FY25 (Dec'24) | [XX.XX]% | [+/-X.XX]% | [YY.YY]% | [+/-Y.YY]% |
| Q2 FY25 (Sep'24) | [XX.XX]% | [+/-X.XX]% | [YY.YY]% | [+/-Y.YY]% |
| Q1 FY25 (Jun'24) | [XX.XX]% | [+/-X.XX]% | [YY.YY]% | [+/-Y.YY]% |
| Q4 FY24 (Mar'24) | [XX.XX]% | [+/-X.XX]% | [YY.YY]% | [+/-Y.YY]% |

**4-Quarter Trends:**
- Holding: [🟢 Increasing / ⚪ Stable / 🔴 Decreasing]
- Pledge: [✅ Decreasing / ⚪ Stable / 🔴 Increasing]

**Promoter Confidence Signal:**

Holding Trend + Pledge Trend = Overall Signal
├─ Increasing + Decreasing Pledge = 🟢🟢 Very Strong (best case)
├─ Stable + Low/Decreasing Pledge = 🟢 Strong
├─ Stable + Stable Pledge = ⚪ Neutral
├─ Decreasing + Stable Pledge = 🔴 Weak
└─ Decreasing + Increasing Pledge = 🔴🔴 Very Weak (worst case)

**{stockName} Promoter Signal:** [Assessment]

**Pledge Risk Assessment:**

Current Pledge: [XX.XX]% of promoter holding

Risk Zones:
├─ 0-25%: ✅ Low Risk - Comfortable position
├─ 25-50%: ⚠️ Moderate Risk - Monitor for increases
├─ 50-75%: 🔴 High Risk - Concerning, may face margin calls
└─ 75-100%: 🔴🔴 Critical Risk - Severe stress, control risk

**Risk Level:** [Assessment]
**Trend:** [Improving ✅ / Stable ⚪ / Deteriorating 🔴]

**Red Flags:**
- [ ] Promoter holding <30% (losing control)
- [ ] Pledge >75% (margin call risk)
- [ ] Rapidly increasing pledge (financial stress)
- [ ] Promoter selling during price rise (lack of confidence)

**{stockName} Promoter Quality:** [🟢 Strong / ⚪ Adequate / 🔴 Concerning]
\\\`\\\`\\\`

#### 2. Institutional Holdings Analysis:

\\\`\\\`\\\`
**FII/DII/MF Holdings:**

| Category | Latest Q | Previous Q | 2Q Ago | 3Q Ago | Trend (4Q) | Net Change |
|----------|----------|-----------|--------|--------|-----------|------------|
| FII | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [↑/↓/→] | [+/-B.BB]% |
| DII | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [↑/↓/→] | [+/-B.BB]% |
| Mutual Funds | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [↑/↓/→] | [+/-B.BB]% |
| Insurance | [X.XX]% | [Y.YY]% | [Z.ZZ]% | [A.AA]% | [↑/↓/→] | [+/-B.BB]% |
| **Total Institutional** | [XX.XX]% | [YY.YY]% | [ZZ.ZZ]% | [AA.AA]% | [↑/↓/→] | [+/-BB.BB]% |

**Institutional Activity Signal:**

ALL increasing = 🟢🟢 Strong Accumulation
FII + DII both increasing = 🟢 Accumulation  
Mixed (some in, some out) = ⚪ Neutral
FII + DII both decreasing = 🔴 Distribution
ALL decreasing = 🔴🔴 Strong Distribution

**{stockName} Institutional Signal:** [Assessment]

**Significant Changes (>1% stake change in quarter):**
- [Institution Name]: [+/-X.XX]% - [New entry/Exit/Increased/Decreased]
- [Another if applicable]

**Key Institutional Holders (Top 5 if holding >1%):**

| Institution | Type | Holding % | Recent Change |
|-------------|------|-----------|---------------|
| [Fund/FII Name] | [MF/FII/Insurance] | [X.XX]% | [+/-Y.YY]% |
| [Name] | [Type] | [X.XX]% | [+/-Y.YY]% |
| [Name] | [Type] | [X.XX]% | [+/-Y.YY]% |

**Quality of Holders:**
- Marquee names (SBI MF, HDFC MF, etc.): [Yes/No]
- Long-term holders: [Identify if any]
- New entrants: [Identify if any - shows fresh interest]
\\\`\\\`\\\`

#### 3. Bulk & Block Deals:

\\\`\\\`\\\`
**Recent Large Transactions (Last 30 Days):**

| Date | Client Name | Type | Quantity | Avg Price | Value (₹L) | % of Equity |
|------|-------------|------|----------|-----------|------------|-------------|
| [DD-MMM] | [Buyer/Seller Name] | Buy/Sell | [X] | ₹[Y] | [Z] | [A]% |
| [DD-MMM] | [Same] | [Same] | [Same] | [Same] | [Same] | [Same] |

**Analysis:**
- Total Bulk Buys (30D): ₹[X] Lakhs
- Total Bulk Sells (30D): ₹[Y] Lakhs
- Net Position: [₹Z Lakhs] [Buying/Selling] pressure

**Notable Participants:**
- [Identify well-known investors, institutions, or operators]
- [Pattern: One-time or sustained activity?]

**Interpretation:**
🟢 Sustained buying by known long-term investors = Positive
⚪ Routine trading, no clear pattern = Neutral
🔴 Sustained selling or operator involvement = Negative

**{stockName} Bulk Deal Signal:** [🟢 Positive / ⚪ Neutral / 🔴 Negative]
\\\`\\\`\\\`

#### 4. Insider Transactions:

\\\`\\\`\\\`
**Director/Insider Trading (Last 90 Days):**

| Date | Name | Designation | Transaction | Shares | Price (₹) | Value (₹L) |
|------|------|-------------|-------------|--------|-----------|------------|
| [DD-MMM] | [Director Name] | [CMD/MD/CFO/etc] | Buy/Sell | [X] | [Y] | [Z] |
| [DD-MMM] | [Same] | [Same] | [Same] | [Same] | [Same] | [Same] |

**Summary:**
- Total Insider Buying: ₹[X] Lakhs ([Y] transactions)
- Total Insider Selling: ₹[Z] Lakhs ([A] transactions)
- Net Signal: [Bullish 🟢 / Neutral ⚪ / Bearish 🔴]

**Context Assessment:**

BULLISH SIGNALS:
├─ Directors buying in open market (conviction)
├─ Multiple directors buying (consensus)
├─ Buying during price decline (value opportunity)
└─ Small/no selling activity

NEUTRAL:
├─ No significant transactions
├─ Routine ESOP exercises

BEARISH SIGNALS:
├─ Directors selling (especially founders)
├─ Selling during price rise (distribution)
├─ Multiple insiders selling (exit)
└─ Large quantum vs typical trading

**{stockName} Insider Signal:** [Assessment with reasoning]
\\\`\\\`\\\`

### Smart Money Scorecard:

\\\`\\\`\\\`
**Component Scores:**

| Dimension | Assessment | Score /100 | Weight | Weighted |
|-----------|-----------|-----------|--------|----------|
| Promoter Holding Trend | [↑/→/↓] | [XX] | 25% | [X.X] |
| Promoter Pledge Status | [Low/Med/High risk] | [XX] | 20% | [X.X] |
| FII Activity | [Buying/Neutral/Selling] | [XX] | 20% | [X.X] |
| DII/MF Activity | [Buying/Neutral/Selling] | [XX] | 15% | [X.X] |
| Bulk Deals | [Positive/Neutral/Negative] | [XX] | 10% | [X.X] |
| Insider Transactions | [Buying/Neutral/Selling] | [XX] | 10% | [X.X] |
|-----------|-----------|-----------|--------|----------|
| **TOTAL SMART MONEY SCORE** | | | **100%** | **[XX.X]** |

**Interpretation:**
75-100: 🟢🟢 Strong Accumulation - Smart money bullish
60-74: 🟢 Accumulation - Net positive positioning
40-59: ⚪ Neutral/Mixed - No clear smart money view
25-39: 🔴 Distribution - Smart money reducing
0-24: 🔴🔴 Strong Distribution - Smart money exiting

**{stockName} Smart Money Status:** [XX]/100 = [Rating]
\\\`\\\`\\\`

### Smart Money Verdict:

\\\`\\\`\\\`
**Overall Assessment:** [Strong Accumulation 🟢🟢 / Accumulation 🟢 / Neutral ⚪ / Distribution 🔴 / Strong Distribution 🔴🔴]

**Key Findings:**
1. **Promoters:** [Increasing with low pledge / Stable / Decreasing or high pledge]
2. **Institutions:** [Accumulating / Stable / Distributing]
3. **Insider Activity:** [Buying / Quiet / Selling]

**Support for {verdict} at ₹{entry}?**

\${Math.abs(parseFloat('{score}')) < 0.30 ? \`
With weak technical signal ({score}), smart money activity is CRUCIAL:

[✅ YES - Strong Support]
Score >70: Smart money is accumulating despite weak price action. They see value that technicals miss. This can override weak signal.

[⚠️ MIXED - Neutral]
Score 40-70: No strong smart money view. Proceed with caution and reduced size.

[❌ NO - Against Trade]
Score <40: Smart money is exiting. Weak technicals + smart money distribution = clear SKIP.
\` : \`
Smart money activity validates or challenges technical signal:

[✅ ALIGNED]
Score >65: Smart money supports \${'{verdict}'}. Trade with confidence.

[⚪ NEUTRAL]
Score 35-65: Mixed signals. Stock-specific factors will decide.

[🔴 CONFLICTING]
Score <35: Smart money contradicts technical. Reconsider trade.
\`}

**Final Smart Money Call:** [Specific assessment]

**Critical Insight:**
[1-2 sentences on most important smart money finding and what it means for the trade]

**Red Flags (if any):**
- [List critical concerns requiring immediate skip]

**Green Flags (if any):**
- [List strong positives supporting trade]
\\\`\\\`\\\`

---

## SECTION 6: RISK ANALYSIS & FINAL VERDICT

### Comprehensive Risk Assessment:

#### 1. Technical Risks:

\\\`\\\`\\\`
**Signal Weakness:** Score {score}

Risk Assessment:
\${Math.abs(parseFloat('{score}')) < 0.15 ? \`
🔴🔴 CRITICAL RISK - Score essentially neutral
- Indicators completely conflicted (50-50 split)
- NO directional conviction from technicals
- Very high whipsaw probability
- Could easily violate ₹{stopLoss} OR miss ₹{target}
- Expected outcome: Sideways drift, frustration
\` : Math.abs(parseFloat('{score}')) < 0.30 ? \`
🔴 HIGH RISK - Weak conviction
- Indicators barely aligned
- Marginal directional bias
- Whipsaw probability elevated
- Setup could easily fail
\` : Math.abs(parseFloat('{score}')) < 0.50 ? \`
⚠️ MODERATE RISK - Decent but not strong
- Indicators reasonably aligned
- Some conviction present
- Normal failure probability
\` : \`
✅ LOW RISK - Strong conviction
- Indicators well-aligned
- High directional confidence
- Lower failure probability
\`}

**Stop Loss Adequacy:**
- Distance to Stop: ₹\${Math.abs(parseFloat('{entry}') - parseFloat('{stopLoss}')).toFixed(2)} ([X]%)
- ATR-based assessment: [Too tight / Adequate / Conservative]
- Circuit risk: [Can stop execute or gap risk?]
\\\`\\\`\\\`

#### 2. Liquidity & Execution Risks:

\\\`\\\`\\\`
[From Section 1 findings]

**Execution Risk Level:** [From liquidity verdict]
- Slippage Estimate: ±[X]%
- Circuit Hit Risk: [Low/Medium/High]
- Order Size Impact: [Minimal/Moderate/Significant]

**Position Entry Risk:**
- Recommended order type: [Market/Limit]
- Staging required: [Yes if illiquid / No if liquid]

**Position Exit Risk:**
- Normal exit: [Clean/Challenging]
- Emergency exit: [Feasible/Difficult]
- Stop loss execution: [Reliable/Uncertain]
\\\`\\\`\\\`

#### 3. Fundamental & Business Risks:

\\\`\\\`\\\`
[From Section 3 findings]

**Company-Specific Risks:**
- Debt Stress: [Low/Medium/High based on D/E ratio]
- Earnings Quality: [Strong/Adequate/Weak based on OCF]
- Competitive Position: [Secure/Vulnerable]
- Management Risk: [Low/Medium/High based on governance]

**Specific Concerns for {stockName}:**
1. [Risk 1 with severity]
2. [Risk 2 with severity]
3. [Risk 3 with severity]

**Fundamental Risk Level:** [Low ✅ / Medium ⚠️ / High 🔴]
\\\`\\\`\\\`

#### 4. Market & Sector Risks:

\\\`\\\`\\\`
[From Section 4 findings]

**Systematic Risks:**
- Market Correction Risk: [VIX, breadth, valuation based]
- Sector Rotation Risk: [Is money leaving sector?]
- FII Outflow Risk: [Current flow status]

**Beta-Adjusted Risk:**
- {stockName} Beta: [X.X]
- If Nifty falls 5%, {stockName} likely falls: [X]%
- Stop loss at -[Y]% may not protect in market crash

**Market Risk Level:** [Low ✅ / Medium ⚠️ / High 🔴]
\\\`\\\`\\\`

#### 5. Event & News Risks:

\\\`\\\`\\\`
[From Section 2 findings]

**Upcoming Binary Events:**
- Earnings (Q[X] FY[YY]): [X] days away
  Risk: [Low/Medium/High based on historical volatility]
- Other events: [List with risk assessment]

**Surprise Risk:**
- Positive surprise probability: [X]%
- Negative surprise probability: [Y]%
- Based on: [Recent trends, sector dynamics]

**Event Risk Level:** [Low ✅ / Medium ⚠️ / High 🔴]
\\\`\\\`\\\`

### Risk Probability Matrix:

\\\`\\\`\\\`
**Prioritized Risk Assessment:**

| Risk | Probability | Impact | Severity | Priority |
|------|-------------|--------|----------|----------|
| [Most likely risk] | [H/M/L] | [-X%] | [Critical/High/Med] | 🔴 1 |
| [Second risk] | [H/M/L] | [-Y%] | [Critical/High/Med] | [2] |
| [Third risk] | [H/M/L] | [-Z%] | [High/Med/Low] | [3] |

**Top 3 Risks:**

1. **[RISK NAME]** - Probability: [X]%, Impact: [Y]%
   - Description: [What could go wrong]
   - Trigger: [What causes this]
   - Mitigation: [How to protect]
   - Early Warning: [What to watch]

2. **[RISK NAME]** - Probability: [X]%, Impact: [Y]%
   - [Same structure]

3. **[RISK NAME]** - Probability: [X]%, Impact: [Y]%
   - [Same structure]
\\\`\\\`\\\`

### Supporting Factors:

\\\`\\\`\\\`
**Top 3 Positive Factors:**

1. **[FACTOR NAME]** - Strength: [High/Medium/Low]
   - Evidence: [Specific data point]
   - Impact: [How this helps hit ₹{target}]
   - Sustainability: [One-time or ongoing]
   - Contribution to thesis: [X]%

2. **[FACTOR NAME]** - Strength: [High/Medium/Low]
   - [Same structure]

3. **[FACTOR NAME]** - Strength: [High/Medium/Low]
   - [Same structure]
\\\`\\\`\\\`

### Scenario Analysis:

\\\`\\\`\\\`
**Probabilistic Outcome Assessment:**

**BASE CASE (Most Likely - [X]% Probability):**
- Description: [What probably happens]
- Price Movement: ₹{entry} → ₹[TARGET_BASE]
- Return: [+/-Y]%
- Timeline: [Z] days
- Catalysts: [What drives this]

**BULL CASE (Optimistic - [Y]% Probability):**
- Description: [Best-case scenario]
- Price Movement: ₹{entry} → ₹{target} or higher
- Return: [+A]%
- Timeline: [B] days  
- Catalysts: [Positive surprises needed]

**BEAR CASE (Pessimistic - [Z]% Probability):**
- Description: [Worst-case scenario]
- Price Movement: ₹{entry} → ₹{stopLoss} or lower
- Return: [-C]%
- Timeline: [D] days
- Catalysts: [Negative triggers]

**EXPECTED VALUE CALCULATION:**

EV = (P_Bull × Return_Bull) + (P_Base × Return_Base) + (P_Bear × Return_Bear)
EV = ([Y]% × [+A]%) + ([X]% × [+/-B]%) + ([Z]% × [-C]%)
**EV = [CALCULATED]%**

**Interpretation:**
- EV >5%: Attractive risk-reward
- EV 2-5%: Acceptable
- EV 0-2%: Marginal, better opportunities exist
- EV <0%: Negative expected value, SKIP

**{stockName} Expected Value: [X]%** → [Attractive/Acceptable/Marginal/Negative]
\\\`\\\`\\\`

---

## 🎯 FINAL CONSOLIDATED VERDICT

### Multi-Factor Scorecard:

\\\`\\\`\\\`
**Comprehensive Scoring (All Sections):**

| Dimension | Score /100 | Weight | Weighted | Grade |
|-----------|-----------|--------|----------|-------|
| Technical Strength | \${Math.abs(parseFloat('{score}')) < 0.15 ? '10-15' : Math.abs(parseFloat('{score}')) < 0.30 ? '20-35' : Math.abs(parseFloat('{score}')) < 0.50 ? '50-65' : '70-85'} | 25% | [X.XX] | [Score-based] |
| Liquidity & Execution | [XX] | 15% | [X.XX] | [From Section 1] |
| News & Sentiment | [XX] | 10% | [X.XX] | [From Section 2] |
| Fundamentals | [XX] | 25% | [X.XX] | [From Section 3] |
| Market/Sector Context | [XX] | 10% | [X.XX] | [From Section 4] |
| Smart Money Activity | [XX] | 10% | [X.XX] | [From Section 5] |
| Risk-Reward Profile | [XX] | 5% | [X.XX] | [From EV calc] |
|-----------|-----------|--------|----------|-------|
| **TOTAL WEIGHTED SCORE** | | **100%** | **[XX.XX]** | **[Overall Grade]** |
\\\`\\\`\\\`

### Decision Matrix Application:

\\\`\\\`\\\`
**Score-Based Recommendation:**

85-100: ✅ STRONG BUY - Execute with high conviction
70-84: ✅ BUY - Execute with standard position
55-69: ⚠️ CONDITIONAL BUY - Reduce size 30-50%
40-54: ⚠️ HOLD/WAIT - Better opportunities exist
25-39: 🔴 SKIP - Too many concerns
<25: 🔴🔴 STRONG SKIP - Clear avoid

**{stockName} Total Score: [XX.XX]/100**
**Preliminary Recommendation: [Based on score band]**
\\\`\\\`\\\`

### Override Rules Check:

\\\`\\\`\\\`
🔴 MANDATORY SKIP - DO NOT TRADE if ANY:
- [ ] Illiquid (Avg Daily Value <₹25L)
- [ ] Critical red flag (Fraud, SEBI action, Auditor quit)
- [ ] Promoter pledge >90%
- [ ] Debt/Equity >5x with negative cash flow
- [ ] Multiple circuit hits suggesting manipulation
- [ ] Accounting irregularities
- [ ] Expected Value <-2%

⚠️ PROCEED WITH EXTREME CAUTION if ANY:
- [ ] Promoter pledge >75%
- [ ] FII + DII both selling heavily
- [ ] Earnings in next 3 days
- [ ] VIX >25
- [ ] Major lawsuit pending verdict

**{stockName} Override Check:** [✅ PASSED / 🔴 FAILED - specific rule]

IF FAILED: Recommendation overridden to SKIP regardless of score.
\\\`\\\`\\\`

### Position Sizing Adjustment:

\\\`\\\`\\\`
**Conviction-Based Position Sizing:**

Base Position Size Guidelines:
├─ Score >85: 4-5% of portfolio (high conviction)
├─ Score 70-85: 3-4% (standard)
├─ Score 55-70: 2-3% (reduced)
├─ Score 40-55: 1-2% (minimal)
└─ Score <40: 0% (skip)

\${Math.abs(parseFloat('{score}')) < 0.30 ? \`
**Weak Signal Adjustment:**
Technical conviction is weak ({score}), so REDUCE base sizing:
- If final score >70: Use 2-3% (vs 3-4% standard)
- If final score 55-70: Use 1.5-2.5% (vs 2-3%)
- If final score 40-55: Use 0.5-1.5% (vs 1-2%)
- If final score <40: SKIP entirely
\` : ''}

**Liquidity Adjustment:**
- If Daily Value <₹50L: Further reduce by 50%
- If Circuit risk high: Cap at 1% regardless

**Final Recommended Position Size for {stockName}:**
Based on Score [XX] + Signal [{score}] + Liquidity [Status]:
→ **[X.X]% of portfolio**

In absolute terms (example ₹10L portfolio):
→ **₹[CALCULATED] investment**
\\\`\\\`\\\`

---

### FINAL RECOMMENDATION:

\\\`\\\`\\\`
┌────────────────────────────────────────────────────────────┐
│                                                             │
│  VERDICT: [✅ EXECUTE / ⚠️ EXECUTE WITH CAUTION / 🔴 SKIP]  │
│                                                             │
│  Confidence: [🟢 HIGH >70 / 🟡 MEDIUM 40-70 / 🔴 LOW <40]   │
│                                                             │
│  Position Size: [X.X]% of portfolio                        │
│                                                             │
└────────────────────────────────────────────────────────────┘
\\\`\\\`\\\`

---

### IF ✅ EXECUTE - Trade Plan:

\\\`\\\`\\\`
**Entry Strategy:**
- Entry Price: ₹{entry}
- Order Type: [Market / Limit at ₹[SPECIFIC]]
- Timing: [Immediate / Wait for [CONDITION]]
- Position Staging: [Single entry / Split into 2-3 tranches if large]

**Exit Strategy - Stop Loss:**
- Stop Loss: ₹{stopLoss} (HARD STOP - NON-NEGOTIABLE)
- Order Type: Stop-Loss Limit at ₹[SLIGHTLY BELOW]
- Risk: ₹\${Math.abs(parseFloat('{entry}') - parseFloat('{stopLoss}')).toFixed(2)} per share = [TOTAL RISK]
- If Stop Hit: Accept loss, DO NOT average down, wait [X] days before re-evaluating
- 3-Bar/3-Day Cooldown: Wait before re-entering if stopped

**Exit Strategy - Profit Targets:**
\${Math.abs(parseFloat('{score}')) < 0.30 ? \`
Given weak signal, use CONSERVATIVE profit-taking:
- Target 1: ₹[MIDPOINT between entry and target] - Book 50-60% position
- Target 2: ₹{target} - Book remaining 40-50%
- Rationale: Weak signals less likely to hit full target, take profits early
\` : \`
- Target 1: ₹[CALCULATE ~60-70% of move] - Book 40-50% position
- Target 2: ₹{target} - Book remaining 50-60%
- Trailing Stop: If Target 1 hit, move SL to breakeven ₹{entry}
\`}

**Time-Based Exit:**
- Maximum Holding: [30 days for weak signals / 45-60 days for strong signals]
- Review at: [X] days - If no progress, consider exiting
- Rationale: Don't let stagnant positions tie up capital

**Event-Based Exit:**
- IF [Specific event] announced → Exit before event
- IF negative news breaks → Immediate market exit
- IF fundamentals deteriorate → Reassess, likely exit

**Trailing Stop Strategy** (if price moves favorably):
- When hits ₹[ENTRY + 50% of target]: Move SL to ₹{entry} (breakeven)
- When hits ₹[ENTRY + 75% of target]: Move SL to ₹[ENTRY + 25%] (lock profit)
- When hits ₹{target}: Move SL to ₹[TARGET - 1%] (protect gains)

**Position Size:**
- Recommended: [X.X]% of portfolio
- In shares: [CALCULATE] shares
- Total investment: ₹[CALCULATE]
- Total risk if stopped: ₹[CALCULATE]
- Total reward if target: ₹[CALCULATE]
\\\`\\\`\\\`

### IF ⚠️ EXECUTE WITH CAUTION - Modified Plan:

\\\`\\\`\\\`
**Proceed with these modifications:**

**Concerns Identified:**
1. [Primary concern - e.g., Weak technical signal {score}]
2. [Secondary concern - e.g., Upcoming earnings in X days]
3. [Tertiary concern - e.g., Moderate liquidity]

**Risk Mitigation:**
- REDUCED Position: [X]% (vs standard [Y]%)
- TIGHTER Monitoring: Daily price/news checks mandatory
- EARLIER Exit: Exit by [DATE] before [EVENT]
- LOWER Target: Consider ₹[REDUCED TARGET] vs ₹{target}

**Modified Entry:**
- Entry: [Stage into position - 50% now, 50% after confirmation]
- Confirmation: [Specific trigger - volume, news, sector turn]
- Or: Wait for [SPECIFIC IMPROVEMENT] before entering

**Modified Exit:**
- Keep same SL: ₹{stopLoss}
- But use tighter trailing stop (don't let winners turn to losers)
- Exit 50% at first sign of weakness
- Maximum hold: [15-20 days] vs normal [30-45 days]

**Conditions to Upgrade to Full Position:**
- If [CONDITION 1 - e.g., Score improves to >0.40]
- If [CONDITION 2 - e.g., Major positive news]
- Then can increase to standard [Y]% position

**Conditions to Exit Immediately:**
- If [CONDITION A - e.g., Falls below ₹[SUPPORT]]
- If [CONDITION B - e.g., Negative surprise announcement]
- Don't wait for stop loss, exit at market
\\\`\\\`\\\`

### IF 🔴 SKIP - No Trade:

\\\`\\\`\\\`
**Recommendation: DO NOT TRADE**

**Primary Reasons (Top 3):**
1. [Most critical - e.g., "Conviction score {score} too weak + fundamentals don't compensate"]
2. [Second - e.g., "High promoter pledge (75%) creates unacceptable risk"]
3. [Third - e.g., "Smart money distributing - FII/DII both selling"]

**Why This Matters:**
[Explain in 2-3 sentences why these specific factors make this a bad trade]

**Better Alternatives:**

IF interested in sector:
- [Peer stock 1] - [Why better setup]
- [Peer stock 2] - [Why better setup]

IF like the company:
- Wait for: [Specific improvement - score >0.40, event to pass, etc.]
- Re-evaluate: [X] days/weeks
- Watch for: [Specific trigger that would make tradeable]

IF need deployment now:
- Look for: [Stocks with >0.50 conviction in different sectors]
- Or: [Consider index ETFs if individual ideas lacking]

**What Would Make {stockName} Tradeable:**

For Technical:
1. Conviction score improves to >[THRESHOLD]
2. Clear trend emerges (not sideways chop)
3. Volume confirms direction

For Fundamental:
1. [Specific improvement - e.g., Pledge reduction to <50%]
2. [Catalyst - e.g., Major order win announced]
3. [Trend - e.g., 2 consecutive quarters of earnings beats]

For Market:
1. Sector turns favorable (outperforms Nifty)
2. VIX drops below [X]
3. FII flows turn positive

**Monitor These for Changes:**
- [Specific metric 1 to track]
- [Specific metric 2 to track]
- Re-evaluate after: [Specific event or time period]
\\\`\\\`\\\`

---

### EXECUTIVE SUMMARY (The Bottom Line):

\\\`\\\`\\\`
**{stockName} ({ticker}) Trade Assessment - Comprehensive Verdict**

**Signal:** {verdict} | **Conviction:** {score}/1.0 | **Setup:** \${Math.abs(parseFloat('{score}')) < 0.15 ? 'Critically Weak' : Math.abs(parseFloat('{score}')) < 0.30 ? 'Weak' : Math.abs(parseFloat('{score}')) < 0.50 ? 'Moderate' : 'Strong'}

**Trade:** ₹{entry} (Entry) → ₹{stopLoss} (Stop) | ₹{target} (Target)
**R:R:** 1:\${(Math.abs(parseFloat('{target}') - parseFloat('{entry}')) / Math.abs(parseFloat('{entry}') - parseFloat('{stopLoss}'))).toFixed(2)} | **Risk:** \${((Math.abs(parseFloat('{entry}') - parseFloat('{stopLoss}')) / parseFloat('{entry}')) * 100).toFixed(2)}% | **Reward:** \${((Math.abs(parseFloat('{target}') - parseFloat('{entry}')) / parseFloat('{entry}')) * 100).toFixed(2)}%

**Multi-Factor Score:** [XX.X]/100

**Key Findings:**
1. **Technical:** [Most important technical finding in one sentence]
2. **Fundamentals:** [Most important fundamental finding in one sentence]
3. **Catalysts:** [Most important catalyst or risk in one sentence]
4. **Smart Money:** [Most important institutional signal in one sentence]
5. **Timing:** [Market/sector context in one sentence]

**Critical Insight:**
[The ONE most important thing to know about this trade - 1-2 sentences maximum]

**Final Recommendation:** [EXECUTE / CONDITIONAL / SKIP] with [X.X]% position
**Confidence Level:** [HIGH / MEDIUM / LOW]

**Primary Reason:**
\${Math.abs(parseFloat('{score}')) < 0.30 ? \`
[Explain whether fundamentals/catalysts provide enough conviction to override weak {score} technical signal, or if weak technicals combined with [other factors] make this a clear skip]
\` : \`
[Explain whether score [XX]/100 combined with [key factor] makes this worth trading, and at what position size]
\`}

**Expected Outcome:** [Most likely scenario based on probabilistic analysis]
**Success Probability:** [X]% (reaching ₹{target})

**If Trading:**
- Entry: [Specific instruction]
- Exit Plan: [Specific stops and targets]
- Monitor: [Most critical metric to watch]
- Duration: [Expected holding period]

**If Skipping:**
- Primary Reason: [Single most important reason]
- Revisit When: [Specific condition or date]
\\\`\\\`\\\`

---

### Monitoring & Review Schedule:

\\\`\\\`\\\`
**IF POSITION TAKEN:**

DAILY (First Week):
- [ ] Price vs ₹{stopLoss} (stop) and ₹{target} (target)
- [ ] Volume abnormalities or unusual activity
- [ ] Breaking news on {stockName} or sector
- [ ] VIX level (exit if spikes >5 points)

WEEKLY (Ongoing):
- [ ] Fundamental developments (quarterly results, announcements)
- [ ] Shareholding pattern changes (end of quarter)
- [ ] Sector relative performance vs Nifty
- [ ] FII/DII flow trends
- [ ] Reassess if thesis still intact

TRIGGER-BASED (Immediate Review):
- [ ] Stop loss hit → Exit, analyze what went wrong
- [ ] Target hit → Book profits per plan
- [ ] Major news (positive or negative) → Reassess thesis
- [ ] Score improvement/deterioration → Adjust conviction
- [ ] Unexpected event announcement → Decide: hold vs exit

**Post-Trade Review (After Exit):**
Document:
- Entry/Exit prices and dates
- Actual vs planned outcome
- What worked / what didn't
- Lessons for future {strategyName} trades
- Was conviction score accurate predictor?
\\\`\\\`\\\`

---

## 📊 ANALYSIS METADATA

**Analysis Completed:** [Auto-fill date/time]
**Analyst:** [AI Model Version]

**Data Freshness:**
- Price Data: [Last updated: timestamp]
- Financial Data: [Latest quarter: QX FY25]
- News: [Scanned through: date]
- Shareholding: [Latest available: QX FY25]
- Market Data: [Current as of: date/time]

**Data Quality Assessment:**
- Overall Availability: [HIGH >80% / MEDIUM 60-80% / LOW <60%]
- Critical Gaps: [List any missing key data]
- Assumptions Made: [List major assumptions if any]
- Confidence Impact: [How data quality affects final confidence]

**Sources Consulted:**
1. NSE/BSE (Price, volume, shareholding)
2. [Screener.in / MoneyControl / Trendlyne] (Financials)
3. [Google News / Company website] (News & announcements)
4. [Specific sources for sector/macro data]

**Limitations:**
- [Any specific limitations to this analysis]
- [Data unavailability impacts]
- [Uncertainty areas]

---

**END OF COMPREHENSIVE ANALYSIS FOR {stockName} ({ticker})**
**Strategy: {strategyName} | Signal: {verdict} | Score: {score}**

---

## 🔧 AI EXECUTION NOTES

**Pre-Analysis Validation:**
1. Confirm all variables populated: {stockName}, {ticker}, {verdict}, {score}, {entry}, {stopLoss}, {target}, {strategyName}
2. Verify {score} is numeric between -1.0 and +1.0
3. Calculate all derived metrics (R:R, risk%, reward%)
4. Set appropriate thresholds based on score strength

**Search Execution:**
- Perform minimum 15-20 web searches across all sections
- Prioritize recent data (<30 days for news, <90 days for financials)
- Cross-verify conflicting information
- Note data freshness and source for all claims

**Scoring Discipline:**
- Use actual numbers, not placeholders
- Show calculation methodology
- Be honest about data gaps
- Adjust confidence down for missing data

**Decision Logic:**
\\\`\\\`\\\`python
# Weak Signal Protocol
if abs(score) < 0.30:
    default_stance = "SKEPTICAL"  # Require strong evidence to trade
    override_threshold = 70  # Need >70 fundamental score to proceed
    
    if fundamental_score > 70 and sentiment_score > 60:
        recommendation = "CONDITIONAL EXECUTE"
        position_size = "REDUCED"
    elif fundamental_score < 50 or critical_red_flags:
        recommendation = "SKIP"
    else:
        recommendation = "WAIT FOR BETTER SETUP"

# Strong Signal Protocol        
elif abs(score) > 0.50:
    default_stance = "VALIDATING"  # Confirm signal is sound
    
    if fundamental_score > 60:
        recommendation = "EXECUTE"
        position_size = "STANDARD"
    elif fundamental_score < 40:
        recommendation = "RECONSIDER"
        position_size = "REDUCED OR SKIP"
\\\`\\\`\\\`

**Output Requirements:**
- Clear verdict: EXECUTE / CONDITIONAL / SKIP
- Specific position size: X.X% of portfolio
- Concrete entry/exit plan with prices
- Honest limitations and confidence level
- Actionable monitoring schedule

---

**Template Version:** 2.0.0
**Last Updated:** 2025-02-14
**Optimized For:** Balanced Analysis Strategy with Dynamic Stock Variables
\`;

export default BALANCED_ANALYSIS_PROMPT;
`;
