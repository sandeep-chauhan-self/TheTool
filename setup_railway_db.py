#!/usr/bin/env python3
"""
Railway PostgreSQL Configuration & Connection Test

This script helps you:
1. Configure the DATABASE_URL environment variable
2. Test the connection to Railway PostgreSQL
3. Initialize the database schema
4. Verify the connection works
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

def configure_railway_db():
    """Configure Railway PostgreSQL connection"""
    
    print("=" * 80)
    print("RAILWAY POSTGRESQL CONFIGURATION")
    print("=" * 80)
    print()
    
    # Railway environment variables
    pg_user = os.getenv('PGUSER', 'postgres')
    pg_password = os.getenv('POSTGRES_PASSWORD', '')
    pg_database = os.getenv('POSTGRES_DB', 'railway')
    
    # Two connection options:
    # 1. Private domain (internal Railway network) - faster, more reliable
    # 2. Public URL (external internet) - for local development
    
    pg_private_domain = os.getenv('RAILWAY_PRIVATE_DOMAIN', '')
    pg_public_domain = os.getenv('RAILWAY_TCP_PROXY_DOMAIN', '')
    pg_public_port = os.getenv('RAILWAY_TCP_PROXY_PORT', '5432')
    
    print("Detected Railway Environment:")
    print(f"  PostgreSQL User: {pg_user}")
    print(f"  PostgreSQL Database: {pg_database}")
    print(f"  Private Domain: {pg_private_domain if pg_private_domain else 'NOT SET'}")
    print(f"  Public Domain: {pg_public_domain if pg_public_domain else 'NOT SET'}")
    print(f"  Public Port: {pg_public_port}")
    print()
    
    # Build DATABASE_URL
    if pg_private_domain:
        database_url = f"postgresql://{pg_user}:{pg_password}@{pg_private_domain}:5432/{pg_database}"
        connection_type = "PRIVATE (Railway Internal Network)"
    elif pg_public_domain:
        database_url = f"postgresql://{pg_user}:{pg_password}@{pg_public_domain}:{pg_public_port}/{pg_database}"
        connection_type = "PUBLIC (External Internet)"
    else:
        print("ERROR: Neither RAILWAY_PRIVATE_DOMAIN nor RAILWAY_TCP_PROXY_DOMAIN found!")
        return None
    
    print(f"Connection Type: {connection_type}")
    print()
    print("Constructed DATABASE_URL:")
    print(f"  postgresql://{pg_user}:{'*' * len(pg_password)}@[domain]:5432/{pg_database}")
    print()
    
    return database_url

def test_connection(database_url):
    """Test the PostgreSQL connection"""
    print("=" * 80)
    print("TESTING CONNECTION")
    print("=" * 80)
    print()
    
    try:
        import psycopg2
        print("✓ psycopg2 module found")
    except ImportError:
        print("✗ psycopg2 not installed. Installing...")
        os.system("pip install psycopg2-binary")
        import psycopg2
        print("✓ psycopg2 installed")
    
    try:
        print(f"Attempting connection...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Get server version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ Connected successfully!")
        print(f"  PostgreSQL Version: {version.split(',')[0]}")
        
        # Test database
        cursor.execute("SELECT datname FROM pg_database WHERE datname = %s;", (database_url.split('/')[-1],))
        db_result = cursor.fetchone()
        if db_result:
            print(f"✓ Database '{database_url.split('/')[-1]}' exists")
        else:
            print(f"⚠ Database '{database_url.split('/')[-1]}' not found")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

def initialize_schema(database_url):
    """Initialize the database schema"""
    print()
    print("=" * 80)
    print("INITIALIZING DATABASE SCHEMA")
    print("=" * 80)
    print()
    
    # Set DATABASE_URL in environment
    os.environ['DATABASE_URL'] = database_url
    
    try:
        from config import config
        from database import init_db
        
        print(f"Database Type: {config.DATABASE_TYPE.upper()}")
        print(f"Initializing schema...")
        
        init_db()
        print("✓ Database schema initialized successfully!")
        return True
    except Exception as e:
        print(f"✗ Schema initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_env_file(database_url):
    """Update or create .env file with DATABASE_URL"""
    print()
    print("=" * 80)
    print("UPDATING .ENV FILE")
    print("=" * 80)
    print()
    
    env_file = Path(__file__).parent / '.env'
    
    try:
        # Read existing .env if it exists
        env_content = {}
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_content[key] = value
        
        # Update DATABASE_URL
        env_content['DATABASE_URL'] = database_url
        
        # Write back
        with open(env_file, 'w') as f:
            for key, value in env_content.items():
                # Don't write passwords in plain text - mark as placeholder
                if 'PASSWORD' in key.upper() and key != 'DATABASE_URL':
                    f.write(f"# {key}=[SET_IN_RAILWAY_ENVIRONMENT]\n")
                else:
                    f.write(f"{key}={value}\n")
        
        print(f"✓ Updated {env_file}")
        print()
        print("NOTE: For security, actual passwords are stored in Railway environment.")
        print("      Set these variables in Railway Dashboard:")
        print("      - PGUSER")
        print("      - POSTGRES_PASSWORD")
        print("      - POSTGRES_DB")
        print("      - RAILWAY_PRIVATE_DOMAIN (or RAILWAY_TCP_PROXY_DOMAIN)")
        return True
    except Exception as e:
        print(f"✗ Failed to update .env: {e}")
        return False

def main():
    """Main setup flow"""
    print("\n")
    
    # Step 1: Configure
    database_url = configure_railway_db()
    if not database_url:
        print("\n✗ Configuration failed. Exiting.")
        return 1
    
    # Step 2: Test connection
    if not test_connection(database_url):
        print("\n✗ Connection test failed. Check your Railway environment variables.")
        return 1
    
    # Step 3: Initialize schema
    if not initialize_schema(database_url):
        print("\n✗ Schema initialization failed.")
        return 1
    
    # Step 4: Update .env
    update_env_file(database_url)
    
    print()
    print("=" * 80)
    print("✅ SETUP COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Restart your Flask application")
    print("2. The app will now use Railway PostgreSQL")
    print("3. Check logs to verify connection")
    print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
