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
    """GET: Retrieve watchlist items, optionally filtered by collection"""
    try:
        # Get optional collection_id filter from query params
        collection_id = request.args.get('collection_id')
        
        if collection_id == 'null' or collection_id == 'default':
            # Filter for Default collection (NULL collection_id)
            items = query_db("""
                SELECT id, ticker, name, created_at, collection_id
                FROM watchlist
                WHERE collection_id IS NULL
                ORDER BY created_at DESC
            """)
        elif collection_id is not None:
            # Filter by specific collection
            items = query_db("""
                SELECT id, ticker, name, created_at, collection_id
                FROM watchlist
                WHERE collection_id = ?
                ORDER BY created_at DESC
            """, (int(collection_id),))
        else:
            # No filter - return all (backward compatible)
            items = query_db("""
                SELECT id, ticker, name, created_at, collection_id
                FROM watchlist
                ORDER BY created_at DESC
            """)
        
        logger.info(f"[WATCHLIST_GET] Query returned type: {type(items)}, len: {len(items)}")
        
        # Handle both tuple (PostgreSQL) and dict (SQLite) return types
        items_dict = []
        if items:  # Only iterate if items is not None/empty
            for idx, item in enumerate(items):
                if isinstance(item, (tuple, list)):
                    items_dict.append({
                        "id": item[0],
                        "ticker": item[1],
                        "name": item[2],
                        "created_at": str(item[3]) if item[3] else None,
                        "collection_id": item[4]
                    })
                else:
                    # Convert Row object to dict
                    item_dict = dict(item)
                    items_dict.append(item_dict)
        
        logger.info(f"[WATCHLIST_GET] Retrieved {len(items_dict)} items")
        
        # Log items with empty ticker for debugging
        empty_ticker_items = [item for item in items_dict if not item.get('ticker') or item.get('ticker').strip() == '']
        if empty_ticker_items:
            logger.warning(f"[WATCHLIST_GET] Found {len(empty_ticker_items)} items with empty ticker: {empty_ticker_items}")
        
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
        
        # Check if already exists (search by ticker)
        existing = query_db(
            "SELECT id FROM watchlist WHERE LOWER(ticker) = LOWER(?)",
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
        
        # Insert new item
        item_id = execute_db(
            """
            INSERT INTO watchlist (ticker, name)
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
                "SELECT ticker FROM watchlist WHERE id = ?",
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
            # Handle tuple (PostgreSQL) return type
            if isinstance(result, (tuple, list)):
                symbol_name = result[0]
            else:
                symbol_name = result['ticker']
            
            execute_db("DELETE FROM watchlist WHERE id = ?", (item_id,))
            logger.info(f"[WATCHLIST_DELETE] Removed by ID - item_id: {item_id}, symbol: {symbol_name}")
        else:
            symbol_name = symbol
            execute_db(
                "DELETE FROM watchlist WHERE LOWER(ticker) = LOWER(?)",
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


@bp.route("/debug/list", methods=["GET"])
def debug_list_watchlist():
    """DEBUG ENDPOINT: List all watchlist items and database info"""
    try:
        items = query_db("SELECT id, ticker, name, created_at FROM watchlist ORDER BY id DESC")
        
        items_list = []
        if items:
            for item in items:
                if isinstance(item, (tuple, list)):
                    items_list.append({
                        "id": item[0],
                        "ticker": item[1],
                        "name": item[2],
                        "created_at": str(item[3]) if item[3] else None
                    })
                else:
                    item_dict = dict(item)
                    items_list.append(item_dict)
        
        logger.info(f"[DEBUG] Watchlist has {len(items_list)} items")
        return jsonify({
            "debug": True,
            "total_items": len(items_list),
            "items": items_list
        }), 200
    except Exception as e:
        logger.error(f"[DEBUG] Error listing watchlist: {e}")
        return {"error": str(e)}, 500


@bp.route("/debug/cleanup", methods=["POST"])
def debug_cleanup_watchlist():
    """DEBUG ENDPOINT: Clean up orphaned/duplicate watchlist entries"""
    try:
        # Delete duplicates keeping the oldest one
        deleted = execute_db("""
            DELETE FROM watchlist 
            WHERE id NOT IN (
                SELECT MIN(id) FROM watchlist GROUP BY LOWER(ticker)
            )
        """)
        
        logger.info(f"[DEBUG] Cleaned up {deleted} duplicate entries")
        
        # Get remaining items
        items = query_db("SELECT id, ticker, name, created_at FROM watchlist ORDER BY id DESC")
        items_list = []
        if items:
            for item in items:
                if isinstance(item, (tuple, list)):
                    items_list.append({
                        "id": item[0],
                        "ticker": item[1],
                        "name": item[2],
                        "created_at": str(item[3]) if item[3] else None
                    })
                else:
                    item_dict = dict(item)
                    items_list.append(item_dict)
        
        return jsonify({
            "debug": True,
            "action": "cleanup_duplicates",
            "deleted_count": deleted,
            "remaining_items": len(items_list),
            "items": items_list
        }), 200
    except Exception as e:
        logger.error(f"[DEBUG] Error cleaning up watchlist: {e}")
        return {"error": str(e)}, 500


