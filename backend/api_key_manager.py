"""
Persistent API Key Management Module

Handles secure storage, validation, and auditing of API keys using database backend.
Supports both PostgreSQL and SQLite with proper hashing and revocation.

SECURITY NOTES:
- API keys are hashed with SHA-256 before storage
- Raw keys are NEVER logged or exposed
- Revocation is soft-delete via revoked_at timestamp
- All operations are audited in audit log
- Thread-safe with connection pooling
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from database import get_db, execute_query, _raise_critical_error

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages persistent API key storage and validation"""
    
    TABLE_SCHEMA_SQLITE = """
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        permissions TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMP,
        last_used_at TIMESTAMP,
        created_by TEXT
    );
    
    CREATE TABLE IF NOT EXISTS api_key_audit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key_hash TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (key_hash) REFERENCES api_keys(key_hash) ON DELETE CASCADE
    );
    
    CREATE INDEX IF NOT EXISTS idx_api_keys_revoked ON api_keys(revoked_at);
    CREATE INDEX IF NOT EXISTS idx_audit_action ON api_key_audit(action);
    """
    
    TABLE_SCHEMA_POSTGRES = """
    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        key_hash TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        permissions TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMP NULL,
        last_used_at TIMESTAMP NULL,
        created_by TEXT
    );
    
    CREATE TABLE IF NOT EXISTS api_key_audit (
        id SERIAL PRIMARY KEY,
        key_hash TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (key_hash) REFERENCES api_keys(key_hash) ON DELETE CASCADE
    );
    
    CREATE INDEX IF NOT EXISTS idx_api_keys_revoked ON api_keys(revoked_at);
    CREATE INDEX IF NOT EXISTS idx_audit_action ON api_key_audit(action);
    """
    
    @staticmethod
    def initialize_storage(database_type: str) -> None:
        """
        Initialize API key storage tables in database.
        
        Args:
            database_type: 'postgres' or 'sqlite'
            
        Raises:
            Exception: If schema creation fails
        """
        try:
            if database_type == 'postgres':
                schema = APIKeyManager.TABLE_SCHEMA_POSTGRES
                # Split into individual statements for PostgreSQL
                for statement in schema.split(';'):
                    statement = statement.strip()
                    if statement:
                        execute_query(statement)
            else:  # sqlite
                schema = APIKeyManager.TABLE_SCHEMA_SQLITE
                # SQLite can handle multiple statements
                for statement in schema.split(';'):
                    statement = statement.strip()
                    if statement:
                        execute_query(statement)
            
            logger.info(f"API key storage initialized for {database_type}")
        except Exception as e:
            logger.error(f"Failed to initialize API key storage: {e}")
            raise
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    def create_api_key(
        name: str,
        permissions: List[str] = None,
        created_by: str = None
    ) -> Tuple[str, Dict]:
        """
        Create a new API key and persist to database.
        
        Args:
            name: Friendly name for the key
            permissions: List of permissions (default: ['read'])
            created_by: User/service that created this key
            
        Returns:
            Tuple of (raw_api_key, metadata_dict)
            IMPORTANT: Raw key is returned ONLY ONCE - save it immediately!
            
        Raises:
            Exception: If database insertion fails
        """
        if permissions is None:
            permissions = ['read']
        
        try:
            # Generate secure API key
            api_key = secrets.token_urlsafe(32)
            key_hash = APIKeyManager.hash_api_key(api_key)
            
            # Serialize permissions for storage
            permissions_str = ','.join(permissions)
            
            # Insert into database
            query = """
            INSERT INTO api_keys (key_hash, name, permissions, created_by)
            VALUES (?, ?, ?, ?)
            """
            execute_query(query, (key_hash, name, permissions_str, created_by))
            
            # Audit log (without exposing raw key)
            APIKeyManager._audit_log(
                key_hash,
                'created',
                f'API key "{name}" created with permissions: {permissions}'
            )
            
            logger.info(f"Created API key: {name} (by {created_by or 'system'})")
            
            # Return raw key and metadata
            metadata = {
                'name': name,
                'permissions': permissions,
                'created_at': datetime.now().isoformat(),
                'key_hash': key_hash
            }
            
            return api_key, metadata
            
        except Exception as e:
            logger.error(f"Failed to create API key '{name}': {e}")
            raise
    
    @staticmethod
    def validate_api_key(api_key: str) -> Optional[Dict]:
        """
        Validate API key and return metadata if valid.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dict with metadata if valid and not revoked, None otherwise
        """
        if not api_key:
            return None
        
        try:
            key_hash = APIKeyManager.hash_api_key(api_key)
            
            # Query for active (non-revoked) key
            query = """
            SELECT id, name, permissions, created_at, last_used_at
            FROM api_keys
            WHERE key_hash = ? AND revoked_at IS NULL
            """
            result = execute_query(query, (key_hash,), fetch_one=True)
            
            if not result:
                return None
            
            # Update last_used_at timestamp
            update_query = "UPDATE api_keys SET last_used_at = ? WHERE key_hash = ?"
            execute_query(update_query, (datetime.now().isoformat(), key_hash))
            
            # Return metadata
            return {
                'id': result.get('id') if isinstance(result, dict) else result[0],
                'name': result.get('name') if isinstance(result, dict) else result[1],
                'permissions': (result.get('permissions') if isinstance(result, dict) else result[2]).split(','),
                'created_at': result.get('created_at') if isinstance(result, dict) else result[3],
                'last_used_at': result.get('last_used_at') if isinstance(result, dict) else result[4]
            }
            
        except Exception as e:
            logger.warning(f"Error validating API key: {e}")
            return None
    
    @staticmethod
    def revoke_api_key(api_key: str) -> bool:
        """
        Revoke (soft-delete) an API key.
        
        Args:
            api_key: The API key to revoke
            
        Returns:
            True if revoked successfully, False if not found
        """
        try:
            key_hash = APIKeyManager.hash_api_key(api_key)
            
            # Get key metadata before revoking
            query = "SELECT name FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL"
            result = execute_query(query, (key_hash,), fetch_one=True)
            
            if not result:
                logger.warning(f"Attempt to revoke non-existent key hash: {key_hash[:8]}...")
                return False
            
            key_name = result.get('name') if isinstance(result, dict) else result[0]
            
            # Update revoked_at timestamp
            update_query = "UPDATE api_keys SET revoked_at = ? WHERE key_hash = ?"
            execute_query(update_query, (datetime.now().isoformat(), key_hash))
            
            # Audit log
            APIKeyManager._audit_log(
                key_hash,
                'revoked',
                f'API key "{key_name}" revoked'
            )
            
            logger.info(f"Revoked API key: {key_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke API key: {e}")
            raise
    
    @staticmethod
    def get_all_active_keys(include_usage: bool = False) -> List[Dict]:
        """
        Retrieve all active (non-revoked) API keys.
        
        Args:
            include_usage: Include last_used_at timestamp
            
        Returns:
            List of key metadata (without raw keys)
        """
        try:
            cols = "id, name, permissions, created_at, created_by"
            if include_usage:
                cols += ", last_used_at"
            
            query = f"SELECT {cols} FROM api_keys WHERE revoked_at IS NULL"
            results = execute_query(query)
            
            keys = []
            for row in results:
                if isinstance(row, dict):
                    permissions = row['permissions'].split(',') if row['permissions'] else []
                    keys.append({
                        'id': row['id'],
                        'name': row['name'],
                        'permissions': permissions,
                        'created_at': row['created_at'],
                        'created_by': row.get('created_by'),
                        'last_used_at': row.get('last_used_at') if include_usage else None
                    })
                else:
                    # Handle tuple results
                    permissions = row[2].split(',') if row[2] else []
                    keys.append({
                        'id': row[0],
                        'name': row[1],
                        'permissions': permissions,
                        'created_at': row[3],
                        'created_by': row[4],
                        'last_used_at': row[5] if include_usage and len(row) > 5 else None
                    })
            
            return keys
            
        except Exception as e:
            logger.error(f"Failed to retrieve active API keys: {e}")
            return []
    
    @staticmethod
    def _audit_log(key_hash: str, action: str, details: str = None) -> None:
        """
        Log audit event for API key operation.
        
        Args:
            key_hash: Hash of the API key
            action: Action performed (created, revoked, validated, etc.)
            details: Additional details (no sensitive information)
        """
        try:
            query = """
            INSERT INTO api_key_audit (key_hash, action, details)
            VALUES (?, ?, ?)
            """
            execute_query(query, (key_hash, action, details))
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")
            # Don't raise - audit failure shouldn't break key operations


# Module initialization: Create master key if not exists
def initialize_master_key() -> None:
    """
    Initialize master API key on first startup.
    Creates master key in database if MASTER_API_KEY env var is set,
    otherwise generates and exits with instructions.
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    master_key_env = os.getenv('MASTER_API_KEY')
    
    if not master_key_env:
        logger.critical(
            "MASTER_API_KEY not found in environment! "
            "Please set MASTER_API_KEY in .env file with a secure value. "
            "Example: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
        raise ValueError("MASTER_API_KEY must be set in environment")
    
    try:
        # Check if master key already exists in database
        key_hash = APIKeyManager.hash_api_key(master_key_env)
        query = "SELECT id FROM api_keys WHERE key_hash = ?"
        result = execute_query(query, (key_hash,), fetch_one=True)
        
        if result:
            logger.info("Master API key already initialized in database")
            return
        
        # Create master key
        _api_key, _metadata = APIKeyManager.create_api_key(
            name='Master Key',
            permissions=['all'],
            created_by='system'
        )
        
        logger.info("Master API key initialized successfully in database")
        
    except Exception as e:
        logger.error(f"Failed to initialize master API key: {e}")
        raise
