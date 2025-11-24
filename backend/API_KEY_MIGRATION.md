# API Key Management Migration Guide

## Overview

The authentication system has been migrated from in-memory API key storage to persistent database-backed storage. This enables:

- **Multi-instance deployments**: API keys work across multiple server instances
- **Secure key rotation**: Keys can be revoked without restarting
- **Audit trails**: Complete history of key creation, revocation, and usage
- **No secrets in logs**: Raw keys are never logged or exposed
- **Distributed support**: Keys are stored in PostgreSQL or SQLite

## Architecture

### New Files

1. **`api_key_manager.py`**: Core API key management module
   - Handles key generation, validation, revocation
   - Manages database schema and migrations
   - Provides audit logging without exposing secrets

2. **`migrations_api_keys.py`**: Database schema migration
   - Creates `api_keys` and `api_key_audit` tables
   - Adds proper indexes for performance
   - Works with both PostgreSQL and SQLite

3. **`auth.py`** (updated): Authentication decorator and utilities
   - Now delegates to `APIKeyManager`
   - Maintains backward-compatible API
   - No changes needed to existing endpoints

## Database Schema

### `api_keys` Table

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    key_hash TEXT UNIQUE NOT NULL,          -- SHA-256 hash of the API key
    name TEXT NOT NULL,                     -- Friendly name
    permissions TEXT NOT NULL,              -- Comma-separated permissions
    created_at TIMESTAMP,                   -- Creation timestamp
    revoked_at TIMESTAMP NULL,              -- Revocation timestamp (NULL = active)
    last_used_at TIMESTAMP NULL,            -- Last validation timestamp
    created_by TEXT                         -- Who created this key
);
```

### `api_key_audit` Table

```sql
CREATE TABLE api_key_audit (
    id INTEGER PRIMARY KEY,
    key_hash TEXT NOT NULL,                 -- Reference to api_keys
    action TEXT NOT NULL,                   -- 'created', 'revoked', 'validated', etc.
    details TEXT,                           -- Action details (no raw keys!)
    created_at TIMESTAMP                    -- Action timestamp
);
```

## Migration Steps

### 1. Update Environment Variables

Ensure `.env` has a secure master key:

```bash
# Generate a new key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
MASTER_API_KEY=your-generated-key-here
```

### 2. Run Database Migrations

The migrations run automatically during app startup, or run manually:

```bash
cd backend
python -c "from migrations_api_keys import migrate_create_api_key_tables; migrate_create_api_key_tables()"
```

### 3. Deploy Application

1. Deploy updated `auth.py` and new files (`api_key_manager.py`, `migrations_api_keys.py`)
2. On first run, `initialize_master_key()` is called during app initialization
3. Master key is validated/created in database
4. All subsequent API key operations use database storage

## API Reference

### Creating API Keys

```python
from api_key_manager import APIKeyManager

# Create a new API key
api_key, metadata = APIKeyManager.create_api_key(
    name='My Integration',
    permissions=['read', 'write'],
    created_by='admin'
)

# api_key is the raw key (save this immediately!)
# metadata contains name, permissions, created_at, key_hash
```

### Validating API Keys

```python
# In your endpoint (handled by @require_auth decorator)
metadata = validate_api_key(request_api_key)
if metadata:
    # Key is valid and active
    permissions = metadata['permissions']
```

### Revoking API Keys

```python
# Revoke a key
revoke_api_key(api_key)
```

### Listing Active Keys

```python
# Get all active keys (metadata only, no raw keys)
keys = APIKeyManager.get_all_active_keys(include_usage=True)

for key in keys:
    print(f"{key['name']} - {key['created_at']}")
```

## Security Considerations

### What Changed

- **Before**: Keys stored in-memory dict, generated on startup, logged to console
- **After**: Keys hashed and persisted to database, never logged

### Key Points

1. **Key Hashing**: Raw keys are hashed with SHA-256 before storage
2. **Audit Logging**: All operations logged with action, timestamp, but NO raw keys
3. **Revocation**: Soft-delete via `revoked_at` timestamp (key remains in DB for audit)
4. **Last Used**: Tracked for usage analysis and cleanup policies
5. **No Console Output**: Raw keys never printed - provide `.env` directly

### Access Control

Use proper file permissions on `.env`:

```bash
chmod 600 .env           # Read/write for owner only
chmod 600 backend/.env   # Same in backend directory
```

## Backward Compatibility

### Existing Code

All existing code continues to work:

```python
# These functions still work - they delegate to APIKeyManager
@require_auth
def my_endpoint():
    pass

# validate_api_key() still returns metadata
metadata = validate_api_key(key)

# create_api_key() and revoke_api_key() have same signatures
key = create_api_key(name, permissions)
revoke_api_key(key)
```

### No Endpoint Changes

All existing endpoints with `@require_auth` work without modification.

## Troubleshooting

### "MASTER_API_KEY not found in environment"

**Issue**: App fails to start

**Solution**:
1. Generate a key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Add to `.env`: `MASTER_API_KEY=<generated-key>`
3. Restart app

### "Failed to initialize API key storage"

**Issue**: Database connection error during startup

**Solution**:
1. Verify database is running
2. Check `DATABASE_URL` or `DB_PATH` in config
3. Ensure write permissions to database file/directory
4. Check logs for specific SQL error

### Keys Lost After Restart (Before Migration)

**Issue**: Previously generated in-memory keys are gone

**Solution**: This is expected. Use persistent keys from database going forward. Previous clients need new keys from `MASTER_API_KEY`.

## Performance

### Database Queries

- **Validate key**: Single index lookup on `key_hash` (< 1ms)
- **Create key**: Single INSERT (< 5ms)
- **Revoke key**: Single UPDATE (< 5ms)
- **List keys**: Full table scan, indexed by revocation status

### Caching Options

For high-traffic scenarios, consider caching:

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1000)
def cached_validate_api_key(api_key: str):
    # Validate against database
    # Cache for 60 seconds per key
    pass
```

Or use Redis for distributed caching (future enhancement).

## Monitoring

### Audit Log Queries

```sql
-- View all actions for a key
SELECT * FROM api_key_audit 
WHERE key_hash = '<hash>' 
ORDER BY created_at DESC;

-- Find recent key creations
SELECT * FROM api_key_audit 
WHERE action = 'created' 
AND created_at > datetime('now', '-7 days');

-- Count usage by action
SELECT action, COUNT(*) FROM api_key_audit 
GROUP BY action;
```

## Future Enhancements

1. **Rate limiting per key**: Store limits in database
2. **Key scopes**: Fine-grained permissions (read_stocks, write_analysis, etc.)
3. **Token expiration**: Add `expires_at` column
4. **OAuth2 integration**: Replace bearer tokens with OAuth
5. **Redis backend**: For ultra-high performance deployments
6. **Key rotation**: Automatic key lifecycle management

## Questions?

Refer to:
- `api_key_manager.py`: Full implementation with docstrings
- `auth.py`: Usage in authentication decorator
- `migrations_api_keys.py`: Schema creation
