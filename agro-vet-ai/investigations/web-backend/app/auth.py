"""
Authentication module for the VetRetro Web Backend API
"""
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import get_settings



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
    settings = get_settings()
    expected_api_key = getattr(settings, 'API_KEY', None)

    if not expected_api_key:
        # If no API key is configured, allow all requests in development mode
        return provided_api_key

    if not provided_api_key or provided_api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return provided_api_key