/**
 * Prompt Builder Utility
 * 
 * Takes strategy ID and dynamic parameters, builds the combined prompt
 * string ready for display and clipboard copy.
 */

import { STRATEGY_PROMPTS, STRATEGY_PROMPT_META } from '../constants/aiPrompts';
import { MEAN_REVERSION_BUY_PROMPT_TEMPLATE } from '../constants/meanReversionBuyPrompt';
import { MOMENTUM_BREAKOUT_HOLD_PROMPT_TEMPLATE } from '../constants/momentumBreakoutHoldPrompt';
import { TREND_SELL_PROMPT_TEMPLATE } from '../constants/trendSellPrompt';
import { UNIVERSAL_PROMPT_TEMPLATE } from '../constants/universalPrompt';
import { WEEKLY_TARGET_HOLD_PROMPT_TEMPLATE } from '../constants/weeklyTargetHoldPrompt';

/**
 * Build the Universal Analysis Prompt with dynamic parameters.
 * 
 * @param {Object} params - Dynamic parameters
 * @returns {string} Formatted universal prompt
 */
export function buildUniversalPrompt(params) {
  const safeParams = {
    stockName: params.stockName || 'Unknown Stock',
    ticker: params.ticker || 'N/A',
    verdict: params.verdict || 'N/A',
    score: params.score != null ? params.score : 'N/A',
    entry: params.entry != null ? Number(params.entry).toFixed(2) : 'N/A',
    stopLoss: params.stopLoss != null ? Number(params.stopLoss).toFixed(2) : 'N/A',
    target: params.target != null ? Number(params.target).toFixed(2) : 'N/A',
    strategyName: params.strategyName || 'Unknown Strategy',
    strategyId: params.strategyId, // Added strategyId to params in AIPromptSection call needed, or infer from strategyName
    date: new Date().toLocaleDateString('en-IN', { 
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    })
  };

  // Determine which template to use
  let selectedTemplate = UNIVERSAL_PROMPT_TEMPLATE;

  // Check for Trend Following (Strategy 2) + SELL Signal
  // We check strategyName for "Trend" or if we can pass strategyId.
  // Assuming safeParams.strategyName contains "Trend"
  const strategyNameLower = safeParams.strategyName.toLowerCase();
  const verdictLower = safeParams.verdict.toLowerCase();

  const isTrendFollowing = strategyNameLower.includes('trend');
  const isSell = verdictLower.includes('sell');

  // Check for Mean Reversion (Strategy 3) + BUY Signal
  const isMeanReversion = strategyNameLower.includes('mean') || strategyNameLower.includes('reversion');
  const isBuy = verdictLower.includes('buy');

  // Check for Momentum Breakout (Strategy 1) + HOLD Signal
  const isMomentum = strategyNameLower.includes('momentum');
  const isHold = verdictLower.includes('hold');

  // Check for Weekly 4% Target (Strategy 4) + HOLD Signal
  const isWeeklyTarget = strategyNameLower.includes('weekly') && strategyNameLower.includes('target');

  if (isTrendFollowing && isSell) {
    selectedTemplate = TREND_SELL_PROMPT_TEMPLATE;
  } else if (isMeanReversion && isBuy) {
    selectedTemplate = MEAN_REVERSION_BUY_PROMPT_TEMPLATE;
  } else if (isMomentum && isHold) {
    selectedTemplate = MOMENTUM_BREAKOUT_HOLD_PROMPT_TEMPLATE;
  } else if (isWeeklyTarget && isHold) {
    selectedTemplate = WEEKLY_TARGET_HOLD_PROMPT_TEMPLATE;
  }

  return selectedTemplate
    .replace(/{stockName}/g, safeParams.stockName)
    .replace(/{ticker}/g, safeParams.ticker)
    .replace(/{verdict}/g, safeParams.verdict)
    .replace(/{score}/g, safeParams.score)
    .replace(/{entry}/g, safeParams.entry)
    .replace(/{stopLoss}/g, safeParams.stopLoss)
    .replace(/{target}/g, safeParams.target)
    .replace(/{strategyName}/g, safeParams.strategyName)
    .replace(/{date}/g, safeParams.date);
}

/**
 * Build a single prompt for a given strategy and prompt index.
 * 
 * @param {number} strategyId - Strategy ID (1-5)
 * @param {number} promptIndex - Prompt index (0-4)
 * @param {Object} params - Dynamic parameters
 * @returns {string} Formatted prompt string
 */
export function buildSinglePrompt(strategyId, promptIndex, params) {
  const prompts = STRATEGY_PROMPTS[strategyId];
  if (!prompts || !prompts[promptIndex]) {
    return 'Prompt not available for this strategy.';
  }
  
  const safeParams = {
    stockName: params.stockName || 'Unknown Stock',
    ticker: params.ticker || 'N/A',
    verdict: params.verdict || 'N/A',
    score: params.score != null ? params.score : 'N/A',
    entry: params.entry != null ? Number(params.entry).toFixed(2) : 'N/A',
    stopLoss: params.stopLoss != null ? Number(params.stopLoss).toFixed(2) : 'N/A',
    target: params.target != null ? Number(params.target).toFixed(2) : 'N/A',
    strategyName: params.strategyName || `Strategy ${strategyId}`,
  };
  
  return prompts[promptIndex](safeParams);
}

/**
 * Build all 5 prompts for a strategy combined into a single string.
 * 
 * @param {number} strategyId - Strategy ID (1-5)
 * @param {Object} params - Dynamic parameters
 * @returns {string} Combined prompt string with all 5 prompts
 */
export function buildCombinedPrompt(strategyId, params) {
  const prompts = STRATEGY_PROMPTS[strategyId];
  if (!prompts) {
    return 'No prompts available for this strategy.';
  }
  
  const safeParams = {
    stockName: params.stockName || 'Unknown Stock',
    ticker: params.ticker || 'N/A',
    verdict: params.verdict || 'N/A',
    score: params.score != null ? params.score : 'N/A',
    entry: params.entry != null ? Number(params.entry).toFixed(2) : 'N/A',
    stopLoss: params.stopLoss != null ? Number(params.stopLoss).toFixed(2) : 'N/A',
    target: params.target != null ? Number(params.target).toFixed(2) : 'N/A',
    strategyName: params.strategyName || `Strategy ${strategyId}`,
  };
  
  const header = `# AI Deep Dive Analysis: ${safeParams.stockName} (${safeParams.ticker})
## Strategy: ${safeParams.strategyName}
## Technical Signal: ${safeParams.verdict} (Score: ${safeParams.score})
## Entry: ₹${safeParams.entry} | Stop Loss: ₹${safeParams.stopLoss} | Target: ₹${safeParams.target}

---
I have performed a technical analysis on the above stock. Please complete ALL 5 analysis sections below. Each section covers what my technical analysis DOES NOT analyze. After completing all sections, provide a FINAL consolidated verdict.

`;
  
  const bodies = prompts.map((promptFn, index) => promptFn(safeParams));
  
  return header + bodies.join('\n\n---\n\n');
}

/**
 * Get prompt titles for a given strategy.
 * 
 * @param {number} strategyId - Strategy ID (1-5) 
 * @returns {string[]} Array of prompt titles
 */
export function getPromptTitles(strategyId) {
  const meta = STRATEGY_PROMPT_META[strategyId];
  return meta ? meta.titles : [];
}
