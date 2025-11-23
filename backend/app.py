"""
TheTool - Stock Analysis Application
Flask application factory with modular blueprint architecture
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Import configuration
from config import config

# Import database and migrations
from database import init_db, init_db_if_needed, close_db
from db_migrations import run_migrations
from utils.logger import setup_logger
from utils.api_utils import register_error_handlers

# Import blueprints
from routes.analysis import bp as analysis_bp
from routes.watchlist import bp as watchlist_bp
from routes.stocks import bp as stocks_bp
from routes.admin import bp as admin_bp


def create_app(config_object=None):
    """
    Application factory for creating Flask app.
    
    Args:
        config_object: Optional config object (defaults to config.py)
    
    Returns:
        Flask application instance
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.config.update(
        DEBUG=config.DEBUG,
        TESTING=False,
        JSON_SORT_KEYS=False,
        JSONIFY_PRETTYPRINT_REGULAR=True
    )
    
    # Setup logging (idempotent, setup_logger handles deduplication)
    logger = setup_logger()
    
    # Configure CORS
    cors_origins = getattr(config, "CORS_ORIGINS", [
        "https://the-tool-theta.vercel.app",
        "https://thetool-production.up.railway.app",
        "http://192.168.57.1:3000",
        "http://localhost:3000"
    ])
    
    CORS(
        app,
        resources={r"/*": {"origins": cors_origins}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization", "X-API-Key"],
        expose_headers=["Content-Type", "X-API-Key"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    
    # Configure rate limiting if available (log only in main process)
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        if config.RATE_LIMIT_ENABLED:
            limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                default_limits=[f"{config.RATE_LIMIT_PER_MINUTE} per minute"],
                storage_uri="memory://",
            )
            # Log only once in main/non-worker process
            if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('GUNICORN_CMD_ARGS'):
                logger.info("Rate limiting enabled")
    except ImportError:
        logger.debug("Flask-Limiter not available, skipping rate limiting")
    
    # Register error handlers (before_request, after_request, error handlers)
    register_error_handlers(app)
    
    # Initialize database
    @app.before_request
    def before_request():
        """Initialize database if needed on first request"""
        init_db_if_needed()
    
    # Close database connection
    app.teardown_appcontext(close_db)
    
    # Run migrations on startup (idempotent, safe in multi-worker; log only once)
    try:
        run_migrations()
        # Log only in main/non-worker process
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('GUNICORN_CMD_ARGS'):
            logger.info("[OK] Database migrations completed")
    except Exception as e:
        logger.warning(f"Migration warning (may already be initialized): {e}")
    
    # Register blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(stocks_bp)
    
    # Log initialization only once (main process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('GUNICORN_CMD_ARGS'):
        logger.info(f"Application created - Environment: {config.FLASK_ENV}")
        logger.info(f"Database: {config.DATABASE_TYPE}")
        logger.info(f"Debug: {config.DEBUG}")
        logger.info(f"CORS Origins: {len(cors_origins)} configured")
    
    return app


# Create default app instance
app = create_app()


# Production entry point
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.getenv("FLASK_ENV") == "development",
        use_reloader=False
    )
