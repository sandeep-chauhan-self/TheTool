"""
Watchlist routes - User watchlist management
"""
import csv
from pathlib import Path
from flask import Blueprint, request, jsonify
from utils.logger import setup_logger
from utils.api_utils import (
    StandardizedErrorResponse,
    validate_request,
    RequestValidator
)
from database import query_db, execute_db, get_db_connection
import json

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
        
        ticker = validated_data.get("ticker", "").strip()
        symbol = validated_data.get("symbol", "").strip()
        notes = validated_data.get("notes", "").strip()
        
        # Check if already exists
        existing = query_db(
            "SELECT id FROM watchlist WHERE LOWER(ticker) = LOWER(?)",
            (ticker,),
            one=True
        )
        
        if existing:
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
        
        logger.info(f"Added {ticker} to watchlist")
        
        return jsonify({
            "id": item_id,
            "ticker": ticker,
            "symbol": symbol,
            "notes": notes,
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
        ticker = data.get("ticker")
        
        if not item_id and not ticker:
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
                return StandardizedErrorResponse.format(
                    "WATCHLIST_NOT_FOUND",
                    f"Watchlist item {item_id} not found",
                    404
                )
            ticker_name = result['ticker']
            execute_db("DELETE FROM watchlist WHERE id = ?", (item_id,))
        else:
            ticker_name = ticker
            execute_db(
                "DELETE FROM watchlist WHERE LOWER(ticker) = LOWER(?)",
                (ticker,)
            )
        
        logger.info(f"Removed {ticker_name} from watchlist")
        
        return jsonify({
            "message": "Removed from watchlist",
            "ticker": ticker_name
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to remove from watchlist: {e}")
        return StandardizedErrorResponse.format(
            "WATCHLIST_DELETE_ERROR",
            "Failed to remove from watchlist",
            500,
            {"error": str(e)}
        )


@bp.route("/populate-all", methods=["POST"])
def populate_all():
    """
    Bulk populate watchlist with all NSE stocks from CSV.
    WARNING: This clears existing watchlist and loads ~2200 stocks.
    
    Request body:
    {
        "confirm": true
    }
    """
    try:
        data = request.get_json() or {}
        
        if not data.get("confirm"):
            return StandardizedErrorResponse.format(
                "CONFIRMATION_REQUIRED",
                "Set confirm=true to proceed with bulk population",
                400
            )
        
        # Get CSV path
        csv_path = Path(__file__).parent.parent / "data" / "nse_stocks_complete.csv"
        
        if not csv_path.exists():
            return StandardizedErrorResponse.format(
                "FILE_NOT_FOUND",
                "NSE stocks CSV not found",
                404
            )
        
        # Read CSV
        stocks_to_insert = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                symbol = row['symbol'].strip()
                name = row.get('name', '').strip()
                yahoo_symbol = row.get('yahoo_symbol', '').strip()
                
                # Use yahoo_symbol as ticker, symbol as symbol
                ticker = yahoo_symbol if yahoo_symbol else f"{symbol}.NS"
                stocks_to_insert.append((ticker, symbol, name))
        
        logger.info(f"Read {len(stocks_to_insert)} stocks from CSV")
        
        # Get DB connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing watchlist
        cursor.execute("DELETE FROM watchlist")
        logger.info("Cleared existing watchlist")
        
        # Bulk insert
        inserted = 0
        failed = 0
        
        for ticker, symbol, notes in stocks_to_insert:
            try:
                cursor.execute(
                    "INSERT INTO watchlist (ticker, symbol, notes) VALUES (?, ?, ?)",
                    (ticker, symbol, notes)
                )
                inserted += 1
                if inserted % 500 == 0:
                    logger.info(f"Inserted {inserted} stocks...")
            except Exception as e:
                logger.warning(f"Failed to insert {ticker}: {e}")
                failed += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Watchlist population complete: {inserted} inserted, {failed} failed")
        
        return jsonify({
            "message": "Watchlist populated successfully",
            "inserted": inserted,
            "failed": failed,
            "total": len(stocks_to_insert)
        }), 200
        
    except Exception as e:
        logger.exception("populate_all error")
        return StandardizedErrorResponse.format(
            "POPULATE_ERROR",
            "Failed to populate watchlist",
            500,
            {"error": str(e)}
        )
