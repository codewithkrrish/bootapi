"""Auth endpoints: register, log in, and "who am I".

Passwords are hashed with pbkdf2 (see app/security.py) and never stored or
returned in plaintext. Tokens are short-lived JWTs — 30 minutes by default.
There is deliberately no refresh-token flow here; add one when your clients
actually need long sessions, not before.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..config import Settings, get_settings
from ..deps import get_current_user, get_store
from ..models import Token, UserCreate, UserPublic
from ..security import create_access_token, hash_password, verify_password
from ..store import DuplicateEmailError, Store, UserRecord

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
def register(data: UserCreate, store: Store = Depends(get_store)) -> UserPublic:
    """Create a user. A taken email is a 409, not a 500."""
    try:
        user = store.create_user(data.email, hash_password(data.password))
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return UserPublic(id=user.id, email=user.email)


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
    store: Store = Depends(get_store),
) -> Token:
    """Trade an email + password for a bearer token.

    Wrong email and wrong password get the same 401 — don't tell an
    attacker which half of the pair was right.
    """
    user = store.get_user_by_email(form.username)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        subject=str(user.id),
        secret=settings.secret_key,
        algorithm=settings.algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
def me(user: UserRecord = Depends(get_current_user)) -> UserPublic:
    """Return the user behind the bearer token."""
    return UserPublic(id=user.id, email=user.email)
