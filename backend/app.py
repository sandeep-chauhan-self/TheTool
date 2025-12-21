"""
TheTool - Stock Analysis Application
Flask application factory with modular blueprint architecture
"""
import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request
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
from routes.watchlist_collections import bp as watchlist_collections_bp
from routes.stocks import bp as stocks_bp
from routes.admin import bp as admin_bp
from routes.strategies import strategies_bp
from routes.backtesting import bp as backtesting_bp


def create_app(config_object=None):
    """
    Application factory for creating Flask app.
    
    Args:
        config_object: Optional config object/dict to override defaults.
                      Accepts:
                      - Module or class with config attributes (uses app.config.from_object)
                      - Dict with config keys (uses app.config.update)
                      - None: uses default config from config module
    
    Returns:
        Flask application instance
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_object is not None:
        # Load provided config object or dict
        if isinstance(config_object, dict):
            app.config.update(config_object)
        else:
            # Assume it's a module or class with config attributes
            app.config.from_object(config_object)
    else:
        # Fall back to default config module
        app.config.update(
            DEBUG=config.DEBUG,
            TESTING=False,
            JSON_SORT_KEYS=False,
            JSONIFY_PRETTYPRINT_REGULAR=True
        )
    
    # Ensure critical Flask defaults are set if not provided
    if 'TESTING' not in app.config:
        app.config['TESTING'] = False
    if 'JSON_SORT_KEYS' not in app.config:
        app.config['JSON_SORT_KEYS'] = False
    if 'JSONIFY_PRETTYPRINT_REGULAR' not in app.config:
        app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    
    # Setup logging (idempotent, setup_logger handles deduplication)
    logger = setup_logger()
    
    # Display environment banner
    logger.info("=" * 70)
    logger.info(f"TheTool Starting - Environment: {config.APP_ENV.upper()} (debug={config.DEBUG})")
    logger.info(f"Log Level: {config.LOG_LEVEL}")
    logger.info("=" * 70)
    
    # Configure CORS - use config.CORS_ORIGINS property directly
    # This is a property that returns list of allowed origins
    cors_origins = config.CORS_ORIGINS
    
    logger.info(f"CORS enabled for origins: {cors_origins}")
    
    # Apply CORS to all routes with wildcard for maximum compatibility
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},  # Allow all origins - Railway edge may interfere
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization", "X-API-Key", "Accept", "Origin"],
        expose_headers=["Content-Type", "X-API-Key"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        max_age=3600,
        send_wildcard=True  # Send * instead of echoing origin
    )
    
    # CRITICAL: Add CORS headers to ALL responses including errors
    # This runs AFTER every request, including OPTIONS preflight
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to ALL responses unconditionally"""
        # Always add CORS headers - don't check origin (Railway edge may strip it)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Accept, Origin'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response
    
    # Handle OPTIONS preflight requests explicitly
    @app.before_request
    def handle_preflight():
        """Handle CORS preflight requests explicitly"""
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key, Accept, Origin'
            response.headers['Access-Control-Max-Age'] = '3600'
            return response
    
    # Configure rate limiting if available (log only in main process)
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        
        rate_limit_enabled = config.RATE_LIMIT_ENABLED
        
        if rate_limit_enabled:
            rate_limit_per_minute = config.RATE_LIMIT_PER_MINUTE
            
            limiter = Limiter(
                app=app,
                key_func=get_remote_address,
                default_limits=[f"{rate_limit_per_minute} per minute"],
                storage_uri="memory://",
            )
            # Attach limiter to app so it can be accessed via current_app.limiter
            app.limiter = limiter
            # Log only once in main/non-worker process
            if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('GUNICORN_CMD_ARGS'):
                logger.info("Rate limiting enabled")
        else:
            app.limiter = None
    except ImportError:
        logger.debug("Flask-Limiter not available, skipping rate limiting")
        app.limiter = None
    
    # Register error handlers (before_request, after_request, error handlers)
    register_error_handlers(app)
    
    # Initialize database on app startup (CRITICAL for Railway PostgreSQL)
    try:
        init_db()
        database_type = config.DATABASE_TYPE
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('GUNICORN_CMD_ARGS'):
            logger.info(f"[OK] Database initialized on startup ({database_type.upper()})")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")
    
    # Initialize database on first request as fallback
    @app.before_request
    def before_request():
        """Initialize database if needed on first request (fallback)"""
        try:
            init_db_if_needed()
        except Exception as e:
            logger.debug(f"Fallback init_db_if_needed: {e}")
    
    # Close database connection
    app.teardown_appcontext(close_db)
    
    # Run migrations on startup (idempotent, safe in multi-worker; log only once)
    try:
        run_migrations()
        # Log only in main/non-worker process
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('GUNICORN_CMD_ARGS'):
            logger.info("[OK] Database migrations completed")
            
            # Development diagnostics: show schema when in debug mode
            if config.DEBUG:
                try:
                    from database import get_db_connection
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    cursor.close()
                    conn.close()
                    logger.debug(f"Database tables: {', '.join(tables)}")
                except Exception as e:
                    logger.debug(f"Could not introspect database schema: {e}")
    except Exception as e:
        logger.warning(f"Migration warning (may already be initialized): {e}")
    
    # Register blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(watchlist_collections_bp)
    app.register_blueprint(stocks_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(backtesting_bp)
    
    # Log initialization only once (main process)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.environ.get('GUNICORN_CMD_ARGS'):
        flask_env = config.FLASK_ENV
        database_type = config.DATABASE_TYPE
        debug = config.DEBUG
        
        logger.info(f"Application created - Environment: {flask_env}")
        logger.info(f"Database: {database_type}")
        logger.info(f"Debug: {debug}")
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
