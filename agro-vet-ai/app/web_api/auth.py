"""
Authentication module for the Agro-Vet AI API
"""
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.utils.logger import get_logger
from app.utils.settings import secrets as s

logger = get_logger(__name__)


# Initialize security scheme
security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """
    Verifies the API key provided in the Authorization header.
    
    Args:
        credentials: HTTP authorization credentials from the header
        
    Returns:
        Optional[str]: The API key if valid, raises HTTPException if invalid
        
    Raises:
        HTTPException: If the API key is invalid or not provided
    """
    provided_api_key = credentials.credentials
    
    # Get the expected API key from settings
    expected_api_key = s.api_key
    
    if not expected_api_key:
        logger.warning("No API key is configured in settings")
        # If no API key is configured, allow all requests in development mode
        return provided_api_key
    
    if not provided_api_key or provided_api_key != expected_api_key:
        logger.warning(f"Invalid API key provided: {provided_api_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    logger.info("Valid API key provided")
    return provided_api_key