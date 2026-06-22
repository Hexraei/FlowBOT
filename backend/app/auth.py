import logging
import secrets
from fastapi import Header, HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

def verify_admin_key(x_admin_key: str = Header(..., description="Admin API key for protected operations")):
    """
    FastAPI dependency that validates the X-Admin-Key header on all admin/agent routes.
    Raises HTTP 401 if the key is missing or does not match settings.ADMIN_API_KEY.
    Raises HTTP 500 on startup if ADMIN_API_KEY is not configured in .env.
    """
    if not settings.ADMIN_API_KEY:
        logger.error(
            "SECURITY: ADMIN_API_KEY is not set in .env. "
            "All admin endpoints are effectively unprotected. Set it immediately."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security misconfiguration: admin key not configured."
        )

    # Use secrets.compare_digest for timing-safe comparison (prevents timing attacks)
    if not secrets.compare_digest(x_admin_key, settings.ADMIN_API_KEY):
        logger.warning("Unauthorized admin access attempt with invalid API key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
