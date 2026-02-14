/**
 * AI Prompt Templates for Each Strategy
 * 
 * Each strategy has 5 prompts covering what the strategy's technical analysis
 * does NOT cover: news, sentiment, fundamentals, institutional activity, risk validation.
 * 
 * Dynamic fields: {stockName}, {ticker}, {verdict}, {score}, {entry}, {stopLoss}, {target}, {strategyName}
 * 
 * These are replaced at runtime by promptBuilder.js
 */

// =============================================================================
// Strategy 1: Balanced Analysis Prompts
// =============================================================================
const STRATEGY_1_PROMPTS = [
  // Prompt 1: Sentiment & News Analysis
  (params) => `## Prompt 1: Sentiment & News Analysis for ${params.stockName}

You are a financial analyst specializing in Indian stock markets. I have performed a **technical analysis** on **${params.stockName} (${params.ticker})** using the **${params.strategyName}** strategy which uses 12 equally-weighted technical indicators (MACD, ADX, EMA, PSAR, RSI, Stochastic, CCI, Williams %R, Bollinger Bands, ATR, OBV, CMF).

**My Analysis Result:**
- Verdict: **${params.verdict}**
- Score: **${params.score}**
- Entry Price: ₹${params.entry}
- Stop Loss: ₹${params.stopLoss}
- Target: ₹${params.target}

**What my analysis DOES NOT cover:**
My technical analysis only looks at price patterns and indicators. It does NOT analyze news, sentiment, or market mood.

**Your Task:**
1. Search for the **latest news** (last 7 days) about ${params.stockName} including corporate announcements, earnings, management changes, regulatory actions
2. Analyze **social media sentiment** and retail investor mood around ${params.stockName}
3. Check for any **upcoming events** (earnings dates, AGM, board meetings, ex-dividend dates)
4. Identify any **red flags** or **positive catalysts** in recent news
5. Rate the overall sentiment as: **Very Bullish / Bullish / Neutral / Bearish / Very Bearish**

**Output Format:**
| Category | Finding | Impact (Positive/Negative/Neutral) |
|----------|---------|--------------------------------------|
| Recent News | ... | ... |
| Corporate Actions | ... | ... |
| Social Sentiment | ... | ... |
| Upcoming Events | ... | ... |
| Red Flags | ... | ... |

**Final Sentiment Score:** [Very Bullish / Bullish / Neutral / Bearish / Very Bearish]
**Does sentiment support the ${params.verdict} verdict?** [YES/NO with reason]`,

  // Prompt 2: Fundamental Analysis
  (params) => `## Prompt 2: Fundamental Analysis for ${params.stockName}

You are a fundamental analyst specializing in Indian equities. I have a **technical ${params.verdict}** signal on **${params.stockName} (${params.ticker})** at ₹${params.entry} using the **${params.strategyName}** strategy (score: ${params.score}).

**What my technical analysis CANNOT tell me:**
My strategy uses 12 equally-weighted indicators (trend, momentum, volatility, volume) but has ZERO insight into the company's financial health.

**Your Task — Deep Fundamental Scan:**
1. **Valuation Metrics:** Current P/E ratio, P/B ratio, EV/EBITDA — are they above or below sector average?
2. **Financial Health:** Debt-to-equity ratio, current ratio, interest coverage ratio
3. **Growth Trajectory:** Revenue growth (YoY), profit growth (YoY), operating margin trend (3 years)
4. **Earnings Quality:** Is profit growth backed by operating cash flow? Any signs of aggressive accounting?
5. **Dividend & Buybacks:** Dividend yield, payout ratio, any recent buyback announcements
6. **Peer Comparison:** How does ${params.stockName} compare with its top 3 sector peers on these metrics?

**Output Format:**
| Metric | ${params.stockName} | Sector Average | Status (✅/⚠️/❌) |
|--------|---------------------|----------------|---------------------|
| P/E Ratio | ... | ... | ... |
| Debt/Equity | ... | ... | ... |
| Revenue Growth | ... | ... | ... |
| Profit Growth | ... | ... | ... |
| Operating Margin | ... | ... | ... |
| ROE | ... | ... | ... |

**Fundamental Rating:** [Strong / Moderate / Weak]
**Does the fundamental picture support entering at ₹${params.entry} with target ₹${params.target}?** [YES/NO with detailed reason]`,

  // Prompt 3: Sector & Market Context
  (params) => `## Prompt 3: Sector & Market Context for ${params.stockName}

You are a market strategist analyzing **${params.stockName} (${params.ticker})** in the context of its sector and the broader Indian market.

**My Technical Signal:** ${params.verdict} (Score: ${params.score}) at ₹${params.entry}
**Strategy Used:** ${params.strategyName} — equal weight to all 12 technical indicators

**What my strategy misses:**
The Balanced strategy treats the stock in isolation. It has NO awareness of sector conditions, Nifty/Sensex trend, FII flows, or macroeconomic factors.

**Your Task:**
1. **Sector Analysis:** Which sector does ${params.stockName} belong to? Is this sector currently in favor or out of favor? Top performers and laggards in the sector.
2. **Market Breadth:** What is the current state of Nifty/Sensex? Is the broader market in an uptrend, downtrend, or sideways?
3. **FII/DII Activity:** What are the latest FII and DII flow patterns? Net buyers or sellers?
4. **Macroeconomic Factors:** Any RBI policy decisions, inflation data, GDP numbers, or global events that could impact ${params.stockName}'s sector?
5. **Relative Strength:** How is ${params.stockName} performing relative to its sector and the Nifty — outperforming or underperforming?

**Output Format:**
| Factor | Current State | Impact on ${params.stockName} |
|--------|--------------|-------------------------------|
| Sector Trend | ... | ... |
| Market Breadth | ... | ... |
| FII/DII Flows | ... | ... |
| Macro Factors | ... | ... |
| Relative Strength | ... | ... |

**Market Context Rating:** [Favorable / Neutral / Unfavorable]
**Should I follow the ${params.verdict} signal given current market conditions?** [YES/NO with reason]`,

  // Prompt 4: Insider & Institutional Activity
  (params) => `## Prompt 4: Insider & Institutional Activity for ${params.stockName}

You are an institutional flow analyst. I have a **${params.verdict}** signal on **${params.stockName} (${params.ticker})** from technical analysis (${params.strategyName}, Score: ${params.score}).

**What my technical analysis misses:**
My strategy uses volume indicators (OBV, CMF) but these are aggregate volume measures. They CANNOT distinguish between retail, FII, DII, or promoter activity.

**Your Task — Smart Money Analysis:**
1. **Promoter Holding:** What is the current promoter holding? Has it increased or decreased in the last 3 quarters?
2. **FII/DII Holding:** What are the latest FII and DII holdings? Any significant changes?
3. **Mutual Fund Activity:** Are major mutual funds increasing or decreasing their positions?
4. **Bulk/Block Deals:** Any recent bulk or block deals in ${params.stockName}? Who was buying/selling?
5. **Insider Trading:** Any insider buying or selling disclosed in the last 3 months?
6. **Pledged Shares:** What percentage of promoter holding is pledged? Is it increasing?

**Output Format:**
| Category | Latest Data | Trend (↑/↓/→) | Signal |
|----------|-------------|---------------|--------|
| Promoter Holding | ...% | ... | ... |
| FII Holding | ...% | ... | ... |
| DII Holding | ...% | ... | ... |
| MF Holding | ...% | ... | ... |
| Pledged Shares | ...% | ... | ... |
| Bulk Deals | ... | ... | ... |

**Smart Money Verdict:** [Accumulation / Distribution / Neutral]
**Does institutional activity support my ${params.verdict} signal at ₹${params.entry}?** [YES/NO with reason]`,

  // Prompt 5: Final Validation & Risk Assessment
  (params) => `## Prompt 5: Final Validation — Should I Follow This Signal?

You are a senior portfolio manager reviewing a trade recommendation. Here is the complete picture:

**Stock:** ${params.stockName} (${params.ticker})
**Technical Signal:** ${params.verdict} (Score: ${params.score})
**Strategy:** ${params.strategyName} — Equal weight to all 12 indicators (MACD, ADX, EMA, PSAR, RSI, Stochastic, CCI, Williams %R, Bollinger Bands, ATR, OBV, CMF)
**Entry:** ₹${params.entry} | **Stop Loss:** ₹${params.stopLoss} | **Target:** ₹${params.target}
**Risk-Reward:** 1:${((params.target - params.entry) / (params.entry - params.stopLoss)).toFixed(1)}

**What the technical analysis covered:**
- 4 trend indicators (MACD, ADX, EMA Crossover, Parabolic SAR)
- 4 momentum indicators (RSI, Stochastic, CCI, Williams %R)
- 2 volatility indicators (Bollinger Bands, ATR)
- 2 volume indicators (OBV, CMF)
- All weighted equally at 1.0x

**What it did NOT cover (analyze these now):**
- Recent news and events
- Financial fundamentals (PE, debt, growth)
- Sector and market conditions
- Institutional/promoter activity
- Global macro factors
- Corporate governance quality

**Your Task — Final Comprehensive Assessment:**
1. Considering ALL factors (technical, fundamental, news, sentiment, sector, institutional), give a **final recommendation**
2. List the **top 3 risks** for this trade
3. List the **top 3 supporting factors**
4. Rate confidence: **High / Medium / Low**
5. If you disagree with the ${params.verdict} verdict, explain exactly why

**Output Format:**

### Final Recommendation
| Aspect | Assessment |
|--------|-----------|
| Technical Analysis | ${params.verdict} (Score: ${params.score}) |
| Fundamental Health | [Your Assessment] |
| News & Sentiment | [Your Assessment] |
| Sector Context | [Your Assessment] |
| Institutional Activity | [Your Assessment] |

### Top Risks
1. ...
2. ...
3. ...

### Supporting Factors
1. ...
2. ...
3. ...

### FINAL VERDICT
**Follow the ${params.verdict} signal?** [YES / NO / YES WITH CAUTION]
**Confidence:** [High / Medium / Low]
**Reasoning:** [Detailed explanation]`
];

