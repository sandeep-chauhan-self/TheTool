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

logger = setup_logger()
bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")


@bp.route("", methods=["GET", "POST", "DELETE"])
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
        
        logger.info(f"[WATCHLIST_GET] Query returned type: {type(items)}, len: {len(items)}, items: {items}")
        
        # Handle both tuple (PostgreSQL) and dict (SQLite) return types
        items_dict = []
        if items:  # Only iterate if items is not None/empty
            for idx, item in enumerate(items):
                if isinstance(item, (tuple, list)):
                    items_dict.append({
                        "id": item[0],
                        "symbol": item[1],
                        "name": item[2],
                        "created_at": str(item[3]) if item[3] else None
                    })
                else:
                    # Convert Row object to dict
                    item_dict = dict(item)
                    items_dict.append(item_dict)
        
        logger.info(f"[WATCHLIST_GET] Retrieved {len(items_dict)} items: {items_dict}")
        
        # Log items with empty symbol for debugging
        empty_symbol_items = [item for item in items_dict if not item.get('symbol') or item.get('symbol').strip() == '']
        if empty_symbol_items:
            logger.warning(f"[WATCHLIST_GET] Found {len(empty_symbol_items)} items with empty symbol: {empty_symbol_items}")
        
        return jsonify({
            "watchlist": items_dict,
            "count": len(items_dict)
        }), 200
        
    except Exception as e:
        logger.error(f"[WATCHLIST_GET] Failed to get watchlist: {e}")
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
        
        logger.info(f"[WATCHLIST_ADD] Incoming request: {data}")
        
        # Validate request
        validated_data, error_response = validate_request(
            data,
            RequestValidator.WatchlistAddRequest
        )
        if error_response:
            logger.warning(f"[WATCHLIST_ADD] Validation failed: {error_response}")
            return error_response
        
        symbol = validated_data.get("symbol", "").strip().upper()
        name = validated_data.get("name", "").strip()
        
        logger.info(f"[WATCHLIST_ADD] Validated symbol: {symbol}, name: {name}")
        
        # Convert symbol to ticker format (add .NS as default exchange)
        # If symbol already contains an exchange code, use it as-is
        if '.' in symbol:
            symbol_with_exchange = symbol
        else:
            # Default to .NS (NSE) if no exchange code provided
            symbol_with_exchange = f"{symbol}.NS"
        
        logger.info(f"[WATCHLIST_ADD] Generated symbol: {symbol_with_exchange}")
        
        # Check if already exists (search by symbol)
        existing = query_db(
            "SELECT id FROM watchlist WHERE LOWER(symbol) = LOWER(?)",
            (symbol_with_exchange,),
            one=True
        )
        
        if existing:
            logger.warning(f"[WATCHLIST_ADD] Duplicate symbol: {symbol_with_exchange}")
            return StandardizedErrorResponse.format(
                "WATCHLIST_DUPLICATE",
                f"Symbol {symbol_with_exchange} already in watchlist",
                409
            )
        
        # Insert new item (only using columns that exist: symbol, name)
        item_id = execute_db(
            """
            INSERT INTO watchlist (symbol, name)
            VALUES (?, ?)
            """,
            (symbol_with_exchange, name)
        )
        
        logger.info(f"[WATCHLIST_ADD] Successfully added - ID: {item_id}, symbol: {symbol_with_exchange}")
        
        return jsonify({
            "id": item_id,
            "symbol": symbol_with_exchange,
            "name": name,
            "message": "Added to watchlist"
        }), 201
        
    except Exception as e:
        logger.error(f"[WATCHLIST_ADD] Failed to add to watchlist: {e}")
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
        
        logger.info(f"[WATCHLIST_DELETE] Incoming request: {data}")
        
        item_id = data.get("id")
        symbol = data.get("symbol") or data.get("ticker")  # Accept both symbol and ticker
        
        if not item_id and not symbol:
            logger.warning("[WATCHLIST_DELETE] No id or symbol provided")
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
                logger.warning(f"[WATCHLIST_DELETE] Item {item_id} not found")
                return StandardizedErrorResponse.format(
                    "WATCHLIST_NOT_FOUND",
                    f"Watchlist item {item_id} not found",
                    404
                )
            # Handle both tuple (PostgreSQL) and dict (SQLite) return types
            if isinstance(result, (tuple, list)):
                symbol_name = result[0]
            else:
                symbol_name = result['symbol']
            
            execute_db("DELETE FROM watchlist WHERE id = ?", (item_id,))
            logger.info(f"[WATCHLIST_DELETE] Removed by ID - item_id: {item_id}, symbol: {symbol_name}")
        else:
            symbol_name = symbol
            execute_db(
                "DELETE FROM watchlist WHERE LOWER(symbol) = LOWER(?)",
                (symbol,)
            )
            logger.info(f"[WATCHLIST_DELETE] Removed by symbol: {symbol_name}")
        
        return jsonify({
            "message": "Removed from watchlist",
            "symbol": symbol_name
        }), 200
        
    except Exception as e:
        logger.error(f"[WATCHLIST_DELETE] Failed to remove from watchlist: {e}")
        return StandardizedErrorResponse.format(
            "WATCHLIST_DELETE_ERROR",
            "Failed to remove from watchlist",
            500,
            {"error": str(e)}
        )

