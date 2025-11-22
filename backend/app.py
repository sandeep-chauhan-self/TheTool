from flask import Flask, jsonify, request
from flask_cors import CORS
import os

from db import get_db, query_db, execute_db, close_db
from auth import require_auth

app = Flask(__name__)

# ---------- GLOBAL CORS (Required for Railway/Vercel) ----------
CORS(
    app,
    resources={r"/*": {"origins": ["https://the-tool-theta.vercel.app"]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type", "X-API-Key"],
)

# Ensure DB closes after every request
app.teardown_appcontext(close_db)

# ---------- AUTH MIDDLEWARE ----------
@app.before_request
def require_api_key():
    # Skip health
    if request.path == "/health":
        return

    if not require_auth():
        return jsonify({
            "error": "Unauthorized",
            "message": "Invalid or missing API key."
        }), 401

# ---------- ROUTES ----------
@app.route("/")
def index():
    return {"status": "ok", "message": "Your Railway app is running!"}

@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "backend running"})

@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    rows = query_db("SELECT id, symbol, name FROM watchlist")
    return jsonify([{"id": r[0], "symbol": r[1], "name": r[2]} for r in rows])

@app.route("/watchlist", methods=["POST"])
def add_watchlist():
    data = request.get_json()
    symbol = data.get("symbol")
    name = data.get("name", "")

    if not symbol:
        return jsonify({"error": "Symbol is required"}), 400

    # Check if symbol already exists
    existing = query_db("SELECT id FROM watchlist WHERE symbol = ?", (symbol,), one=True)
    if existing:
        return jsonify({"error": "Symbol already in watchlist", "already_exists": True}), 409

    execute_db("INSERT INTO watchlist (symbol, name) VALUES (?, ?)", (symbol, name))
    return jsonify({"message": "Added to watchlist", "symbol": symbol}), 201

@app.route("/watchlist", methods=["DELETE"])
def delete_watchlist():
    data = request.get_json()
    symbol = data.get("symbol")

    execute_db("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
    return jsonify({"message": "Removed from watchlist"})

@app.route('/nse-stocks', methods=['GET'])
def get_nse_stocks():
    """Get list of all NSE stocks"""
    try:
        from pathlib import Path
        import json

        # Path to NSE stocks file
        stocks_file = Path(__file__).parent / 'data' / 'nse_stocks.txt'
        json_file = Path(__file__).parent / 'data' / 'nse_stocks.json'

        # If JSON file exists, return it (includes metadata)
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return jsonify(data)

        # Fallback: read TXT file
        if stocks_file.exists():
            with open(stocks_file, 'r', encoding='utf-8') as f:
                stocks = [line.strip() for line in f if line.strip()]
            return jsonify({
                'count': len(stocks),
                'stocks': [{'symbol': s, 'yahoo_symbol': s, 'name': s.replace('.NS', '')} for s in stocks]
            })

        # If file doesn't exist, return error
        return jsonify({
            'error': 'NSE stocks list not found. Run fetch_nse_stocks.py first.',
            'count': 0,
            'stocks': []
        }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_ENV') == 'development')