// =============================================================================
// Strategy 2: Trend Following Prompts
// =============================================================================
const STRATEGY_2_PROMPTS = [
  // Prompt 1: News & Event Catalysts
  (params) => `## Prompt 1: News & Event Catalysts for ${params.stockName} (Trend Following)

You are a catalyst analyst specializing in trending stocks in Indian markets. I have a **${params.verdict}** signal on **${params.stockName} (${params.ticker})** using the **${params.strategyName}** strategy.

**Strategy Context:**
The Trend Following strategy heavily weights MACD (2.5x), ADX (2.5x), EMA Crossover (2.0x), and Parabolic SAR (1.5x) while dampening oscillators (RSI, Stochastic at 0.5x) to avoid premature exits in trending stocks.

**My Analysis Result:**
- Verdict: **${params.verdict}** | Score: **${params.score}**
- Entry: ₹${params.entry} | Stop Loss: ₹${params.stopLoss} (2.5% wider stops) | Target: ₹${params.target} (3x risk-reward)

**What trend analysis CANNOT tell me:**
WHY the stock is trending. Trends need catalysts to sustain them. Without news catalysts, trends can reverse suddenly.

**Your Task:**
1. **Catalyst Hunt:** What news event started or is fueling the current trend in ${params.stockName}? (Earnings beat, new contract, sector policy, management change)
2. **Catalyst Sustainability:** Will this catalyst continue to drive the stock in the trend direction for the next 2-4 weeks?
3. **Counter-Catalysts:** Any upcoming events that could REVERSE this trend? (Earnings miss risk, regulatory headwind, competitor announcement)
4. **Global Catalysts:** Any global events (US Fed decisions, crude oil prices, geopolitical tensions) that could impact the trend?
5. **News Flow Quality:** Is the recent news flow consistently positive/negative, or mixed?

**Output Format:**
| Catalyst Type | Details | Trend Impact (Supports/Threatens) | Duration |
|--------------|---------|-----------------------------------|----------|
| Primary Catalyst | ... | ... | ... |
| Secondary Catalysts | ... | ... | ... |
| Counter-Catalysts | ... | ... | ... |
| Global Factors | ... | ... | ... |

**Catalyst Rating:** [Strong / Moderate / Weak / Absent]
**Is there enough catalyst fuel to sustain this trend to ₹${params.target}?** [YES/NO with reason]`,

  // Prompt 2: Fundamental Health Check
  (params) => `## Prompt 2: Fundamental Health Check for ${params.stockName} (Trend Following)

You are a fundamental analyst. I'm in a **trend-following trade** on **${params.stockName} (${params.ticker})** — ${params.verdict} at ₹${params.entry} with target ₹${params.target}.

**Strategy Context:**
Trend Following trusts MACD, ADX, EMA signals while ignoring oscillator warnings. It uses wider stops (2.5%) and 3x risk-reward. The strategy is designed to "let winners run."

**What trend following misses:**
A stock can trend upward purely on momentum while fundamentals deteriorate (earnings miss, rising debt). Eventually the trend MUST be backed by fundamentals, or it breaks.

**Your Task:**
1. **Earnings Trajectory:** What were the last 4 quarter results? Is the trend in earnings MATCHING the trend in price?
2. **Revenue Quality:** Is revenue growth organic or driven by one-time items?
3. **Debt Position:** Has the company been taking on debt during this trend? Is it sustainable?
4. **Margin Trends:** Are operating and net margins improving, stable, or declining?
5. **Valuation Stretch:** Has the stock become overvalued at current levels compared to its historical PE and sector PE?
6. **Fundamental-Technical Alignment:** Does the fundamental trajectory SUPPORT the current price trend?

**Output Format:**
| Metric | Last 4 Quarters Trend | Status |
|--------|----------------------|--------|
| EPS | ... | ✅/⚠️/❌ |
| Revenue | ... | ✅/⚠️/❌ |
| Operating Margin | ... | ✅/⚠️/❌ |
| Debt/Equity | ... | ✅/⚠️/❌ |
| Current PE vs Historical | ... | ✅/⚠️/❌ |

**Fundamental Support for Trend:** [Strong / Moderate / Weak]
**Risk of fundamental-driven reversal before ₹${params.target}?** [Low / Medium / High with reason]`,

  // Prompt 3: Institutional & Smart Money Flow
  (params) => `## Prompt 3: Institutional & Smart Money Flow for ${params.stockName} (Trend Following)

You are an institutional flow analyst. I'm riding a **${params.verdict}** trend in **${params.stockName} (${params.ticker})** using the Trend Following strategy.

**Strategy Context:**
My strategy uses OBV and CMF at standard 1.0x weight to confirm volume behind the trend. However, these aggregate measures CANNOT distinguish between retail FOMO buying and genuine institutional accumulation.

**Entry:** ₹${params.entry} | **Target:** ₹${params.target} | **Score:** ${params.score}

**Your Task — Who is driving this trend?**
1. **FII Activity:** Are FIIs buying ${params.stockName}? What has been the FII holding change over last 3 quarters?
2. **Domestic Institutions:** Are major mutual funds (SBI, HDFC, ICICI) adding positions?
3. **Promoter Behavior:** Is the promoter buying more shares (bullish) or selling/pledging (concerning)?
4. **Delivery Percentage:** What is the delivery vs. intraday ratio? High delivery = genuine buying.
5. **Volume Profile:** Is the volume increasing as the trend progresses (healthy) or decreasing (exhaustion)?
6. **Retail vs. Institutional Split:** Is this a retail-driven rally (risky) or institution-backed (safer)?

**Output Format:**
| Participant | Action (Buying/Selling/Holding) | Magnitude | Signal |
|-------------|-------------------------------|-----------|--------|
| FIIs | ... | ... | ✅/⚠️/❌ |
| Domestic MFs | ... | ... | ✅/⚠️/❌ |
| Promoter | ... | ... | ✅/⚠️/❌ |
| Retail | ... | ... | ✅/⚠️/❌ |

**Trend Driver:** [Institutional / Retail / Mixed]
**Is smart money behind this trend to ₹${params.target}?** [YES/NO with reason]`,

  // Prompt 4: Sector Momentum & Relative Strength
  (params) => `## Prompt 4: Sector Momentum & Relative Strength for ${params.stockName} (Trend Following)

You are a sector rotation analyst. I have a **${params.verdict}** trend signal on **${params.stockName} (${params.ticker})** at ₹${params.entry}, targeting ₹${params.target}.

**Strategy Context:**
The Trend Following strategy tells me the stock is trending, but it doesn't tell me if the SECTOR is trending too. A stock trending up in a down sector is much riskier than one trending with its sector.

**Your Task:**
1. **Sector Identification:** What sector/industry does ${params.stockName} belong to? What is the sector benchmark index?
2. **Sector Trend:** Is the sector itself in an uptrend, downtrend, or sideways? Compare sector performance over 1 month, 3 months, 6 months.
3. **Sector Rank:** Where does this sector rank among all Nifty sectors? Is it a leading or lagging sector?
4. **${params.stockName} vs Sector:** Is ${params.stockName} outperforming or underperforming its sector? By how much?
5. **Sector Rotation Signal:** Is money flowing INTO this sector or OUT of it? (Based on sector-level FII/DII data)
6. **Top Sector Movers:** What are the top 3 performing stocks in the same sector? Is ${params.stockName} among them?

**Output Format:**
| Factor | Assessment | Signal |
|--------|-----------|--------|
| Sector Trend | ... | ✅/⚠️/❌ |
| Sector Rank (of 12) | ... | ✅/⚠️/❌ |
| Stock vs Sector | ... | ✅/⚠️/❌ |
| Money Flow | ... | ✅/⚠️/❌ |
| Sector Leaders | ... | Context |

**Sector Support for Trend:** [Strong / Moderate / Weak]
**Is ${params.stockName}'s trend supported by sector momentum?** [YES/NO with reason]`,

  // Prompt 5: Trend Reversal Risk & Exit Validation
  (params) => `## Prompt 5: Trend Reversal Risk — Final Validation for ${params.stockName}

You are a senior risk manager reviewing my trend-following trade.

**Trade Setup:**
- **Stock:** ${params.stockName} (${params.ticker})
- **Signal:** ${params.verdict} (Score: ${params.score})
- **Strategy:** ${params.strategyName} — MACD (2.5x), ADX (2.5x), EMA (2.0x), PSAR (1.5x), oscillators dampened at 0.5x
- **Entry:** ₹${params.entry} | **Stop Loss:** ₹${params.stopLoss} (2.5%) | **Target:** ₹${params.target} (3x risk-reward)

**Strategy Philosophy:**
"Trust the trend, ignore oscillator warnings, use wider stops to stay in the trend longer."

**Known Strategy Limitations:**
- Underperforms in choppy/sideways markets
- Late entry signals (trend already started)
- Can suffer during trend reversals
- No awareness of news, fundamentals, or market context

**Your Task — Comprehensive Trend Risk Assessment:**
1. **Trend Age:** How long has the current trend been running? Early, mid, or late stage?
2. **Divergence Check:** Are there any bearish/bullish divergences between price and volume that the strategy might miss?
3. **Key Levels Ahead:** Any major resistance/support levels between ₹${params.entry} and ₹${params.target} that could stall the trend?
4. **Upcoming Risk Events:** Earnings, RBI policy, global events in the next 2-4 weeks
5. **Market Regime:** Is the overall market supportive of trend trades right now?
6. **Comprehensive Risk Score:** Combine all factors

**Output Format:**

### Trend Health Assessment
| Factor | Status | Risk Level |
|--------|--------|-----------|
| Trend Stage | [Early/Mid/Late] | [Low/Medium/High] |
| Volume Confirmation | ... | [Low/Medium/High] |
| Key Resistance/Support | ... | [Low/Medium/High] |
| Event Risk | ... | [Low/Medium/High] |
| Market Regime | ... | [Low/Medium/High] |

### FINAL VERDICT
**Follow the ${params.verdict} signal?** [YES / NO / YES WITH CAUTION]
**Confidence:** [High / Medium / Low]
**Biggest Risk:** [One sentence]
**Recommendation:** [Detailed paragraph explaining whether the trend has enough momentum, catalyst, and institutional support to reach ₹${params.target}]`
];

