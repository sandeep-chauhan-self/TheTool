"""
Watchlist Collections routes - Named watchlist management
Allows users to create multiple watchlists with custom names
"""
from flask import Blueprint, request, jsonify
from utils.logger import setup_logger
from utils.api_utils import StandardizedErrorResponse
from database import query_db, execute_db

logger = setup_logger()
bp = Blueprint("watchlist_collections", __name__, url_prefix="/api/watchlist-collections")


@bp.route("", methods=["GET"])
def get_all_collections():
    """GET: Retrieve all watchlist collections"""
    try:
        collections = query_db("""
            SELECT id, name, description, created_at
            FROM watchlist_collections
            ORDER BY name ASC
        """)
        
        result = []
        if collections:
            for item in collections:
                if isinstance(item, (tuple, list)):
                    result.append({
                        "id": item[0],
                        "name": item[1],
                        "description": item[2],
                        "created_at": str(item[3]) if item[3] else None
                    })
                else:
                    result.append(dict(item))
        
        # Get stock count for each collection
        for collection in result:
            count_result = query_db(
                "SELECT COUNT(*) FROM watchlist WHERE collection_id = ?",
                (collection["id"],),
                one=True
            )
            if count_result:
                collection["stock_count"] = count_result[0] if isinstance(count_result, (tuple, list)) else count_result.get("count", 0)
            else:
                collection["stock_count"] = 0
        
        # Also add count for "Default" (collection_id IS NULL)
        default_count = query_db(
            "SELECT COUNT(*) FROM watchlist WHERE collection_id IS NULL",
            one=True
        )
        default_stock_count = 0
        if default_count:
            default_stock_count = default_count[0] if isinstance(default_count, (tuple, list)) else default_count.get("count", 0)
        
        # Insert "Default" collection at the beginning
        result.insert(0, {
            "id": None,
            "name": "Default",
            "description": "Default watchlist",
            "created_at": None,
            "stock_count": default_stock_count
        })
        
        logger.info(f"[COLLECTIONS_GET] Retrieved {len(result)} collections")
        
        return jsonify({
            "collections": result,
            "count": len(result)
        }), 200
        
    except Exception as e:
        logger.error(f"[COLLECTIONS_GET] Failed: {e}")
        return StandardizedErrorResponse.format(
            "COLLECTIONS_FETCH_ERROR",
            "Failed to retrieve watchlist collections",
            500,
            {"error": str(e)}
        )


@bp.route("", methods=["POST"])
def create_collection():
    """POST: Create a new watchlist collection"""
    try:
        data = request.get_json() or {}
        
        name = data.get("name", "").strip()
        description = data.get("description", "").strip()
        
        if not name:
            return StandardizedErrorResponse.format(
                "INVALID_REQUEST",
                "Collection name is required",
                400
            )
        
        if len(name) > 50:
            return StandardizedErrorResponse.format(
                "INVALID_REQUEST",
                "Collection name must be 50 characters or less",
                400
            )
        
        # Check for duplicate name
        existing = query_db(
            "SELECT id FROM watchlist_collections WHERE LOWER(name) = LOWER(?)",
            (name,),
            one=True
        )
        
        if existing:
            return StandardizedErrorResponse.format(
                "COLLECTION_DUPLICATE",
                f"A collection named '{name}' already exists",
                409
            )
        
        # Create collection
        collection_id = execute_db(
            "INSERT INTO watchlist_collections (name, description) VALUES (?, ?)",
            (name, description)
        )
        
        logger.info(f"[COLLECTIONS_CREATE] Created collection: {name} (ID: {collection_id})")
        
        return jsonify({
            "id": collection_id,
            "name": name,
            "description": description,
            "message": "Collection created successfully"
        }), 201
        
    except Exception as e:
        logger.error(f"[COLLECTIONS_CREATE] Failed: {e}")
        return StandardizedErrorResponse.format(
            "COLLECTION_CREATE_ERROR",
            "Failed to create collection",
            500,
            {"error": str(e)}
        )


@bp.route("/<int:collection_id>", methods=["DELETE"])
def delete_collection(collection_id):
    """DELETE: Delete a watchlist collection (moves stocks to Default)"""
    try:
        # Check if collection exists
        existing = query_db(
            "SELECT id, name FROM watchlist_collections WHERE id = ?",
            (collection_id,),
            one=True
        )
        
        if not existing:
            return StandardizedErrorResponse.format(
                "COLLECTION_NOT_FOUND",
                f"Collection {collection_id} not found",
                404
            )
        
        collection_name = existing[1] if isinstance(existing, (tuple, list)) else existing.get("name")
        
        # Move all stocks from this collection to Default (NULL)
        execute_db(
            "UPDATE watchlist SET collection_id = NULL WHERE collection_id = ?",
            (collection_id,)
        )
        
        # Delete the collection
        execute_db(
            "DELETE FROM watchlist_collections WHERE id = ?",
            (collection_id,)
        )
        
        logger.info(f"[COLLECTIONS_DELETE] Deleted collection: {collection_name} (ID: {collection_id})")
        
        return jsonify({
            "message": f"Collection '{collection_name}' deleted. Stocks moved to Default.",
            "collection_id": collection_id
        }), 200
        
    except Exception as e:
        logger.error(f"[COLLECTIONS_DELETE] Failed: {e}")
        return StandardizedErrorResponse.format(
            "COLLECTION_DELETE_ERROR",
            "Failed to delete collection",
            500,
            {"error": str(e)}
        )


