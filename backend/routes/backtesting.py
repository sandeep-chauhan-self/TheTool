"""
Backtesting API endpoints

Following TheTool architecture:
- Thread-safe with get_db_session() for background job compatibility
- Uses _convert_query_params() for database abstraction (PostgreSQL/SQLite)
- Centralized logging via infrastructure.logger
- Error handling via api_utils.register_error_handlers
- Multi-strategy support (1-5)
"""

from flask import Blueprint, request, jsonify
from utils.backtesting import BacktestEngine, STRATEGY_CONFIGS
import logging

bp = Blueprint('backtesting', __name__, url_prefix='/api/backtest')
logger = logging.getLogger('trading_analyzer')


@bp.route('/strategies', methods=['GET'])
def get_strategies():
    """
    Get list of available strategies for backtesting.
    
    Returns:
        {
            'strategies': [
                {
                    'id': 1,
                    'name': 'Balanced Analysis',
                    'description': '...',
                    'params': { ... }
                },
                ...
            ]
        }
    """
    strategies = []
    for strategy_id, config in STRATEGY_CONFIGS.items():
        strategies.append({
            'id': strategy_id,
            'name': config['name'],
            'description': config['description'],
            'params': {
                'target_pct': config['target_pct'],
                'stop_loss_pct': config['stop_loss_pct'],
                'max_bars': config['max_bars'],
                'rsi_range': f"{config['rsi_min']}-{config['rsi_max']}",
            }
        })
    return jsonify({'strategies': strategies}), 200


@bp.route('/ticker/<ticker>', methods=['GET'])
def backtest_ticker(ticker):
    """
    Backtest a strategy on a single ticker.
    
    Query params:
    - days: Historical days to analyze (30-365, default 90)
    - strategy_id: Strategy to backtest (1-5, default 5)
    
    Example:
        GET /api/backtest/ticker/RELIANCE.NS?days=90&strategy_id=5
    
    Returns:
        {
            'ticker': 'RELIANCE.NS',
            'strategy_id': 5,
            'strategy_name': 'Weekly 4% Target',
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
        strategy_id = request.args.get('strategy_id', 5, type=int)
        
        # Validate
        if days < 30 or days > 365:
            return jsonify({'error': 'days must be between 30 and 365'}), 400
        
        if strategy_id not in STRATEGY_CONFIGS:
            return jsonify({'error': f'Invalid strategy_id: {strategy_id}. Must be 1-5.'}), 400
        
        logger.info(f"[API] Backtest request: {ticker} ({days} days, strategy_id={strategy_id})")
        
        # Run backtest
        engine = BacktestEngine(strategy_id=strategy_id)
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
            'days': 90,
            'strategy_id': 5
        }
    
    Returns:
        {
            'tickers_analyzed': 3,
            'strategy_id': 5,
            'strategy_name': 'Weekly 4% Target',
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
        strategy_id = data.get('strategy_id', 5)
        
        # Validate
        if not tickers:
            return jsonify({'error': 'tickers array required'}), 400
        
        if not isinstance(tickers, list):
            return jsonify({'error': 'tickers must be a list'}), 400
        
        if len(tickers) > 50:
            return jsonify({'error': 'Maximum 50 tickers per backtest'}), 400
        
        if days < 30 or days > 365:
            return jsonify({'error': 'days must be between 30 and 365'}), 400
        
        if strategy_id not in STRATEGY_CONFIGS:
            return jsonify({'error': f'Invalid strategy_id: {strategy_id}. Must be 1-5.'}), 400
        
        logger.info(f"[API] Portfolio backtest: {len(tickers)} tickers ({days} days, strategy_id={strategy_id})")
        
        # Run backtest for each ticker
        engine = BacktestEngine(strategy_id=strategy_id)
        results = {}
        
        for ticker in tickers:
            logger.debug(f"[API] Backtesting {ticker}...")
            results[ticker] = engine.backtest_ticker(ticker, days=days)
        
        logger.info(f"[API] Portfolio backtest complete: {len(tickers)} tickers")
        
        return jsonify({
            'tickers_analyzed': len(tickers),
            'days': days,
            'strategy_id': strategy_id,
            'strategy_name': STRATEGY_CONFIGS[strategy_id]['name'],
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
