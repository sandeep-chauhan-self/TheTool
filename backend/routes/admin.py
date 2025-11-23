"""
Admin and utility routes - Health checks, config, system info
"""
from pathlib import Path
from flask import Blueprint, jsonify
from utils.logger import setup_logger
from database import query_db, get_db_connection
from config import config
import sys

logger = setup_logger()
bp = Blueprint("admin", __name__)


@bp.route("/", methods=["GET"])
def index():
    """Root endpoint - API info"""
    return jsonify({
        "app": "TheTool",
        "version": "2.0.0",
        "environment": config.FLASK_ENV,
        "api": "Stock Analysis API",
        "endpoints": {
            "analysis": "/api/analysis",
            "watchlist": "/api/watchlist",
            "stocks": "/api/stocks",
            "health": "/health",
            "config": "/config"
        }
    }), 200


@bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint with system diagnostics"""
    try:
        health_status = {
            "status": "healthy",
            "environment": config.FLASK_ENV,
            "database": "unknown",
            "components": {}
        }
        
        # Check database connectivity
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check core tables (whitelisted to prevent SQL injection)
            tables_to_check = [
                'analysis_results',
                'analysis_jobs',
                'watchlist'
            ]
            
            tables_ok = []
            for table in tables_to_check:
                try:
                    # Use parameterized query to safely check table counts
                    # Note: Table names cannot be parameterized in SQL, so we use whitelist
                    if table not in tables_to_check:
                        continue
                    query = f"SELECT COUNT(*) FROM {table}"
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    tables_ok.append(table)
                    health_status["components"][f"{table}_count"] = count
                except Exception as e:
                    health_status["components"][f"{table}_error"] = str(e)
            
            # Get version (simple SELECT without parameters needed)
            try:
                cursor.execute("SELECT version FROM db_version ORDER BY version DESC LIMIT 1")
                version = cursor.fetchone()
                health_status["components"]["db_version"] = version[0] if version else "unknown"
            except Exception as e:
                health_status["components"]["db_version_error"] = str(e)
            
            cursor.close()
            conn.close()
            
            health_status["database"] = "connected" if tables_ok else "error"
            health_status["components"]["tables_checked"] = len(tables_ok)
            
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["database"] = "disconnected"
            health_status["components"]["db_error"] = str(e)
        
        # Check config
        health_status["components"]["config_loaded"] = True
        health_status["components"]["debug_mode"] = config.DEBUG
        health_status["components"]["rate_limiting"] = config.RATE_LIMIT_ENABLED
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.exception("health check error")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@bp.route("/config", methods=["GET"])
def get_config():
    """Get current configuration (non-sensitive)"""
    try:
        return jsonify({
            "environment": config.FLASK_ENV,
            "debug": config.DEBUG,
            "database_type": config.DATABASE_TYPE,
            "rate_limiting": config.RATE_LIMIT_ENABLED,
            "rate_limit_per_minute": config.RATE_LIMIT_PER_MINUTE if config.RATE_LIMIT_ENABLED else None,
            "cors_origins": config.CORS_ORIGINS,
            "features": {
                "redis": bool(config.REDIS_URL),
                "bulk_analysis": True,
                "watchlist": True,
                "export": True
            }
        }), 200
        
    except Exception as e:
        logger.exception("get_config error")
        return jsonify({"error": str(e)}), 500