// =============================================================================
// Strategy 3: Mean Reversion Prompts
// =============================================================================
const STRATEGY_3_PROMPTS = [
  // Prompt 1: Breakout/Breakdown Risk
  (params) => `## Prompt 1: Breakout/Breakdown Risk for ${params.stockName} (Mean Reversion)

You are a price action analyst specializing in range-bound stocks. I have a **${params.verdict}** signal on **${params.stockName} (${params.ticker})** using the **${params.strategyName}** strategy.

**Strategy Context:**
Mean Reversion heavily weights RSI (2.5x), Bollinger Bands (2.5x), Stochastic (2.0x), CCI (1.5x), Williams %R (1.5x) while dampening trend indicators (MACD, ADX, EMA, PSAR at 0.5x). It uses 1.5% tight stops and 1.5x targets.

**My Analysis Result:**
- Verdict: **${params.verdict}** | Score: **${params.score}**
- Entry: ₹${params.entry} | Stop Loss: ₹${params.stopLoss} (tight 1.5%) | Target: ₹${params.target}

**The BIGGEST risk with mean reversion: BREAKOUTS**
If the stock breaks out of its range, my position is immediately wrong and the tight stop loss may not be enough.

**Your Task:**
1. **Range Definition:** What is the current trading range for ${params.stockName}? How many times has the stock bounced between support and resistance in the last 3 months?
2. **Range Duration:** How long has this range lasted? Longer ranges produce more powerful breakouts.
3. **Volatility Compression:** Is ATR/Bollinger Band width contracting? (Compression precedes breakouts)
4. **Volume Pattern:** Is volume increasing near support/resistance? (Precursor to breakout)
5. **Breakout Catalysts:** Any upcoming events (earnings, sector news) that could force a breakout?
6. **Adjacent Levels:** If the range breaks, what is the next support/resistance level?

**Output Format:**
| Factor | Current State | Breakout Risk |
|--------|-------------|---------------|
| Range Width | ₹... to ₹... | ... |
| Range Duration | ... weeks | [Low/Medium/High] |
| Volatility Trend | [Compressing/Stable/Expanding] | [Low/Medium/High] |
| Volume Near Extremes | [Low/Normal/High] | [Low/Medium/High] |
| Catalyst Risk | ... | [Low/Medium/High] |

**Overall Breakout Probability:** [Low / Medium / High]
**Is it safe to play mean reversion at ₹${params.entry}?** [YES/NO with reason]`,

  // Prompt 2: News & Earnings Event Risk
  (params) => `## Prompt 2: News & Earnings Event Risk for ${params.stockName} (Mean Reversion)

You are an event risk analyst. I'm considering a **mean reversion ${params.verdict}** on **${params.stockName} (${params.ticker})** at ₹${params.entry}.

**Strategy Context:**
Mean reversion works because stocks oscillate between overbought and oversold. But events (earnings, news) can PERMANENTLY shift the price to a new level, destroying the range.

**Stop Loss:** ₹${params.stopLoss} (only 1.5% — very tight for event risk)
**Target:** ₹${params.target} (1.5x risk-reward)

**Your Task:**
1. **Earnings Calendar:** When is the next earnings report for ${params.stockName}? How many trading sessions away?
2. **Past Earnings Volatility:** What was the average gap up/gap down on earnings days over the last 4 quarters?
3. **Corporate Actions:** Any upcoming dividends, stock splits, bonuses, rights issues?
4. **Board Meetings:** Any scheduled board meetings that could announce material changes?
5. **Sector-Wide Events:** Any sector policy announcements, government regulations, import/export duties changes?
6. **Event Gap Risk:** Given my 1.5% stop loss, what is the probability that an event causes a gap beyond my stop?

**Output Format:**
| Event | Date/Timeline | Expected Volatility | Gap Risk vs 1.5% Stop |
|-------|------|---|----|
| Earnings | ... | ±...% typical | [Safe/Risky/Dangerous] |
| Corporate Actions | ... | ... | [Safe/Risky/Dangerous] |
| Board Meeting | ... | ... | [Safe/Risky/Dangerous] |
| Sector Events | ... | ... | [Safe/Risky/Dangerous] |

**Event Risk Rating:** [Low / Medium / High]
**Should I wait for any event to pass before entering at ₹${params.entry}?** [YES with specific event / NO]`,

  // Prompt 3: Fundamental Fair Value
  (params) => `## Prompt 3: Fundamental Fair Value for ${params.stockName} (Mean Reversion)

You are a value analyst. I'm playing a **mean reversion** trade on **${params.stockName} (${params.ticker})** assuming the price will revert to the mean.

**Strategy Context:**
Mean reversion assumes the stock is oscillating around a "fair value." But if the fundamentals have CHANGED, the fair value itself may have shifted, and the old range is no longer valid.

**My Trade:** ${params.verdict} at ₹${params.entry} → Target ₹${params.target}

**Critical Question: Is the current range fundamentally justified?**

**Your Task:**
1. **Intrinsic Value Estimate:** Based on PE, PB, DCF, or earnings power, what is the approximate fair value of ${params.stockName}?
2. **Range vs Fair Value:** Is the current trading range (around ₹${params.entry}) aligned with fair value? Or has the stock been trading below/above fair value?
3. **Fundamental Shift:** Have there been any recent changes in earnings guidance, revenue outlook, or competitive position that could shift the fair value?
4. **Sector Valuation:** How does ${params.stockName}'s valuation compare to sector peers? Is it cheap, fair, or expensive?
5. **Mean Regression Target:** My target is ₹${params.target}. Is this price level fundamentally justified?

**Output Format:**
| Valuation Method | Estimated Fair Value | vs Current Price |
|-----------------|---------------------|-----------------|
| PE-based | ₹... | [Undervalued/Fair/Overvalued] |
| PB-based | ₹... | [Undervalued/Fair/Overvalued] |
| Peer Comparison | ₹... | [Undervalued/Fair/Overvalued] |

**Is ₹${params.entry} a fundamentally supported entry for mean reversion?** [YES/NO with reason]
**Is ₹${params.target} a realistic mean reversion target?** [YES/NO with reason]`,

  // Prompt 4: Options & Derivatives Sentiment
  (params) => `## Prompt 4: Options & Derivatives Sentiment for ${params.stockName} (Mean Reversion)

You are a derivatives analyst. I'm taking a **mean reversion ${params.verdict}** trade on **${params.stockName} (${params.ticker})** at ₹${params.entry}.

**Strategy Context:**
Mean reversion uses oscillators to detect overbought/oversold. But the OPTIONS market often provides better forward-looking sentiment data than price oscillators.

**Your Task:**
1. **Put-Call Ratio:** What is the current PCR for ${params.stockName} or its sector? Is it signaling fear or greed?
2. **Options Open Interest:** Where are the major OI concentrations at strike prices? These act as support/resistance.
3. **Max Pain Level:** What is the current max pain level? It often acts as a magnet for the stock price.
4. **Implied Volatility:** Is IV high (expecting big move — dangerous for mean reversion) or low (calm — good for mean reversion)?
5. **Options Sentiment:** Are traders buying calls or puts more aggressively?
6. **OI-Based Support/Resistance:** Based on options OI, what are the key levels?

**Output Format:**
| Metric | Value | Signal for Mean Reversion |
|--------|-------|--------------------------|
| PCR | ... | [Favorable/Neutral/Unfavorable] |
| Max Pain | ₹... | ... |
| IV Rank | ...% | [Low = Good / High = Risky] |
| Put OI Concentration | ₹... | Support Level |
| Call OI Concentration | ₹... | Resistance Level |

**Options Market Verdict:** [Supports Mean Reversion / Against Mean Reversion / Neutral]
**Does the derivatives market agree with my ${params.verdict} at ₹${params.entry}?** [YES/NO with reason]`,

  // Prompt 5: Range Validation & Full Risk Assessment
  (params) => `## Prompt 5: Full Validation — Should I Play Mean Reversion on ${params.stockName}?

You are a senior portfolio manager reviewing my mean-reversion trade.

**Trade Setup:**
- **Stock:** ${params.stockName} (${params.ticker})
- **Signal:** ${params.verdict} (Score: ${params.score})
- **Strategy:** ${params.strategyName} — RSI (2.5x), Bollinger (2.5x), Stochastic (2.0x), CCI (1.5x), Williams %R (1.5x), trend indicators at 0.5x
- **Entry:** ₹${params.entry} | **Stop Loss:** ₹${params.stopLoss} (tight 1.5%) | **Target:** ₹${params.target} (1.5x RR)

**Mean Reversion Philosophy:**
"Buy oversold, sell overbought, with tight stops since ranges are well-defined."

**Known Limitations:**
- Underperforms when trends emerge (breakouts)
- Counter-trend = higher risk per trade
- Can get caught in breakouts with 1.5% stops
- No news, fundamentals, or event awareness

**Your Task — Comprehensive Validation:**
1. Is the range still intact? Any signs of imminent breakout?
2. Do fundamentals support mean reversion at these levels?
3. Are there event risks that could destroy the range?
4. What does the options market say about upcoming volatility?
5. Is the broader market favorable for mean reversion strategies?

**Output Format:**

### Range Validation
| Check | Status | Risk |
|-------|--------|------|
| Range Intact | [Yes/Weakening/Breaking] | [Low/Medium/High] |
| Fundamental Support | ... | [Low/Medium/High] |
| Event Risk | ... | [Low/Medium/High] |
| Options Sentiment | ... | [Low/Medium/High] |
| Market Regime | ... | [Low/Medium/High] |

### FINAL VERDICT
**Follow the ${params.verdict} signal?** [YES / NO / YES WITH CAUTION]
**Confidence:** [High / Medium / Low]
**Biggest Risk:** [One sentence]
**Recommendation:** [Detailed paragraph on whether mean reversion is the right play for ${params.stockName} right now, considering breakout risk, events, and market conditions]`
];

