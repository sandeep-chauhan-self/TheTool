/**
 * Prompt Builder Utility
 * 
 * Takes strategy ID and dynamic parameters, builds the combined prompt
 * string ready for display and clipboard copy.
 */

import { STRATEGY_PROMPTS, STRATEGY_PROMPT_META } from '../constants/aiPrompts';

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
