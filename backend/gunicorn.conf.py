"""
Gunicorn configuration for production deployment on Railway and similar platforms

This config is auto-loaded by gunicorn when running with:
    gunicorn -c gunicorn.conf.py wsgi:app

Or on Railway, the platform automatically uses gunicorn with this config.
"""

import os
import multiprocessing
import logging

# Basic settings
bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
workers = max(2, multiprocessing.cpu_count())
worker_class = "sync"  # Use sync worker (safer for SQLite/Postgres)
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeouts
timeout = 120  # Request timeout (120 seconds)
graceful_timeout = 30  # Time to wait for worker graceful shutdown

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.getenv("LOG_LEVEL", "info").lower()
access_log_format = '[%(asctime)s] %(h)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" {%(D)s}'

# Server mechanics
daemon = False  # Don't daemonize (Railway expects foreground process)
pidfile = None  # No PID file for Railway ephemeral environment
umask = 0o022
user = None  # Run as current user
group = None

# Application behavior
preload_app = False  # Load app in worker, not master (safer with migrations)
keepalive = 5


def on_starting(server):
    """Called when Gunicorn is starting"""
    logger = logging.getLogger(__name__)
    logger.info(f"Gunicorn starting with {server.cfg.workers} workers")


def on_exit(_server):
    """Called when Gunicorn is exiting"""
    logger = logging.getLogger(__name__)
    logger.info("Gunicorn shutting down")


# Environment-specific tuning
if os.getenv("FLASK_ENV") == "production":
    # Production settings
    workers = max(4, multiprocessing.cpu_count())
    timeout = 300  # Longer timeout for heavy analysis
elif os.getenv("FLASK_ENV") == "development":
    # Development settings
    workers = 1
    reload = True  # Auto-reload on code changes
    timeout = 600
else:
    # Default (Railway)
    workers = max(2, multiprocessing.cpu_count())
    timeout = 120
