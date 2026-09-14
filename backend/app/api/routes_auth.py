"""Authentication, User management, API Key generation and Session Claiming routes."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import (
    MOCK_API_KEYS_DB,
    MOCK_USERS_DB,
    TenantContext,
    create_access_token,
    generate_api_key,
    get_tenant_context,
    hash_password,
    verify_password,
)
from app.core.config import get_settings
from app.core.user_db import user_db
from app.schemas.auth import (
    APIKeyCreate,
    APIKeyResponse,
    ClaimSessionRequest,
    ClaimSessionResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.vector_stores.store_manager import store_manager

router = APIRouter(prefix="/auth", tags=["Authentication & API Keys"])
settings = get_settings()


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register a new account and get JWT token",
)
async def register(payload: UserRegister) -> TokenResponse:
    """Create a new user account with email and password in PostgreSQL."""
    email_clean = payload.email.lower().strip()

    # 1. Check if user already exists in PostgreSQL Neon
    existing = await user_db.get_user_by_email(email_clean)
    if not existing:
        for u in MOCK_USERS_DB.values():
            if u["email"] == email_clean:
                existing = u
                break

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta registrada con este correo electrónico.",
        )

    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    hashed_pwd = hash_password(payload.password)

    # 2. Persist in PostgreSQL Neon
    try:
        await user_db.create_user(user_id=user_id, email=email_clean, hashed_password=hashed_pwd)
    except Exception as exc:
        # Fallback to in-memory if DB transient error
        MOCK_USERS_DB[user_id] = {
            "user_id": user_id,
            "email": email_clean,
            "hashed_password": hashed_pwd,
            "created_at": now,
        }

    access_token = create_access_token(data={"sub": user_id, "email": email_clean})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        email=email_clean,
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(payload: UserLogin) -> TokenResponse:
    """Authenticate with credentials from PostgreSQL and obtain JWT access token."""
    email_clean = payload.email.lower().strip()

    # 1. Query PostgreSQL Neon
    target_user = await user_db.get_user_by_email(email_clean)
    if not target_user:
        for u in MOCK_USERS_DB.values():
            if u["email"] == email_clean:
                target_user = u
                break

    if not target_user or not verify_password(payload.password, target_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas. Verifique su correo y contraseña.",
        )

    user_id = target_user["user_id"]
    access_token = create_access_token(data={"sub": user_id, "email": email_clean})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user_id,
        email=email_clean,
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
async def get_me(tenant: TenantContext = Depends(get_tenant_context)) -> UserResponse:
    """Retrieve profile and API Key count for authenticated user."""
    if tenant.is_ephemeral or not tenant.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe iniciar sesión para acceder a su perfil.",
        )

    user = await user_db.get_user_by_id(tenant.user_id)
    if not user:
        user = MOCK_USERS_DB.get(tenant.user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    # Fetch active API keys count
    keys = await user_db.list_user_api_keys(tenant.user_id)
    active_keys = len(keys) if keys else sum(
        1 for k in MOCK_API_KEYS_DB.values()
        if k.get("user_id") == tenant.user_id and k.get("is_active", True)
    )

    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        created_at=user["created_at"],
        active_api_keys_count=active_keys,
    )


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    summary="Create a new API Key for external LLM consumption",
)
async def create_api_key(
    payload: APIKeyCreate,
    tenant: TenantContext = Depends(get_tenant_context),
) -> APIKeyResponse:
    """Generate a persistent API key for calling /api/v1/rag/query from external LLMs."""
    if tenant.is_ephemeral or not tenant.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe tener una cuenta registrada para generar API Keys.",
        )

    raw_key, key_hash, masked = generate_api_key()
    key_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Store in PostgreSQL
    try:
        await user_db.create_api_key(
            key_id=key_id,
            user_id=tenant.user_id,
            key_hash=key_hash,
            key_prefix="rke_live_",
            name=payload.name,
        )
    except Exception:
        # In-memory fallback
        MOCK_API_KEYS_DB[key_hash] = {
            "key_id": key_id,
            "user_id": tenant.user_id,
            "name": payload.name,
            "masked_key": masked,
            "created_at": now,
            "is_active": True,
        }

    return APIKeyResponse(
        key_id=key_id,
        name=payload.name,
        masked_key=masked,
        raw_key=raw_key,
        created_at=now,
        is_active=True,
    )


@router.get(
    "/api-keys",
    response_model=list[APIKeyResponse],
    summary="List active API Keys",
)
async def list_api_keys(tenant: TenantContext = Depends(get_tenant_context)) -> list[APIKeyResponse]:
    """List all API Keys belonging to authenticated user."""
    if tenant.is_ephemeral or not tenant.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe tener una cuenta registrada para ver sus API Keys.",
        )

    db_keys = await user_db.list_user_api_keys(tenant.user_id)
    if db_keys:
        return [
            APIKeyResponse(
                key_id=k["key_id"],
                name=k["name"],
                masked_key=f"{k['key_prefix']}****...****",
                raw_key=None,
                created_at=k["created_at"],
                is_active=k.get("is_active", True),
            )
            for k in db_keys
        ]

    # Fallback in-memory
    user_keys = [
        APIKeyResponse(
            key_id=k["key_id"],
            name=k["name"],
            masked_key=k["masked_key"],
            raw_key=None,
            created_at=k["created_at"],
            is_active=k.get("is_active", True),
        )
        for k in MOCK_API_KEYS_DB.values()
        if k.get("user_id") == tenant.user_id and k.get("is_active", True)
    ]
    return sorted(user_keys, key=lambda x: x.created_at, reverse=True)


@router.delete(
    "/api-keys/{key_id}",
    summary="Revoke an API Key",
)
async def revoke_api_key(
    key_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict[str, str]:
    """Revoke an API Key so it can no longer be used by external LLMs."""
    if tenant.is_ephemeral or not tenant.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe iniciar sesión para administrar sus API Keys.",
        )

    revoked = await user_db.revoke_api_key(tenant.user_id, key_id)
    if not revoked:
        for k_hash, k_data in list(MOCK_API_KEYS_DB.items()):
            if k_data.get("key_id") == key_id and k_data.get("user_id") == tenant.user_id:
                k_data["is_active"] = False
                revoked = True
                break

    if not revoked:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key no encontrada.")

    return {"message": "API Key revocada exitosamente."}


@router.post(
    "/claim-session",
    response_model=ClaimSessionResponse,
    summary="Claim guest session and link documents to permanent account",
)
async def claim_session(
    payload: ClaimSessionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> ClaimSessionResponse:
    """Transfer documents from an ephemeral 24h guest session to the authenticated user's account."""
    if tenant.is_ephemeral or not tenant.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Debe iniciar sesión para reclamar un espacio de trabajo efímero.",
        )

    claimed_count = await store_manager.claim_guest_session(payload.guest_session_id, tenant.user_id)
    return ClaimSessionResponse(
        claimed_documents=claimed_count,
        message=f"Se vincularon exitosamente {claimed_count} documentos a su cuenta permanente. Sus datos ya no expirarán.",
    )
