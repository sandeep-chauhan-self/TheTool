#!/usr/bin/env python
"""
Migration runner for Railway
Run on Railway with: railway run python run_migration_direct.py
"""

import os
import sys
import subprocess

# Change to backend directory where migration files are
os.chdir('backend')

# Run the migration wrapper
result = subprocess.run([sys.executable, 'migrations_add_constraints.py'], 
                       capture_output=False)

sys.exit(result.returncode)
