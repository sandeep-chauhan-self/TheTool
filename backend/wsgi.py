"""
WSGI entrypoint for gunicorn (Railway-compatible)

This module provides the production-ready application instance
for deployment on Railway and other WSGI-compatible platforms.

Usage:
  gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
  
Or on Railway (automatic):
  Set PORT env variable; Railway will run gunicorn with this module.
"""

import os
import sys
from pathlib import Path

# Ensure backend module is importable
backend_path = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_path))

# Import and initialize the Flask app
from app import app

if __name__ == "__main__":
    # Fallback for local testing (not used by gunicorn)
    port = int(os.getenv("PORT", 8000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.getenv("FLASK_ENV") == "development"
    )
