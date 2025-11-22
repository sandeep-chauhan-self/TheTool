from flask import Flask, jsonify, request
from flask_cors import CORS
from db import init_db_if_needed, query_db, execute_db, close_db
from pathlib import Path
import json

app = Flask(__name__)

# ---------- GLOBAL CORS ----------
CORS(
    app,
    resources={r"/*": {"origins": ["https://the-tool-theta.vercel.app"]}},
    supports_credentials=False,
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    expose_headers=["Content-Type", "X-API-Key"],
)

# Ensure DB connection cleanup
app.teardown_appcontext(close_db)

# ---------- DB INIT (Gunicorn-safe) ----------
@app.before_request
def ensure_db():
    init_db_if_needed()


# ---------- AUTH ----------
@app.before_request
def require_api_key():
    if request.path in ["/health", "/"]:
        return
    if request.method == "OPTIONS":
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
    return {"status": "ok", "message": "Backend running"}

@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/watchlist", methods=["GET"])
def get_watchlist():
    rows = query_db("SELECT id, symbol, name FROM watchlist")
    return jsonify([
        {"id": r["id"], "symbol": r["symbol"], "name": r["name"]}
        for r in rows
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
        (symbol,), one=True
    )

    if existing:
        return {"error": "Symbol exists", "already_exists": True}, 409

    execute_db("INSERT INTO watchlist (symbol, name) VALUES (?, ?)", (symbol, name))
    return {"message": "Added", "symbol": symbol}, 201


@app.route("/watchlist", methods=["DELETE"])
def delete_watchlist():
    data = request.get_json()
    symbol = data.get("symbol")
    execute_db("DELETE FROM watchlist WHERE symbol = ?", (symbol,))
    return {"message": "Removed"}


@app.route('/nse-stocks', methods=['GET'])
def get_nse_stocks():
    try:
        from pathlib import Path
        import json

        backend_root = Path(__file__).resolve().parent / "data"

        json_file = backend_root / "nse_stocks.json"
        txt_file = backend_root / "nse_stocks.txt"

        if json_file.exists():
            return jsonify(json.loads(json_file.read_text()))

        if txt_file.exists():
            stocks = [
                line.strip() for line in txt_file.read_text().splitlines()
                if line.strip()
            ]
            return jsonify({
                "count": len(stocks),
                "stocks": [
                    {
                        "symbol": s,
                        "yahoo_symbol": s,
                        "name": s.replace(".NS", "")
                    } for s in stocks
                ]
            })

        return jsonify({
            "error": "NSE stocks list not found.",
            "count": 0,
            "stocks": []
        }), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
