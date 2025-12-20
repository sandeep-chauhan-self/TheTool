"""
Test Strategy 5 Validation Integration

Tests the new validation features:
1. ADX market regime filter
2. Momentum context validation
3. Confidence scoring
"""

from utils.analysis_orchestrator import AnalysisOrchestrator

def test_strategy5_validation():
    """Test Strategy 5 analysis with validation"""
    orchestrator = AnalysisOrchestrator()
    result = orchestrator.analyze('RELIANCE.NS', strategy_id=5, use_demo_data=True)
    
    print('=== Strategy 5 Analysis Result ===')
    print(f"Ticker: {result.get('ticker')}")
    print(f"Score: {result.get('score')}")
    print(f"Verdict: {result.get('verdict')}")
    print(f"Signal: {result.get('signal')}")
    print(f"Entry: {result.get('entry')}")
    print(f"Stop: {result.get('stop')}")
    print(f"Target: {result.get('target')}")
    
    # Check validation results
    if 'validation' in result:
        print('')
        print('=== Strategy 5 Validation ===')
        print(f"Confidence Score: {result.get('confidence_score')}")
        print(f"Market Regime: {result.get('market_regime')}")
        val = result.get('validation', {})
        print(f"Momentum Valid: {val.get('momentum_valid')}")
        print(f"Momentum Reason: {val.get('momentum_reason')}")
        if val.get('validation_warnings'):
            print(f"Warnings:")
            for w in val.get('validation_warnings', []):
                print(f"  - {w}")
    else:
        print('')
        print('No validation applied (verdict not BUY)')
    
    return result


def test_backtesting_validation():
    """Test backtesting with Strategy 5 validation"""
    from utils.backtesting import BacktestEngine
    
    engine = BacktestEngine(strategy_id=5)
    print('')
    print('=== Backtesting with Strategy 5 Validation ===')
    print(f"ADX Filter Enabled: {engine.USE_ADX_FILTER}")
    print(f"ADX Choppy Threshold: {engine.ADX_CHOPPY_THRESHOLD}")
    print(f"Strategy 5 Validation Enabled: {engine.USE_STRATEGY5_VALIDATION}")
    
    # Run a quick backtest
    result = engine.backtest_ticker('TCS.NS', days=60)
    
    if 'error' not in result:
        print(f"")
        print(f"=== Backtest Results for TCS.NS ===")
        print(f"Period: {result.get('backtest_period')}")
        print(f"Total Signals: {result.get('total_signals')}")
        print(f"Winning Trades: {result.get('winning_trades')}")
        print(f"Losing Trades: {result.get('losing_trades')}")
        print(f"Win Rate: {result.get('win_rate')}%")
        print(f"Expectancy: {result.get('expectancy')}%")
        print(f"Profit Factor: {result.get('profit_factor')}")
    else:
        print(f"Backtest error: {result.get('error')}")
    
    return result


if __name__ == '__main__':
    print('Testing Strategy 5 Validation Integration...\n')
    test_strategy5_validation()
    test_backtesting_validation()
    print('\n✅ All tests completed!')