// =============================================================================
// Strategy 4: Momentum Breakout Prompts
// =============================================================================
const STRATEGY_4_PROMPTS = [
  // Prompt 1: Breakout Catalyst Validation
  (params) => `## Prompt 1: Breakout Catalyst Validation for ${params.stockName} (Momentum Breakout)

You are a breakout trading analyst. I have a **${params.verdict}** signal on **${params.stockName} (${params.ticker})** using the **${params.strategyName}** strategy.

**Strategy Context:**
Momentum Breakout heavily weights OBV (2.5x) and CMF (2.5x) for volume confirmation, with RSI (2.0x) and ATR (2.0x) for momentum and volatility. It detects breakouts via volume and volatility expansion.

**My Analysis Result:**
- Verdict: **${params.verdict}** | Score: **${params.score}**
- Entry: ₹${params.entry} | Stop Loss: ₹${params.stopLoss} (wider 3%) | Target: ₹${params.target} (2.5x RR)

**The critical question: Is this a REAL breakout or a FALSE breakout?**
Volume and price alone can't tell you WHY the stock is breaking out. Without a catalyst, breakouts often fail.

**Your Task:**
1. **Catalyst Identification:** What specific event or news triggered this potential breakout? (Earnings beat, order win, sector policy, product launch)
2. **Catalyst Magnitude:** Is this catalyst big enough to sustain a move to ₹${params.target}? Or is it a minor event being overreacted to?
3. **Historical Pattern:** In the past, how has ${params.stockName} reacted to similar catalysts? Does it hold gains or give them back?
4. **Competing Narrative:** Is there any bearish narrative that could undermine this breakout?
5. **Catalyst Duration:** Is this a one-time event (gap and fade risk) or an ongoing story (sustained trend)?

**Output Format:**
| Factor | Assessment | Breakout Support |
|--------|-----------|-----------------|
| Primary Catalyst | ... | [Strong/Moderate/Weak/None] |
| Catalyst Magnitude | ... | [Sufficient/Insufficient] |
| Historical Precedent | ... | [Bullish/Bearish/Mixed] |
| Counter-Narrative | ... | [Absent/Present/Strong] |
| Catalyst Duration | [One-time/Short-term/Long-term] | ... |

**Breakout Authenticity:** [High Conviction / Medium / Low — Possible Fakeout]
**Is this breakout backed by a real catalyst?** [YES/NO with reason]`,

  // Prompt 2: Fundamental Justification
  (params) => `## Prompt 2: Fundamental Justification for ${params.stockName} Breakout

You are a fundamental analyst evaluating whether a **breakout** in **${params.stockName} (${params.ticker})** is fundamentally justified.

**Trade:** ${params.verdict} at ₹${params.entry} → Target ₹${params.target} (2.5x risk-reward)
**Strategy:** Momentum Breakout — volume and momentum focused

**The question: Does the price DESERVE to be higher/lower?**
Breakouts without fundamental support eventually fail. Volume spike + no fundamental change = potential trap.

**Your Task:**
1. **Earnings Power:** Can ${params.stockName}'s earnings justify a price of ₹${params.target}? What PE would that imply?
2. **Revenue Catalyst:** Is there a new revenue stream, market expansion, or contract win that justifies revaluation?
3. **Margin Expansion:** Any reason to expect margin improvement (cost reduction, pricing power)?
4. **Competitive Moat:** Does ${params.stockName} have a competitive advantage that supports higher valuations?
5. **Analyst Consensus:** What are analyst target prices? Is ₹${params.target} within or beyond analyst estimates?
6. **Valuation at Target:** What would PE, PB, EV/EBITDA be at ₹${params.target}? Would it still be reasonable?

**Output Format:**
| Metric | At Entry (₹${params.entry}) | At Target (₹${params.target}) | Sector Average |
|--------|-----|------|------|
| PE Ratio | ... | ... | ... |
| PB Ratio | ... | ... | ... |
| EV/EBITDA | ... | ... | ... |

**Fundamental Support:** [Strong / Moderate / Weak]
**Is ₹${params.target} a fundamentally reasonable target?** [YES/NO with reason]`,

  // Prompt 3: Institutional Activity Deep Dive
  (params) => `## Prompt 3: Institutional Activity for ${params.stockName} (Momentum Breakout)

You are an institutional flow analyst. I see a **volume breakout** signal in **${params.stockName} (${params.ticker})** — ${params.verdict} at ₹${params.entry}.

**Strategy Context:**
My strategy uses OBV (2.5x) and CMF (2.5x) to detect volume-based breakouts. But these are AGGREGATE volume measures. A volume spike from 100 retail traders and a volume spike from 1 institutional order look the same to OBV/CMF.

**Critical Question: WHO is behind the volume spike?**

**Your Task:**
1. **Block/Bulk Deals:** Any recent block or bulk deals in ${params.stockName}? Who bought? Who sold?
2. **FII Buying Trend:** Have FIIs been accumulating ${params.stockName} in the last 1-3 months?
3. **Mutual Fund Changes:** Any major mutual fund scheme recently adding ${params.stockName}?
4. **Delivery Percentage:** What is the delivery percentage on the breakout day(s)? High delivery = genuine, low = speculative.
5. **Short Interest:** Any significant short positions that could fuel a short squeeze?
6. **Promoter Activity:** Is the promoter buying alongside the breakout?

**Output Format:**
| Participant | Activity | Volume Signal |
|-------------|---------|---------------|
| FIIs | ... | [Accumulating/Distributing/Neutral] |
| DIIs/MFs | ... | [Accumulating/Distributing/Neutral] |
| Promoter | ... | [Buying/Selling/Neutral] |
| Delivery % | ...% | [High (>50%)/Medium/Low] |
| Short Interest | ... | [Not significant/Moderate/Short squeeze potential] |

**Volume Authenticity:** [Institutional / Retail-driven / Mixed]
**Is this an institutional breakout?** [YES/NO with reason]`,

  // Prompt 4: Sector Rotation & Market Context
  (params) => `## Prompt 4: Sector Rotation for ${params.stockName} (Momentum Breakout)

You are a sector rotation strategist. I have a **breakout ${params.verdict}** signal on **${params.stockName} (${params.ticker})** at ₹${params.entry}.

**Strategy Context:**
Momentum Breakout detects individual stock breakouts but has NO awareness of whether the SECTOR is breaking out too. A stock breaking out with its sector is much more reliable.

**Your Task:**
1. **Sector Momentum:** Is ${params.stockName}'s sector showing strength? Compare 1W, 1M, 3M sector returns.
2. **Sector Breakout:** Is the sector index also breaking out of a range/consolidation?
3. **${params.stockName} as Leader/Laggard:** Is ${params.stockName} leading the sector breakout or catching up late?
4. **Money Flow:** Is institutional money rotating INTO this sector? (Sector-level FII/DII data)
5. **Cross-Sector Comparison:** How does this sector rank vs all Nifty sectors? Is money flowing in or out?
6. **Market Breadth:** How many stocks in this sector are also showing breakout patterns?

**Output Format:**
| Metric | Value | Signal |
|--------|-------|--------|
| Sector 1M Return | ...% | ✅/⚠️/❌ |
| Sector 3M Return | ...% | ✅/⚠️/❌ |
| Sector Rank (of 12) | #... | ✅/⚠️/❌ |
| ${params.stockName} vs Sector | [Leading/Inline/Lagging] | ✅/⚠️/❌ |
| Sector Breadth | ...% of stocks bullish | ✅/⚠️/❌ |

**Sector Support for Breakout:** [Strong / Moderate / Weak]
**Is this a sector-wide breakout or stock-specific?** [Sector-wide / Stock-specific with reason]`,

  // Prompt 5: False Breakout Risk & Exit Strategy
  (params) => `## Prompt 5: False Breakout Risk — Final Validation for ${params.stockName}

You are a senior risk manager reviewing my momentum breakout trade.

**Trade Setup:**
- **Stock:** ${params.stockName} (${params.ticker})
- **Signal:** ${params.verdict} (Score: ${params.score})
- **Strategy:** ${params.strategyName} — OBV (2.5x), CMF (2.5x), RSI (2.0x), ATR (2.0x)
- **Entry:** ₹${params.entry} | **Stop Loss:** ₹${params.stopLoss} (3% wider) | **Target:** ₹${params.target} (2.5x RR)

**Biggest Risk: FALSE BREAKOUT**
Strategy uses wider 3% stops to handle breakout volatility, but false breakouts can still cause losses.

**False Breakout Checklist — Verify Each:**
1. ✅/❌ **Volume Confirmation:** Was breakout volume > 1.5x average volume?
2. ✅/❌ **Price Close:** Did price CLOSE above resistance (not just an intraday wick)?
3. ✅/❌ **Catalyst Exists:** Is there a fundamental reason for the breakout?
4. ✅/❌ **Institutional Backing:** Are institutions buying or is it retail FOMO?
5. ✅/❌ **Sector Support:** Is the sector also breaking out?
6. ✅/❌ **No Divergence:** Are RSI and price both making new highs/lows (no divergence)?

**Your Task — Comprehensive Assessment:**
Complete the checklist above and provide a final verdict.

**Output Format:**

### False Breakout Checklist
| Check | Status | Evidence |
|-------|--------|----------|
| Volume > 1.5x Average | ✅/❌ | ... |
| Price Closed Above Level | ✅/❌ | ... |
| Catalyst Present | ✅/❌ | ... |
| Institutional Backing | ✅/❌ | ... |
| Sector Support | ✅/❌ | ... |
| No Divergence | ✅/❌ | ... |

**Score:** .../6 checks passed

### FINAL VERDICT
**Follow the ${params.verdict} signal?** [YES / NO / YES WITH CAUTION]
**Confidence:** [High / Medium / Low]
**False Breakout Probability:** [Low / Medium / High]
**Recommendation:** [Detailed paragraph on whether this breakout will hold, considering volume, catalyst, institutions, and sector context]`
];

