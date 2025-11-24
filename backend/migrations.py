# backend/migrations.py
"""
Database migration runner.

This module can be executed in two ways:
1. From backend directory: python migrations.py
2. As a module: python -m backend.migrations (when backend is a package)

The import uses try/except to support both absolute and relative imports.
"""

import sys
from pathlib import Path

# Add backend directory to path if needed (for direct execution)
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    # Try absolute import first (when run as module or backend is on PYTHONPATH)
    from database import init_db_if_needed
except ImportError:
    # Fallback: relative import (when run from backend directory directly)
    try:
        from .database import init_db_if_needed
    except ImportError:
        # Last resort: try adding parent to path
        parent_dir = backend_dir.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        from backend.database import init_db_if_needed
if __name__ == "__main__":
    print("Initializing DB and schema...")
    init_db_if_needed()
    print("Done.")
