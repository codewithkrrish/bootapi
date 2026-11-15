"""Shared dependencies: settings, the store, and the current user.

Routers take these as function arguments and FastAPI wires them up.
Nothing here imports a router, so there's no import cycle to trip over.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .config import Settings, get_settings
from .security import TokenError, decode_access_token
from .store import Store, UserRecord

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_store(settings: Settings = Depends(get_settings)) -> Store:
    """Build the store from settings (cheap — connections are per-call)."""
    return Store(settings.database_path)


def get_current_user(
    token: str = Depends(_oauth2_scheme),
    settings: Settings = Depends(get_settings),
    store: Store = Depends(get_store),
) -> UserRecord:
    """Decode the bearer token and load the user it belongs to.

    Any failure here is a 401 with the same message — login and token
    problems shouldn't leak different hints to whoever is probing.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        subject = decode_access_token(token, settings.secret_key, settings.algorithm)
        user_id = int(subject)
    except (TokenError, ValueError):
        raise credentials_error from None
    user = store.get_user_by_id(user_id)
    if user is None:
        raise credentials_error
    return user