// =============================================================================
// Strategy 5: Weekly 4% Target Prompts
// =============================================================================
const STRATEGY_5_PROMPTS = [
  // Prompt 1: Upcoming Events & Earnings Calendar
  (params) => `## Prompt 1: Events & Earnings Calendar for ${params.stockName} (Weekly 4% Target)

You are an event-focused swing trade analyst. I have a **${params.verdict}** signal on **${params.stockName} (${params.ticker})** using the **${params.strategyName}** strategy.

**Strategy Context:**
Strategy 5 targets 4% profit within 15 bars (~3 weeks). It uses momentum indicators (RSI 2.0x, Stochastic 2.0x, CCI 1.8x) with trend filters (SMA 50, ADX > 20) and validation (3/5 momentum convergence). It allows up to 35% position size.

**My Analysis Result:**
- Verdict: **${params.verdict}** | Score: **${params.score}**
- Entry: ₹${params.entry} | Stop Loss: ₹${params.stopLoss} (3-4% dynamic) | Target: ₹${params.target} (4%)
- Maximum holding: 15 bars (~3 weeks)

**The critical question: What events could happen in the next 3 weeks?**
During a 15-bar hold period, ANY event can wreck a swing trade. The strategy has a 3-bar cooldown after losses but NO awareness of upcoming events.

**Your Task:**
1. **Earnings Date:** When is ${params.stockName}'s next quarterly earnings? Is it within the 15-bar window?
2. **Dividend Dates:** Any ex-dividend dates in the next 3 weeks? (Price typically drops by dividend amount)
3. **Board Meetings:** Any scheduled board meetings?
4. **Sector Events:** Any budget announcement, policy changes, or regulatory decisions affecting ${params.stockName}'s sector?
5. **Global Events:** US Fed meeting, RBI policy, geopolitical risks in the next 3 weeks?
6. **Historical Event Volatility:** How much did ${params.stockName} move on its last 4 events?

**Output Format:**
| Event | Date | Days Away | Expected Impact | Risk to 4% Target |
|-------|------|-----------|----------------|-------------------|
| Earnings | ... | ... | ±...% | [None/Low/Medium/High/Critical] |
| Dividend | ... | ... | ... | [None/Low/Medium/High/Critical] |
| Board Meeting | ... | ... | ... | [None/Low/Medium/High/Critical] |
| RBI Policy | ... | ... | ... | [None/Low/Medium/High/Critical] |
| Other | ... | ... | ... | [None/Low/Medium/High/Critical] |

**Event Risk Rating:** [Clear / Low / Medium / High]
**Can I safely hold ${params.stockName} for 15 bars to target ₹${params.target}?** [YES/NO with reason]`,

  // Prompt 2: Market Sentiment & Breadth
  (params) => `## Prompt 2: Market Sentiment & Breadth for ${params.stockName} (Weekly 4% Target)

You are a market sentiment analyst. I'm planning a **swing trade** on **${params.stockName} (${params.ticker})** — ${params.verdict} at ₹${params.entry}, targeting 4% in 1-3 weeks.

**Strategy Context:**
Strategy 5 requires ADX > 20 and price above SMA(50) for entries. But it has NO awareness of overall market sentiment, VIX levels, or advance-decline ratios.

**Your Task — Is the market environment suitable for swing trading?**
1. **India VIX:** What is the current India VIX level? Below 15 = calm (good for swings), above 20 = volatile (risky)
2. **Market Breadth:** What is the advance-decline ratio on NSE? Are most stocks rising or falling?
3. **Nifty/Sensex Trend:** Is the index above its 50 DMA and 200 DMA? (Trend alignment)
4. **FII/DII Sentiment:** Net FII/DII flows for the last week. Are institutions bullish or bearish?
5. **Global Risk Appetite:** What is the global risk sentiment? (US markets, dollar index, bond yields)
6. **Seasonal Patterns:** Any seasonal factors (budget month, quarterly settlement, results season)?

**Output Format:**
| Indicator | Current Value | Signal for Swing Trading |
|-----------|------|------|
| India VIX | ... | [Favorable (<15) / Neutral / Risky (>20)] |
| Advance-Decline | ... | [Bullish / Neutral / Bearish] |
| Nifty vs 50 DMA | ... | [Above / Below] |
| FII Net Flow (1W) | ₹... Cr | [Buying / Selling] |
| Global Sentiment | ... | [Risk-On / Neutral / Risk-Off] |

**Market Environment:** [Excellent / Good / Average / Poor for swing trading]
**Should I deploy 4% target swing trades in this market?** [YES/NO with reason]`,

  // Prompt 3: Fundamental Quick Scan
  (params) => `## Prompt 3: Fundamental Quick Scan for ${params.stockName} (Weekly 4% Target)

You are a fundamental screener. I'm considering a **1-3 week swing trade** on **${params.stockName} (${params.ticker})** — ${params.verdict} at ₹${params.entry}.

**Strategy Context:**
Strategy 5 is momentum-based with intelligent filters. It allows up to 35% position size for high-conviction trades. For a 35% position, the fundamentals MUST be sound — even for a short-term trade.

**Target:** ₹${params.target} (4%) | **Max Hold:** 15 bars

**Your Task — Quick Fundamental Health Check:**
1. **Earnings Quality:** Were the last 2 quarters' earnings in line, beat, or miss? Any revenue growth?
2. **Debt Concerns:** Any concerning debt levels? Can the company service its debt?
3. **Promoter Red Flags:** Any promoter pledge increase, selling, or corporate governance issues?
4. **Cash Flow:** Is operating cash flow positive and growing?
5. **Sector Tailwinds/Headwinds:** Any sector-level fundamental changes affecting ${params.stockName}?
6. **Quick Ratio Check:** Is the stock reasonably valued for a short-term trade? (Not at 100x PE)

**Output Format (Traffic Light):**
| Check | Status | Details |
|-------|--------|---------|
| Recent Earnings | 🟢/🟡/🔴 | ... |
| Debt Health | 🟢/🟡/🔴 | ... |
| Promoter Issues | 🟢/🟡/🔴 | ... |
| Cash Flow | 🟢/🟡/🔴 | ... |
| Sector Fundamentals | 🟢/🟡/🔴 | ... |
| Valuation | 🟢/🟡/🔴 | ... |

**Score:** .../6 green lights
**Is ${params.stockName} fundamentally safe for a 35% position swing trade?** [YES/NO with reason]`,

  // Prompt 4: Sector Health & Rotation Check
  (params) => `## Prompt 4: Sector Health for ${params.stockName} (Weekly 4% Target)

You are a sector rotation analyst. I'm planning a **4% swing trade** on **${params.stockName} (${params.ticker})** — ${params.verdict} at ₹${params.entry}.

**Strategy Context:**
Strategy 5's best results occur when the market is in an uptrend AND the stock just broke above consolidation with above-average volume. But it has NO sector awareness.

**Your Task:**
1. **Sector Identification & Trend:** What sector is ${params.stockName} in? Is the sector trending up, down, or sideways over 1W, 2W, 1M?
2. **Sector Relative Strength:** How does this sector rank among all NSE sectors? Top 3 = bullish, Bottom 3 = bearish.
3. **Sector Money Flow:** Net FII/DII activity in this sector. Is money coming in or going out?
4. **Sector Peers Performance:** How are the top 5 stocks in this sector performing? Is ${params.stockName} among the leaders?
5. **Sector Catalyst:** Any sector-specific catalyst (policy change, global demand, commodities) that could help or hurt?
6. **4% Viability:** Given sector conditions, can ${params.stockName} realistically move 4% in 1-3 weeks?

**Output Format:**
| Factor | Assessment | Signal |
|--------|-----------|--------|
| Sector 1W Return | ...% | ✅/⚠️/❌ |
| Sector 2W Return | ...% | ✅/⚠️/❌ |
| Sector Rank | #.../12 | ✅/⚠️/❌ |
| Money Flow | ... | ✅/⚠️/❌ |
| ${params.stockName} vs Peers | [Leading/Middle/Lagging] | ✅/⚠️/❌ |

**Sector Support:** [Strong / Moderate / Weak]
**Does the sector support a 4% move in ${params.stockName} over 1-3 weeks?** [YES/NO with reason]`,

  // Prompt 5: 4% Target Viability & Final Validation
  (params) => `## Prompt 5: Final Validation — Can ${params.stockName} Hit 4% in 3 Weeks?

You are a senior swing trading coach reviewing my trade setup.

**Trade Setup:**
- **Stock:** ${params.stockName} (${params.ticker})
- **Signal:** ${params.verdict} (Score: ${params.score})
- **Strategy:** ${params.strategyName} — Momentum-focused with intelligent filters
  - Entry Filters: SMA(50) trend, RSI 50-75 window, 3/5 momentum convergence, ADX > 20, 3-bar cooldown
  - Weights: RSI (2.0x), Stochastic (2.0x), CCI (1.8x), Williams %R (1.6x), MACD (1.5x)
- **Entry:** ₹${params.entry} | **Stop Loss:** ₹${params.stopLoss} (3-4% ATR-based) | **Target:** ₹${params.target} (4%)
- **Max Hold:** 15 bars (~3 weeks) | **Position Size:** Up to 35% of capital

**Strategy Performance Benchmarks:**
- Win Rate: 55-65% | Profit Factor: 1.5-2.5x
- Target Hit Rate: 40-45% | Time Exit Win Rate: 72%

**Key Question: Can ${params.stockName} realistically move 4% in 1-3 weeks given ALL factors?**

**Your Task — Comprehensive Assessment:**
1. **Historical Volatility:** What is ${params.stockName}'s average weekly move? Is 4% achievable in its typical range?
2. **Event Calendar:** Any events in the 15-bar window that could help or hurt?
3. **Fundamental Health:** Is the company fundamentally sound?
4. **Sector & Market:** Are market conditions supportive?
5. **Institutional Interest:** Is smart money aligned?
6. **Risk Assessment:** What could go wrong?

**Output Format:**

### Viability Assessment
| Factor | Assessment | 4% Target Support |
|--------|-----------|-------------------|
| Avg Weekly Move | ±...% | [Easy/Achievable/Stretch/Unlikely] |
| Event Risk | ... | [Clear/Moderate/High] |
| Fundamentals | ... | [Strong/Moderate/Weak] |
| Sector Support | ... | [Strong/Moderate/Weak] |
| Institutional Alignment | ... | [Aligned/Neutral/Against] |

### FINAL VERDICT
**Follow the ${params.verdict} signal?** [YES / NO / YES WITH CAUTION]
**4% Target Probability:** [High (>50%) / Medium (30-50%) / Low (<30%)]
**Confidence for 35% Position:** [Full size / Reduce to 20% / Reduce to 10% / Skip]
**Biggest Risk:** [One sentence]
**Recommendation:** [Detailed paragraph — should the user take this trade, at what position size, and what to watch for during the hold period]`
];

