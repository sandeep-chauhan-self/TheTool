from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from pathlib import Path

from db import (
    init_db_if_needed,
    query_db,
    execute_db,
    close_db
)

app = Flask(__name__)

# ---------- CORS (Vercel → Railway) ----------
FRONTEND_URL = "https://the-tool-theta.vercel.app"

CORS(
    app,
    resources={r"/*": {"origins": [FRONTEND_URL]}},
    supports_credentials=False,
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type", "X-API-Key"],
)

# ---------- DB CLOSE ----------
app.teardown_appcontext(close_db)

# ---------- DB INIT (Gunicorn SAFE) ----------
@app.before_request
def ensure_db_initialized():
    init_db_if_needed()


# ---------- AUTH ----------
@app.before_request
def require_api_key():
    if request.method == "OPTIONS":
        return
    if request.path == "/health":
        return
    
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return jsonify({
            "error": "Unauthorized",
            "message": "Missing X-API-Key"
        }), 401


# ---------- ROUTES ----------
@app.route("/")
def index():
    return {"status": "ok", "message": "Railway backend running"}

@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    rows = query_db("SELECT id, symbol, name FROM watchlist")
    return jsonify([
        {"id": row["id"], "symbol": row["symbol"], "name": row["name"]}
        for row in rows
    ])


@app.route("/watchlist", methods=["POST"])
def add_watchlist():
    data = request.get_json()
    symbol = data.get("symbol")
    name = data.get("name", "")

    if not symbol:
        return {"error": "Symbol required"}, 400

    existing = query_db(
        "SELECT id FROM watchlist WHERE symbol = ?",
        (symbol,),
        one=True
    )

    if existing:
        return {"error": "Already exists", "already_exists": True}, 409

    execute_db(
        "INSERT INTO watchlist (symbol, name) VALUES (?, ?)",
        (symbol, name)
    )

    return {"message": "Added", "symbol": symbol}, 201


@app.route("/watchlist", methods=["DELETE"])
def delete_watchlist():
    data = request.get_json()
    symbol = data.get("symbol")
    execute_db("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
    return {"message": "Removed"}


@app.route("/nse-stocks", methods=["GET"])
def get_nse_stocks():
    try:
        backend_root = Path(__file__).parent
        file_txt = backend_root / "backend" / "data" / "nse_stocks.txt"
        file_json = backend_root / "backend" / "data" / "nse_stocks.json"

        if file_json.exists():
            return jsonify(json.loads(file_json.read_text()))

        if file_txt.exists():
            stocks = [x.strip() for x in file_txt.read_text().split("\n") if x.strip()]
            return jsonify({
                "count": len(stocks),
                "stocks": [
                    {"symbol": s, "yahoo_symbol": s, "name": s.replace(".NS", "")}
                    for s in stocks
                ]
            })

        return {"error": "NSE stock file not found"}, 404

    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