@bp.route("/<int:collection_id>/stocks", methods=["GET"])
def get_collection_stocks(collection_id):
    """GET: Retrieve all stocks in a specific collection"""
    try:
        items = query_db("""
            SELECT id, ticker, name, created_at
            FROM watchlist
            WHERE collection_id = ?
            ORDER BY created_at DESC
        """, (collection_id,))
        
        result = []
        if items:
            for item in items:
                if isinstance(item, (tuple, list)):
                    result.append({
                        "id": item[0],
                        "ticker": item[1],
                        "name": item[2],
                        "created_at": str(item[3]) if item[3] else None
                    })
                else:
                    result.append(dict(item))
        
        return jsonify({
            "stocks": result,
            "count": len(result),
            "collection_id": collection_id
        }), 200
        
    except Exception as e:
        logger.error(f"[COLLECTION_STOCKS_GET] Failed: {e}")
        return StandardizedErrorResponse.format(
            "COLLECTION_STOCKS_ERROR",
            "Failed to retrieve collection stocks",
            500,
            {"error": str(e)}
        )


@bp.route("/add-stocks", methods=["POST"])
def add_stocks_to_collection():
    """POST: Add multiple stocks to a watchlist collection"""
    try:
        data = request.get_json() or {}
        
        collection_id = data.get("collection_id")  # None = Default
        stocks = data.get("stocks", [])  # List of {symbol, name} or just symbols
        
        if not stocks:
            return StandardizedErrorResponse.format(
                "INVALID_REQUEST",
                "No stocks provided",
                400
            )
        
        # Validate collection exists (if not Default)
        if collection_id is not None:
            existing = query_db(
                "SELECT id FROM watchlist_collections WHERE id = ?",
                (collection_id,),
                one=True
            )
            if not existing:
                return StandardizedErrorResponse.format(
                    "COLLECTION_NOT_FOUND",
                    f"Collection {collection_id} not found",
                    404
                )
        
        added = []
        skipped = []
        
        for stock in stocks:
            # Handle both formats: {symbol, name} or just string symbol
            if isinstance(stock, dict):
                symbol = stock.get("symbol", "").strip().upper()
                name = stock.get("name", "").strip()
            else:
                symbol = str(stock).strip().upper()
                name = ""
            
            if not symbol:
                continue
            
            # Add .NS if no exchange code
            if '.' not in symbol:
                symbol = f"{symbol}.NS"
            
            # Check if already exists in this collection
            existing = query_db(
                "SELECT id FROM watchlist WHERE LOWER(ticker) = LOWER(?) AND (collection_id = ? OR (collection_id IS NULL AND ? IS NULL))",
                (symbol, collection_id, collection_id),
                one=True
            )
            
            if existing:
                skipped.append(symbol)
                continue
            
            # Insert
            execute_db(
                "INSERT INTO watchlist (ticker, name, collection_id) VALUES (?, ?, ?)",
                (symbol, name, collection_id)
            )
            added.append(symbol)
        
        logger.info(f"[ADD_STOCKS] Added {len(added)} stocks to collection {collection_id}, skipped {len(skipped)} duplicates")
        
        return jsonify({
            "message": f"Added {len(added)} stocks to watchlist",
            "added": added,
            "skipped": skipped,
            "collection_id": collection_id
        }), 201
        
    except Exception as e:
        logger.error(f"[ADD_STOCKS] Failed: {e}")
        return StandardizedErrorResponse.format(
            "ADD_STOCKS_ERROR",
            "Failed to add stocks to collection",
            500,
            {"error": str(e)}
        )


@bp.route("/move-stocks", methods=["POST"])
def move_stocks_to_collection():
    """POST: Move stocks from one collection to another"""
    try:
        data = request.get_json() or {}
        
        target_collection_id = data.get("target_collection_id")  # None = Default
        stock_ids = data.get("stock_ids", [])  # List of watchlist item IDs
        
        if not stock_ids:
            return StandardizedErrorResponse.format(
                "INVALID_REQUEST",
                "No stock IDs provided",
                400
            )
        
        # Validate target collection exists (if not Default)
        if target_collection_id is not None:
            existing = query_db(
                "SELECT id FROM watchlist_collections WHERE id = ?",
                (target_collection_id,),
                one=True
            )
            if not existing:
                return StandardizedErrorResponse.format(
                    "COLLECTION_NOT_FOUND",
                    f"Target collection {target_collection_id} not found",
                    404
                )
        
        # Update collection_id for all specified stocks
        placeholders = ','.join(['?' for _ in stock_ids])
        execute_db(
            f"UPDATE watchlist SET collection_id = ? WHERE id IN ({placeholders})",
            [target_collection_id] + stock_ids
        )
        
        logger.info(f"[MOVE_STOCKS] Moved {len(stock_ids)} stocks to collection {target_collection_id}")
        
        return jsonify({
            "message": f"Moved {len(stock_ids)} stocks",
            "target_collection_id": target_collection_id,
            "moved_count": len(stock_ids)
        }), 200
        
    except Exception as e:
        logger.error(f"[MOVE_STOCKS] Failed: {e}")
        return StandardizedErrorResponse.format(
            "MOVE_STOCKS_ERROR",
            "Failed to move stocks",
            500,
            {"error": str(e)}
        )
