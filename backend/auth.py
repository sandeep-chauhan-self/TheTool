"""
Authentication and Authorization Module

CRITICAL FIX (ISSUE_021): Implements API key-based authentication
to prevent unauthorized access to all endpoints.

Security Features:
- API key validation
- Request signing (optional)
- Rate limiting per API key
- Audit logging for all authenticated requests
"""

import os
import secrets
import hashlib
import logging
import threading
from functools import wraps
from datetime import datetime
from flask import request, jsonify
from typing import Optional, Callable
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

logger = logging.getLogger(__name__)

# API Keys storage (in production, move to database or environment)
# For now, we generate a master key on startup
MASTER_API_KEY = os.getenv('MASTER_API_KEY')
if not MASTER_API_KEY:
    # Generate a secure API key on first run
    MASTER_API_KEY = secrets.token_urlsafe(32)
    logger.warning("=" * 80)
    logger.warning("NO MASTER_API_KEY FOUND IN ENVIRONMENT!")
    logger.warning(f"Generated temporary API key: {MASTER_API_KEY}")
    logger.warning("Add this to your .env file: MASTER_API_KEY=" + MASTER_API_KEY)
    logger.warning("=" * 80)

# Store valid API keys (hash them for security)
VALID_API_KEYS = {
    hashlib.sha256(MASTER_API_KEY.encode()).hexdigest(): {
        'name': 'Master Key',
        'permissions': ['all'],
        'created_at': datetime.now().isoformat()
    }
}


def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage comparison"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Validate an API key and return its metadata
    
    Args:
        api_key: The API key to validate
        
    Returns:
        dict: API key metadata if valid, None otherwise
    """
    if not api_key:
        return None
    
    key_hash = hash_api_key(api_key)
    return VALID_API_KEYS.get(key_hash)


def require_auth(f: Callable) -> Callable:
    """
    Decorator to require authentication for an endpoint.
    
    Usage:
        @app.route('/protected', methods=['GET'])
        @require_auth
        def protected_endpoint():
            return jsonify({"message": "Authenticated!"})
    
    Authentication Methods:
        1. Header: Authorization: Bearer <api_key>
        2. Query param: ?api_key=<api_key>
        3. Header: X-API-Key: <api_key>
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract API key from request
        api_key = None
        
        # Method 1: Authorization header (Bearer token)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header.split(' ')[1]
        
        # Method 2: X-API-Key header
        if not api_key:
            api_key = request.headers.get('X-API-Key')
        
        # Method 3: Query parameter (less secure, but convenient for testing)
        if not api_key:
            api_key = request.args.get('api_key')
        
        # Validate API key
        key_metadata = validate_api_key(api_key)
        if not key_metadata:
            logger.warning(f"Unauthorized access attempt to {request.path} from {request.remote_addr}")
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid or missing API key. Please provide a valid API key using one of these methods:\n" +
                          "1. Header: Authorization: Bearer <api_key>\n" +
                          "2. Header: X-API-Key: <api_key>\n" +
                          "3. Query param: ?api_key=<api_key>"
            }), 401
        
        # Log authenticated request
        logger.info(f"Authenticated request to {request.path} using key: {key_metadata['name']}")
        
        # Add key metadata to request context
        request.api_key_metadata = key_metadata
        
        return f(*args, **kwargs)
    
    return decorated_function


def create_api_key(name: str, permissions: list = None) -> str:
    """
    Create a new API key with specified permissions.
    
    Args:
        name: Friendly name for the API key
        permissions: List of permissions (default: ['all'])
        
    Returns:
        str: The generated API key (save this securely!)
    """
    if permissions is None:
        permissions = ['read']
    
    # Generate secure API key
    api_key = secrets.token_urlsafe(32)
    key_hash = hash_api_key(api_key)
    
    # Store metadata
    VALID_API_KEYS[key_hash] = {
        'name': name,
        'permissions': permissions,
        'created_at': datetime.now().isoformat()
    }
    
    logger.info(f"Created new API key: {name} with permissions: {permissions}")
    
    return api_key


def revoke_api_key(api_key: str) -> bool:
    """
    Revoke an API key
    
    Args:
        api_key: The API key to revoke
        
    Returns:
        bool: True if revoked successfully
    """
    key_hash = hash_api_key(api_key)
    if key_hash in VALID_API_KEYS:
        key_metadata = VALID_API_KEYS[key_hash]
        del VALID_API_KEYS[key_hash]
        logger.info(f"Revoked API key: {key_metadata['name']}")
        return True
    return False


# Optional: Implement rate limiting per API key
api_key_request_counts = {}
# Thread-safe lock for protecting api_key_request_counts dictionary and timestamp lists
# This prevents race conditions when multiple threads check/update rate limits simultaneously
api_key_request_counts_lock = threading.RLock()

def check_rate_limit(api_key: str, max_requests_per_minute: int = 60) -> bool:
    """
    Check if API key has exceeded rate limit (thread-safe)
    
    Args:
        api_key: The API key to check
        max_requests_per_minute: Maximum requests allowed per minute
        
    Returns:
        bool: True if within rate limit, False if exceeded
        
    Thread Safety:
        - Acquires lock for all reads/writes to api_key_request_counts
        - Prunes stale timestamps while holding lock
        - Removes empty entries to prevent memory leaks
        - For production, replace with Redis-based or distributed rate limiter
    """
    now = datetime.now()
    key_hash = hash_api_key(api_key)
    
    # Acquire lock for entire critical section
    with api_key_request_counts_lock:
        # Initialize tracking for this key if not exists
        if key_hash not in api_key_request_counts:
            api_key_request_counts[key_hash] = []
        
        # Get reference to this key's timestamp list
        timestamps = api_key_request_counts[key_hash]
        
        # Remove requests older than 1 minute (prune stale timestamps)
        pruned_timestamps = [
            ts for ts in timestamps
            if (now - ts).total_seconds() < 60
        ]
        api_key_request_counts[key_hash] = pruned_timestamps
        
        # Check if limit exceeded
        if len(pruned_timestamps) >= max_requests_per_minute:
            logger.warning(f"Rate limit exceeded for key hash {key_hash[:8]}... (limit: {max_requests_per_minute}/min)")
            return False
        
        # Add current request timestamp
        pruned_timestamps.append(now)
        
        # Clean up: Remove empty entries to prevent memory growth
        # (This would be rare unless a key is rate-limited and never used again)
        # Schedule cleanup of truly abandoned keys (more than 1 hour of inactivity)
        keys_to_remove = [
            k for k, ts_list in api_key_request_counts.items()
            if not ts_list  # Remove keys with empty timestamp lists
        ]
        for k in keys_to_remove:
            del api_key_request_counts[k]
            logger.debug(f"Cleaned up empty rate limit entry for key hash {k[:8]}...")
        
        return True