// =============================================================================
// Export: Strategy Prompts Map
// =============================================================================
export const STRATEGY_PROMPTS = {
  1: STRATEGY_1_PROMPTS,
  2: STRATEGY_2_PROMPTS,
  3: STRATEGY_3_PROMPTS,
  4: STRATEGY_4_PROMPTS,
  5: STRATEGY_5_PROMPTS,
};

/**
 * Strategy prompt metadata for display
 */
export const STRATEGY_PROMPT_META = {
  1: {
    titles: [
      'Sentiment & News Analysis',
      'Fundamental Analysis',
      'Sector & Market Context',
      'Insider & Institutional Activity',
      'Final Validation & Risk Assessment',
    ]
  },
  2: {
    titles: [
      'News & Event Catalysts',
      'Fundamental Health Check',
      'Institutional & Smart Money Flow',
      'Sector Momentum & Relative Strength',
      'Trend Reversal Risk & Exit Validation',
    ]
  },
  3: {
    titles: [
      'Breakout/Breakdown Risk',
      'News & Earnings Event Risk',
      'Fundamental Fair Value',
      'Options & Derivatives Sentiment',
      'Range Validation & Full Risk Assessment',
    ]
  },
  4: {
    titles: [
      'Breakout Catalyst Validation',
      'Fundamental Justification',
      'Institutional Activity Deep Dive',
      'Sector Rotation & Market Context',
      'False Breakout Risk & Exit Strategy',
    ]
  },
  5: {
    titles: [
      'Events & Earnings Calendar',
      'Market Sentiment & Breadth',
      'Fundamental Quick Scan',
      'Sector Health & Rotation Check',
      '4% Target Viability & Final Validation',
    ]
  },
};
