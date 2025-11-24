"""Direct cleanup script for production - deletes orphaned watchlist entries"""
import os
import sys

# Using Railway's own database tools
print("Connecting to Railway database...")
os.system('railway run python -c "import psycopg2; conn = psycopg2.connect(os.environ.get(\'DATABASE_URL\')); cur = conn.cursor(); cur.execute(\'DELETE FROM watchlist WHERE symbol LIKE \\\'%RELIANCE%\\\'; ); conn.commit(); print(\'Deleted RELIANCE entries\'); cur.close(); conn.close()"')
