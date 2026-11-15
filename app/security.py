"""Password hashing and JWT helpers.

Deliberately light on dependencies: hashing is stdlib pbkdf2 and tokens are
PyJWT. A starter template shouldn't drag in a whole auth framework before
you've written your first endpoint — this is the smallest honest version of
"users can log in", and it's easy to swap out later.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

HASH_ALGORITHM = "sha256"
HASH_ITERATIONS = 200_000
SALT_BYTES = 16


class TokenError(ValueError):
    """Raised when a token is missing, expired, or just wrong."""


def hash_password(password: str) -> str:
    """Hash a password with pbkdf2 + a random salt.

    Stored format: ``pbkdf2$<iterations>$<salt hex>$<hash hex>``.
    """
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        HASH_ALGORITHM, password.encode("utf-8"), salt, HASH_ITERATIONS
    )
    return f"pbkdf2${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a plaintext password against a stored hash.

    Returns False for malformed stored values instead of raising — a corrupt
    row shouldn't take the login endpoint down with it.
    """
    try:
        _scheme, iterations, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest.hex(), hash_hex)


def create_access_token(
    subject: str,
    secret: str,
    algorithm: str,
    expires_minutes: int,
) -> str:
    """Mint a signed JWT whose subject is the user's id."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str, secret: str, algorithm: str) -> str:
    """Verify a token and return its subject.

    Raises TokenError for expired, tampered, or malformed tokens.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise TokenError("token has no subject")
    return subject
