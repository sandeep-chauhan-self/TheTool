"""
Setup local PostgreSQL database for TheTool
Run this once after installing PostgreSQL
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Local PostgreSQL credentials
HOST = 'localhost'
PORT = 5432
USER = 'postgres'
PASSWORD = 'SANDstorm@10'
DATABASE = 'trading_app'

def create_database():
    """Create the trading_app database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE {DATABASE}')
            print(f'✓ Database "{DATABASE}" created successfully!')
        else:
            print(f'✓ Database "{DATABASE}" already exists!')
        
        cursor.close()
        conn.close()
        
        # Now connect to the new database and verify
        conn = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f'✓ Connected to: {version[:50]}...')
        cursor.close()
        conn.close()
        
        print(f'\n✓ PostgreSQL setup complete!')
        print(f'  Connection string: postgresql://{USER}:****@{HOST}:{PORT}/{DATABASE}')
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        return False

if __name__ == '__main__':
    create_database()
