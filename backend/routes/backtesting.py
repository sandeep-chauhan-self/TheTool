"""
Backtesting API endpoints

Following TheTool architecture:
- Thread-safe with get_db_session() for background job compatibility
- Uses _convert_query_params() for database abstraction (PostgreSQL/SQLite)
- Centralized logging via infrastructure.logger
- Error handling via api_utils.register_error_handlers
"""

from flask import Blueprint, request, jsonify
from utils.backtesting import BacktestEngine
import logging

bp = Blueprint('backtesting', __name__, url_prefix='/api/backtest')
logger = logging.getLogger('trading_analyzer')


@bp.route('/ticker/<ticker>', methods=['GET'])
def backtest_ticker(ticker):
    """
    Backtest Strategy 5 on a single ticker.
    
    Query params:
    - days: Historical days to analyze (30-365, default 90)
    
    Example:
        GET /api/backtest/ticker/RELIANCE.NS?days=90
    
    Returns:
        {
            'ticker': 'RELIANCE.NS',
            'backtest_period': '2025-11-01 to 2025-01-28',
            'total_signals': 45,
            'winning_trades': 32,
            'losing_trades': 13,
            'win_rate': 71.1,
            'profit_factor': 2.45,
            'total_profit_pct': 18.5,
            'avg_win': 4.2,
            'avg_loss': -3.1,
            'max_drawdown': -8.5,
            'consecutive_wins': 8,
            'trades_per_day': 0.5,
            'trades': [
                {
                    'entry_date': '2025-01-15',
                    'entry_price': 2500.50,
                    'exit_price': 2605.00,
                    'target': 2600.52,
                    'stop_loss': 2425.49,
                    'outcome': 'WIN',
                    'pnl_pct': 4.18,
                    'bars_held': 3,
                    'reason': 'Hit 4% target',
                    'confidence': 95.0,
                    'rsi': 58.5
                },
                ...
            ]
        }
    """
    try:
        # Get parameters
        days = request.args.get('days', 90, type=int)
        
        # Validate
        if days < 30 or days > 365:
            return jsonify({'error': 'days must be between 30 and 365'}), 400
        
        logger.info(f"[API] Backtest request: {ticker} ({days} days)")
        
        # Run backtest
        engine = BacktestEngine(strategy_id=5)
        result = engine.backtest_ticker(ticker, days=days)
        
        if 'error' in result:
            logger.warning(f"[API] Backtest failed for {ticker}: {result['error']}")
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"[API] Invalid parameter: {str(e)}")
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"[API] Backtest failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/portfolio', methods=['POST'])
def backtest_portfolio():
    """
    Backtest multiple tickers.
    
    Body:
        {
            'tickers': ['RELIANCE.NS', 'TCS.NS', 'INFY.NS'],
            'days': 90
        }
    
    Returns:
        {
            'tickers_analyzed': 3,
            'results': {
                'RELIANCE.NS': { backtest_result },
                'TCS.NS': { backtest_result },
                'INFY.NS': { backtest_result }
            }
        }
    """
    try:
        # Get request data
        data = request.json or {}
        tickers = data.get('tickers', [])
        days = data.get('days', 90)
        
        # Validate
        if not tickers:
            return jsonify({'error': 'tickers array required'}), 400
        
        if not isinstance(tickers, list):
            return jsonify({'error': 'tickers must be a list'}), 400
        
        if len(tickers) > 50:
            return jsonify({'error': 'Maximum 50 tickers per backtest'}), 400
        
        if days < 30 or days > 365:
            return jsonify({'error': 'days must be between 30 and 365'}), 400
        
        logger.info(f"[API] Portfolio backtest: {len(tickers)} tickers ({days} days)")
        
        # Run backtest for each ticker
        engine = BacktestEngine(strategy_id=5)
        results = {}
        
        for ticker in tickers:
            logger.debug(f"[API] Backtesting {ticker}...")
            results[ticker] = engine.backtest_ticker(ticker, days=days)
        
        logger.info(f"[API] Portfolio backtest complete: {len(tickers)} tickers")
        
        return jsonify({
            'tickers_analyzed': len(tickers),
            'days': days,
            'results': results
        }), 200
        
    except ValueError as e:
        logger.error(f"[API] Invalid parameter: {str(e)}")
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"[API] Portfolio backtest failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/compare-strategies', methods=['POST'])
def compare_strategies():
    """
    Compare performance of different strategies on same ticker.
    
    Body:
        {
            'ticker': 'RELIANCE.NS',
            'days': 90,
            'strategies': [1, 2, 3, 4, 5]
        }
    
    Returns:
        {
            'ticker': 'RELIANCE.NS',
            'days': 90,
            'comparison': {
                'strategy_1': { backtest_result },
                'strategy_2': { backtest_result },
                'strategy_5': { backtest_result }
            }
        }
    """
    try:
        # Get request data
        data = request.json or {}
        ticker = data.get('ticker')
        days = data.get('days', 90)
        strategies = data.get('strategies', [1, 2, 3, 4, 5])
        
        # Validate
        if not ticker:
            return jsonify({'error': 'ticker required'}), 400
        
        if not isinstance(strategies, list) or len(strategies) == 0:
            return jsonify({'error': 'strategies must be non-empty list'}), 400
        
        if days < 30 or days > 365:
            return jsonify({'error': 'days must be between 30 and 365'}), 400
        
        logger.info(f"[API] Strategy comparison: {ticker} (days={days}, strategies={strategies})")
        
        # Run backtest for each strategy
        comparison = {}
        
        for strategy_id in strategies:
            try:
                logger.debug(f"[API] Backtesting strategy {strategy_id}...")
                engine = BacktestEngine(strategy_id=strategy_id)
                comparison[f'strategy_{strategy_id}'] = engine.backtest_ticker(ticker, days=days)
            except Exception as e:
                logger.error(f"[API] Strategy {strategy_id} failed: {str(e)}")
                comparison[f'strategy_{strategy_id}'] = {'error': str(e)}
        
        logger.info(f"[API] Strategy comparison complete for {ticker}")
        
        return jsonify({
            'ticker': ticker,
            'days': days,
            'comparison': comparison
        }), 200
        
    except ValueError as e:
        logger.error(f"[API] Invalid parameter: {str(e)}")
        return jsonify({'error': f'Invalid parameter: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"[API] Strategy comparison failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
