"""
Bulk Analysis Authentication - Password verification for multi-stock analysis
"""
import bcrypt
from flask import Blueprint, request, jsonify
from config import config
from utils.logger import setup_logger

logger = setup_logger()
bp = Blueprint("bulk_auth", __name__, url_prefix="/api/auth")


@bp.route("/verify-bulk-password", methods=["POST"])
def verify_bulk_password():
    """
    Verify password for bulk/multi-stock analysis access.
    
    Request body:
    {
        "password": "user-entered-password"
    }
    
    Returns:
        200 + {"authorized": true} on success
        403 + {"authorized": false, "message": "..."} on wrong password
        503 if no password hash is configured
    """
    try:
        # Check if password hash is configured
        password_hash = config.BULK_ANALYSIS_PASSWORD_HASH
        if not password_hash:
            logger.warning("[BULK_AUTH] No BULK_ANALYSIS_PASSWORD_HASH configured")
            return jsonify({
                "authorized": False,
                "message": "Bulk analysis password not configured on server"
            }), 503

        # Get password from request
        data = request.get_json() or {}
        password = data.get("password", "")

        if not password:
            return jsonify({
                "authorized": False,
                "message": "Password is required"
            }), 400

        # Verify password against stored bcrypt hash
        is_valid = bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )

        if is_valid:
            logger.info("[BULK_AUTH] Password verified successfully")
            return jsonify({"authorized": True}), 200
        else:
            logger.warning("[BULK_AUTH] Invalid password attempt")
            return jsonify({
                "authorized": False,
                "message": "Incorrect password"
            }), 403

    except Exception as e:
        logger.exception("[BULK_AUTH] Password verification error")
        return jsonify({
            "authorized": False,
            "message": "Server error during verification"
        }), 500
