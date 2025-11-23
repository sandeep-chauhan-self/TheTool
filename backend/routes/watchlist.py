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
            SELECT id, ticker, symbol, notes, created_at
            FROM watchlist
            ORDER BY created_at DESC
        """)
        
        items_dict = [dict(item) for item in items]
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
        notes = data.get("notes", "").strip()
        
        logger.info(f"[WATCHLIST_ADD] Validated symbol: {symbol}, name: {name}")
        
        # Convert symbol to ticker format (add .NS as default exchange)
        # If symbol already contains an exchange code, use it as-is
        if '.' in symbol:
            ticker = symbol
        else:
            # Default to .NS (NSE) if no exchange code provided
            ticker = f"{symbol}.NS"
        
        logger.info(f"[WATCHLIST_ADD] Generated ticker: {ticker}")
        
        # Check if already exists (search by ticker)
        existing = query_db(
            "SELECT id FROM watchlist WHERE LOWER(ticker) = LOWER(?)",
            (ticker,),
            one=True
        )
        
        if existing:
            logger.warning(f"[WATCHLIST_ADD] Duplicate ticker: {ticker}")
            return StandardizedErrorResponse.format(
                "WATCHLIST_DUPLICATE",
                f"Ticker {ticker} already in watchlist",
                409
            )
        
        # Insert new item
        item_id = execute_db(
            """
            INSERT INTO watchlist (ticker, symbol, notes)
            VALUES (?, ?, ?)
            """,
            (ticker, symbol, notes)
        )
        
        logger.info(f"[WATCHLIST_ADD] Successfully added - ID: {item_id}, ticker: {ticker}, symbol: {symbol}")
        
        return jsonify({
            "id": item_id,
            "ticker": ticker,
            "symbol": symbol,
            "notes": notes,
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
        ticker = data.get("ticker")
        
        if not item_id and not ticker:
            logger.warning("[WATCHLIST_DELETE] No id or ticker provided")
            return StandardizedErrorResponse.format(
                "INVALID_REQUEST",
                "Provide either 'id' or 'ticker'",
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
            ticker_name = result['ticker']
            execute_db("DELETE FROM watchlist WHERE id = ?", (item_id,))
            logger.info(f"[WATCHLIST_DELETE] Removed by ID - item_id: {item_id}, ticker: {ticker_name}")
        else:
            ticker_name = ticker
            execute_db(
                "DELETE FROM watchlist WHERE LOWER(ticker) = LOWER(?)",
                (ticker,)
            )
            logger.info(f"[WATCHLIST_DELETE] Removed by ticker: {ticker_name}")
        
        return jsonify({
            "message": "Removed from watchlist",
            "ticker": ticker_name
        }), 200
        
    except Exception as e:
        logger.error(f"[WATCHLIST_DELETE] Failed to remove from watchlist: {e}")
        return StandardizedErrorResponse.format(
            "WATCHLIST_DELETE_ERROR",
            "Failed to remove from watchlist",
            500,
            {"error": str(e)}
        )

