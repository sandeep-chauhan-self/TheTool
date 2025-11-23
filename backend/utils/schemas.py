"""
Centralized response schema definitions for API validation.

Used to validate and document API response formats before returning to client.
"""

from typing import Dict, Any, List, Optional


class ResponseSchemas:
    """Standard response schema definitions"""
    
    # Job Status Response
    JOB_STATUS = {
        "type": "object",
        "required": ["job_id", "status", "progress", "completed", "total"],
        "properties": {
            "job_id": {"type": "string"},
            "status": {"type": "string", "enum": ["queued", "processing", "completed", "failed", "cancelled"]},
            "progress": {"type": "integer", "minimum": 0, "maximum": 100},
            "completed": {"type": "integer", "minimum": 0},
            "total": {"type": "integer", "minimum": 0},
            "successful": {"type": "integer", "minimum": 0},
            "current_index": {"type": "integer"},
            "current_ticker": {"type": ["string", "null"]},
            "message": {"type": "string"},
            "errors": {"type": ["string", "array"]},
            "created_at": {"type": "string"},
            "updated_at": {"type": "string"},
            "started_at": {"type": ["string", "null"]},
            "completed_at": {"type": ["string", "null"]}
        }
    }
    
    # Analysis History Response
    ANALYSIS_HISTORY = {
        "type": "object",
        "required": ["ticker", "history"],
        "properties": {
            "ticker": {"type": "string"},
            "history": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "ticker": {"type": "string"},
                        "symbol": {"type": "string"},
                        "analysis_data": {"type": ["string", "object"]},
                        "created_at": {"type": "string"},
                        "job_id": {"type": ["string", "null"]}
                    }
                }
            }
        }
    }
    
    # Stock History Response
    STOCK_HISTORY = {
        "type": "object",
        "required": ["symbol", "history", "count"],
        "properties": {
            "symbol": {"type": "string"},
            "history": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "ticker": {"type": "string"},
                        "symbol": {"type": "string"},
                        "analysis_data": {"type": ["string", "object"]},
                        "created_at": {"type": "string"},
                        "job_id": {"type": ["string", "null"]}
                    }
                }
            },
            "count": {"type": "integer", "minimum": 0}
        }
    }
    
    # Watchlist Response
    WATCHLIST = {
        "type": "object",
        "required": ["watchlist"],
        "properties": {
            "watchlist": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "ticker", "symbol"],
                    "properties": {
                        "id": {"type": "integer"},
                        "ticker": {"type": "string"},
                        "symbol": {"type": "string"},
                        "notes": {"type": ["string", "null"]},
                        "created_at": {"type": "string"}
                    }
                }
            },
            "count": {"type": "integer", "minimum": 0}
        }
    }
    
    # Analysis Job Created Response
    JOB_CREATED = {
        "type": "object",
        "required": ["job_id", "status"],
        "properties": {
            "job_id": {"type": "string"},
            "status": {"type": "string"},
            "tickers": {"type": "array", "items": {"type": "string"}},
            "symbols": {"type": "array", "items": {"type": "string"}},
            "capital": {"type": "number"},
            "count": {"type": "integer"},
            "message": {"type": "string"}
        }
    }
    
    # Error Response
    ERROR_RESPONSE = {
        "type": "object",
        "required": ["error"],
        "properties": {
            "error": {
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {"type": ["object", "null"]},
                    "timestamp": {"type": "string"}
                }
            }
        }
    }
    
    # NSE Stocks List Response
    NSE_STOCKS_LIST = {
        "type": "object",
        "required": ["stocks"],
        "properties": {
            "stocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "symbol": {"type": "string"},
                        "name": {"type": "string"},
                        "yahoo_symbol": {"type": "string"}
                    }
                }
            },
            "count": {"type": "integer", "minimum": 0}
        }
    }
    
    # All Stocks Response (paginated)
    ALL_STOCKS = {
        "type": "object",
        "required": ["stocks"],
        "properties": {
            "stocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "ticker": {"type": "string"},
                        "symbol": {"type": "string"},
                        "name": {"type": "string"}
                    }
                }
            },
            "count": {"type": "integer", "minimum": 0},
            "page": {"type": "integer"},
            "per_page": {"type": "integer"},
            "total": {"type": "integer"}
        }
    }
    
    # Health Check Response
    HEALTH_CHECK = {
        "type": "object",
        "required": ["status"],
        "properties": {
            "status": {"type": "string", "enum": ["healthy", "degraded", "unhealthy"]},
            "timestamp": {"type": "string"},
            "database": {"type": "string"},
            "version": {"type": "string"},
            "uptime_seconds": {"type": "number"}
        }
    }
    
    # Configuration Response
    CONFIG = {
        "type": "object",
        "required": ["flask_env"],
        "properties": {
            "flask_env": {"type": "string"},
            "debug": {"type": "boolean"},
            "database_type": {"type": "string"},
            "version": {"type": "string"},
            "features": {"type": "object"}
        }
    }


class SchemaValidator:
    """Simple schema validator using basic type checking"""
    
    @staticmethod
    def validate(data: Any, schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate data against schema.
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "Response must be a dictionary"
        
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Check types for known properties
        properties = schema.get("properties", {})
        for field, prop_schema in properties.items():
            if field not in data:
                continue
            
            value = data[field]
            prop_type = prop_schema.get("type")
            
            if prop_type == "array" and not isinstance(value, list):
                return False, f"Field '{field}' must be an array, got {type(value).__name__}"
            elif prop_type == "object" and not isinstance(value, dict):
                return False, f"Field '{field}' must be an object, got {type(value).__name__}"
            elif prop_type == "string" and not isinstance(value, str):
                return False, f"Field '{field}' must be a string, got {type(value).__name__}"
            elif prop_type == "integer" and not isinstance(value, int):
                return False, f"Field '{field}' must be an integer, got {type(value).__name__}"
            elif prop_type == "boolean" and not isinstance(value, bool):
                return False, f"Field '{field}' must be a boolean, got {type(value).__name__}"
            elif prop_type == "number" and not isinstance(value, (int, float)):
                return False, f"Field '{field}' must be a number, got {type(value).__name__}"
        
        return True, None


def validate_response(response: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate API response against schema.
    
    Args:
        response: Response data dictionary
        schema: Schema to validate against
    
    Returns:
        (is_valid, error_message)
    """
    return SchemaValidator.validate(response, schema)
