"""Authentication, JWT tokens, API Key management and Tenant resolution."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
import jwt
from fastapi import Header, HTTPException, status

from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: Raw password.

    Returns:
        Salted bcrypt hash string.
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: Raw password to verify.
        hashed_password: Stored bcrypt hash string.

    Returns:
        True if password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload claims to encode into JWT.
        expires_delta: Optional custom lifetime timedelta.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a signed JWT access token.

    Args:
        token: JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        HTTPException: If token is expired or invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La sesión ha expirado. Por favor inicia sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def generate_api_key(prefix: str = "rke_live_") -> tuple[str, str, str]:
    """Generate a high-entropy API key for external LLM consumption.

    Args:
        prefix: Key prefix indicator.

    Returns:
        Tuple of (full_raw_key, key_hash_sha256, key_masked_display).
        Only key_hash_sha256 should be stored in database!
    """
    raw_token = secrets.token_hex(24)
    full_key = f"{prefix}{raw_token}"
    key_hash = hashlib.sha256(full_key.encode("utf-8")).hexdigest()
    masked = f"{prefix}{raw_token[:4]}...{raw_token[-4:]}"
    return full_key, key_hash, masked


def hash_api_key(raw_key: str) -> str:
    """Hash an API key using SHA-256 for lookup."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class TenantContext:
    """Resolved tenant context for multi-tenancy isolation."""

    def __init__(
        self,
        tenant_id: str,
        is_ephemeral: bool,
        user_id: str | None = None,
        email: str | None = None,
    ):
        self.tenant_id = tenant_id
        self.is_ephemeral = is_ephemeral
        self.user_id = user_id
        self.email = email

    @property
    def is_authenticated(self) -> bool:
        """True if tenant corresponds to a registered account."""
        return not self.is_ephemeral and self.user_id is not None


# In-memory mock stores as fallback
# Keyed by user_id or api_key_hash
MOCK_USERS_DB: dict[str, dict[str, Any]] = {}
MOCK_API_KEYS_DB: dict[str, dict[str, Any]] = {}


async def get_tenant_context(
    authorization: str | None = Header(None),
    x_guest_session: str | None = Header(None),
) -> TenantContext:
    """FastAPI dependency to resolve the tenant context.

    Inspects Authorization header (Bearer JWT or Bearer rke_live_*)
    or X-Guest-Session header. If none is present, generates a guest session.

    Returns:
        TenantContext with tenant_id and ephemeral flag.
    """
    # 1. Check Authorization Bearer header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()

        # Is it an API Key for external LLMs?
        if token.startswith("rke_live_"):
            key_hash = hash_api_key(token)
            # Try PostgreSQL user_db first
            from app.core.user_db import user_db
            key_record = await user_db.get_api_key_by_hash(key_hash)
            if not key_record:
                key_record = MOCK_API_KEYS_DB.get(key_hash)

            if not key_record or not key_record.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API Key inválida o revocada.",
                )
            user_id = key_record["user_id"]
            return TenantContext(
                tenant_id=f"user_{user_id}",
                is_ephemeral=False,
                user_id=user_id,
            )

        # Otherwise it is a user JWT
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no contiene identificador de usuario válido.",
            )
        return TenantContext(
            tenant_id=f"user_{user_id}",
            is_ephemeral=False,
            user_id=user_id,
            email=email,
        )

    # 2. Check X-Guest-Session header
    if x_guest_session and x_guest_session.strip():
        guest_id = x_guest_session.strip().replace(" ", "_")
        return TenantContext(
            tenant_id=f"guest_{guest_id}",
            is_ephemeral=True,
        )

    # 3. Default fallback: new ephemeral guest
    new_guest_id = secrets.token_hex(8)
    return TenantContext(
        tenant_id=f"guest_{new_guest_id}",
        is_ephemeral=True,
    )
