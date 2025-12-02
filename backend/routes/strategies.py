"""
Strategies API Routes

Provides endpoints for listing strategies and getting help content.
Strategies are Python classes (code-defined), database stores only metadata.
"""

from flask import Blueprint, jsonify, request
import logging

from strategies import StrategyManager

logger = logging.getLogger(__name__)

strategies_bp = Blueprint('strategies', __name__)


@strategies_bp.route('/api/strategies', methods=['GET'])
def list_strategies():
    """
    List all available strategies.
    
    Returns:
        JSON with list of strategies (id, name, description, help_url)
    """
    try:
        strategies = StrategyManager.list_summary()
        
        return jsonify({
            'success': True,
            'strategies': strategies,
            'default_strategy_id': 1
        })
    
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategies_bp.route('/api/strategies/<int:strategy_id>', methods=['GET'])
def get_strategy(strategy_id: int):
    """
    Get detailed strategy information including weights.
    
    Args:
        strategy_id: Integer ID of the strategy
        
    Returns:
        JSON with full strategy details
    """
    try:
        if not StrategyManager.exists(strategy_id):
            return jsonify({
                'success': False,
                'error': f'Strategy {strategy_id} not found'
            }), 404
        
        strategy = StrategyManager.get(strategy_id)
        
        return jsonify({
            'success': True,
            'strategy': strategy.to_dict()
        })
    
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategies_bp.route('/api/strategies/<int:strategy_id>/help', methods=['GET'])
def get_strategy_help(strategy_id: int):
    """
    Get strategy help content (Markdown).
    
    Args:
        strategy_id: Integer ID of the strategy
        
    Query Parameters:
        format: 'markdown' (default) or 'html'
        
    Returns:
        JSON with help content
    """
    try:
        if not StrategyManager.exists(strategy_id):
            return jsonify({
                'success': False,
                'error': f'Strategy {strategy_id} not found'
            }), 404
        
        strategy = StrategyManager.get(strategy_id)
        content = strategy.get_help_content()
        
        # Convert to HTML if requested
        format_type = request.args.get('format', 'markdown')
        
        if format_type == 'html':
            try:
                import markdown
                content = markdown.markdown(
                    content,
                    extensions=['tables', 'fenced_code', 'codehilite']
                )
            except ImportError:
                logger.warning("markdown module not installed, returning raw markdown")
        
        return jsonify({
            'success': True,
            'strategy_id': strategy_id,
            'name': strategy.name,
            'description': strategy.description,
            'help_content': content,
            'format': format_type
        })
    
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id} help: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@strategies_bp.route('/api/strategies/<int:strategy_id>/weights', methods=['GET'])
def get_strategy_weights(strategy_id: int):
    """
    Get indicator weights for a strategy.
    
    Args:
        strategy_id: Integer ID of the strategy
        
    Returns:
        JSON with indicator and category weights
    """
    try:
        if not StrategyManager.exists(strategy_id):
            return jsonify({
                'success': False,
                'error': f'Strategy {strategy_id} not found'
            }), 404
        
        strategy = StrategyManager.get(strategy_id)
        
        return jsonify({
            'success': True,
            'strategy_id': strategy_id,
            'name': strategy.name,
            'indicator_weights': strategy.get_indicator_weights(),
            'category_weights': strategy.get_category_weights(),
            'indicator_params': strategy.get_indicator_params(),
            'risk_profile': strategy.get_risk_profile()
        })
    
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id} weights: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
