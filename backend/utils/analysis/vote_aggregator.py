"""
Strategy Aggregator Utility

Aggregates multiple trading strategy signals into a unified recommendation.
Similar to compute_score.py but for strategies instead of indicators.

Functions:
- aggregate_strategies: Combines strategy votes with confidence weighting
- select_best_strategy: Picks the strategy with highest confidence
"""

import logging

logger = logging.getLogger(__name__)


def aggregate_strategies(strategy_results):
    """
    Aggregate multiple strategy signals into final recommendation
    
    Args:
        strategy_results: List of strategy result dictionaries, each containing:
            {
                'signal': 'BUY' | 'SELL' | 'NEUTRAL',
                'entry_price': float,
                'stop_loss': float,
                'target': float,
                'confidence': float (0.0-1.0),
                'reason': str,
                'strategy_name': str
            }
    
    Returns:
        dict: {
            'recommended_action': 'BUY' | 'SELL' | 'NEUTRAL',
            'best_strategy': dict (strategy with highest confidence),
            'entry_price': float,
            'stop_loss': float,
            'target': float,
            'overall_confidence': float,
            'strategy_votes': {
                'BUY': int,
                'SELL': int,
                'NEUTRAL': int
            },
            'all_strategies': list (all strategy results)
        }
    """
    try:
        if not strategy_results or len(strategy_results) == 0:
            return {
                'recommended_action': 'NEUTRAL',
                'best_strategy': None,
                'entry_price': None,
                'stop_loss': None,
                'target': None,
                'overall_confidence': 0.0,
                'strategy_votes': {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0},
                'all_strategies': []
            }
        
        # Count votes for each signal
        vote_counts = {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0}
        weighted_votes = {'BUY': 0.0, 'SELL': 0.0, 'NEUTRAL': 0.0}
        
        for strategy in strategy_results:
            signal = strategy.get('signal', 'NEUTRAL')
            confidence = strategy.get('confidence', 0.0)
            
            if signal in vote_counts:
                vote_counts[signal] += 1
                weighted_votes[signal] += confidence
        
        # Find signal with highest weighted vote
        recommended_action = max(weighted_votes, key=weighted_votes.get)
        
        # Select best strategy (highest confidence)
        best_strategy = max(strategy_results, key=lambda x: x.get('confidence', 0.0))
        
        # Calculate overall confidence (average of all confidences)
        total_confidence = sum(s.get('confidence', 0.0) for s in strategy_results)
        overall_confidence = total_confidence / len(strategy_results) if strategy_results else 0.0
        
        # Use best strategy's prices as recommendation
        entry_price = best_strategy.get('entry_price')
        stop_loss = best_strategy.get('stop_loss')
        target = best_strategy.get('target')
        
        result = {
            'recommended_action': recommended_action,
            'best_strategy': best_strategy,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'target': target,
            'overall_confidence': round(overall_confidence, 2),
            'strategy_votes': vote_counts,
            'all_strategies': strategy_results
        }
        
        logger.info(f"Strategy aggregation: {recommended_action} (confidence: {overall_confidence:.2f})")
        return result
        
    except Exception as e:
        logger.error(f"Error aggregating strategies: {e}")
        return {
            'recommended_action': 'NEUTRAL',
            'best_strategy': None,
            'entry_price': None,
            'stop_loss': None,
            'target': None,
            'overall_confidence': 0.0,
            'strategy_votes': {'BUY': 0, 'SELL': 0, 'NEUTRAL': 0},
            'all_strategies': strategy_results
        }


def select_best_strategy(strategy_results):
    """
    Select the single best strategy from results (highest confidence)
    
    Args:
        strategy_results: List of strategy result dictionaries
    
    Returns:
        dict: Single best strategy or None
    """
    if not strategy_results or len(strategy_results) == 0:
        return None
    
    return max(strategy_results, key=lambda x: x.get('confidence', 0.0))
