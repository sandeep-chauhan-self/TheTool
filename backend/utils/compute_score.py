"""
Backward Compatibility Shim for utils.compute_score

This module provides backward compatibility for code that imports from utils.compute_score.
The actual implementation has been moved to utils.analysis_orchestrator.

All functions delegate to utils.analysis_orchestrator.
"""

# Re-export everything from analysis_orchestrator
from utils.analysis_orchestrator import (
    AnalysisOrchestrator,
    DataFetcher,
    IndicatorEngine,
    SignalAggregator,
    TradeCalculator,
    ResultFormatter,
    ALL_INDICATORS,
    TYPE_BIAS
)

# Main analysis function
def analyze_ticker(ticker, indicator_list=None, capital=None, use_demo_data=False, analysis_config=None):
    """
    Analyze a ticker symbol using technical indicators.
    
    This is a backward compatibility wrapper. The actual implementation
    is in utils.analysis_orchestrator.AnalysisOrchestrator.
    
    Args:
        ticker: Stock ticker symbol
        indicator_list: List of indicator names (None = all)
        capital: Available capital for position sizing
        use_demo_data: Use demo data instead of live data
        analysis_config: Optional dict with additional config:
            - risk_percent: Max risk per trade (default 2%)
            - position_size_limit: Max position size as % of capital (default 20%)
            - risk_reward_ratio: Min risk-reward ratio (default 1.5)
            - data_period: Historical data period (default '200d')
            - category_weights: Dict of category weights
            - enabled_indicators: Dict of indicator toggles
        
    Returns:
        Dictionary with analysis results
    """
    orchestrator = AnalysisOrchestrator()
    return orchestrator.analyze(ticker, indicator_list, capital, use_demo_data, analysis_config)


# Helper functions
def aggregate_votes(indicator_results):
    """Aggregate indicator votes into composite score."""
    return SignalAggregator.aggregate_votes(indicator_results)


def get_verdict(score):
    """Convert score to trading verdict."""
    return SignalAggregator.get_verdict(score)


__all__ = [
    'analyze_ticker',
    'aggregate_votes',
    'get_verdict',
    'AnalysisOrchestrator',
    'DataFetcher',
    'IndicatorEngine',
    'SignalAggregator',
    'TradeCalculator',
    'ResultFormatter',
]
