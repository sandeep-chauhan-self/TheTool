"""
Watchlist routes - User watchlist management
"""
from flask import Blueprint, request, jsonify
from utils.logger import setup_logger
from utils.api_utils import (
    StandardizedErrorResponse,
    validate_request,
    RequestValidator
)
from database import query_db, execute_db
from auth import require_auth
import json

logger = setup_logger()
bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")


@bp.route("", methods=["GET", "POST", "DELETE"])
@require_auth
def watchlist():
    """
    Manage user watchlist.
    
    GET: Retrieve all watchlist items
    POST: Add item to watchlist
    DELETE: Remove item from watchlist
    """
    try:
        if request.method == "GET":
            return _get_watchlist()
        elif request.method == "POST":
            return _add_to_watchlist()
        elif request.method == "DELETE":
            return _remove_from_watchlist()
            
    except Exception as e:
        logger.exception("watchlist error")
        return StandardizedErrorResponse.format(
            "WATCHLIST_ERROR",
            "Watchlist operation failed",
            500,
            {"error": str(e)}
        )


def _get_watchlist():
    """GET: Retrieve watchlist items"""
    try:
        items = query_db("""
            SELECT id, symbol, name, created_at
            FROM watchlist
            ORDER BY created_at DESC
        """)
        
        return jsonify({
            "watchlist": [dict(item) for item in items],
            "count": len(items)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get watchlist: {e}")
        return StandardizedErrorResponse.format(
            "WATCHLIST_FETCH_ERROR",
            "Failed to retrieve watchlist",
            500,
            {"error": str(e)}
        )


def _add_to_watchlist():
    """POST: Add item to watchlist"""
    try:
        data = request.get_json() or {}
        
        # Validate request
        validated_data, error_response = validate_request(
            data,
            RequestValidator.WatchlistAddRequest
        )
        if error_response:
            return error_response
        
        symbol = validated_data.get("symbol", "").strip()
        name = validated_data.get("name", "").strip()
        
        # Check if already exists
        existing = query_db(
            "SELECT id FROM watchlist WHERE LOWER(symbol) = LOWER(?)",
            (symbol,),
            one=True
        )
        
        if existing:
            return StandardizedErrorResponse.format(
                "WATCHLIST_DUPLICATE",
                f"Symbol {symbol} already in watchlist",
                409
            )
        
        # Insert new item
        item_id = execute_db(
            """
            INSERT INTO watchlist (symbol, name)
            VALUES (?, ?)
            """,
            (symbol, name)
        )
        
        logger.info(f"Added {symbol} to watchlist")
        
        return jsonify({
            "id": item_id,
            "symbol": symbol,
            "name": name,
            "message": "Added to watchlist"
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to add to watchlist: {e}")
        return StandardizedErrorResponse.format(
            "WATCHLIST_ADD_ERROR",
            "Failed to add to watchlist",
            500,
            {"error": str(e)}
        )


def _remove_from_watchlist():
    """DELETE: Remove item from watchlist"""
    try:
        data = request.get_json() or {}
        
        item_id = data.get("id")
        symbol = data.get("symbol")
        
        if not item_id and not symbol:
            return StandardizedErrorResponse.format(
                "INVALID_REQUEST",
                "Provide either 'id' or 'symbol'",
                400
            )
        
        # Build query
        if item_id:
            result = query_db(
                "SELECT symbol FROM watchlist WHERE id = ?",
                (item_id,),
                one=True
            )
            if not result:
                return StandardizedErrorResponse.format(
                    "WATCHLIST_NOT_FOUND",
                    f"Watchlist item {item_id} not found",
                    404
                )
            symbol_name = result['symbol']
            execute_db("DELETE FROM watchlist WHERE id = ?", (item_id,))
        else:
            symbol_name = symbol
            execute_db(
                "DELETE FROM watchlist WHERE LOWER(symbol) = LOWER(?)",
                (symbol,)
            )
        
        logger.info(f"Removed {symbol_name} from watchlist")
        
        return jsonify({
            "message": "Removed from watchlist",
            "symbol": symbol_name
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        return StandardizedErrorResponse.format(
            "WATCHLIST_DELETE_ERROR",
            "Failed to remove from watchlist",
            500,
            {"error": str(e)}
        )
