"""PostgreSQL relational storage for users and API keys."""

import logging
from datetime import datetime, timezone
from typing import Any
import psycopg
from psycopg.rows import dict_row

from app.core.config import get_settings

logger = logging.getLogger("rag_engine.user_db")
settings = get_settings()


class UserDatabase:
    """Relational PostgreSQL storage for user accounts and developer API keys."""

    def __init__(self, connection_url: str | None = None) -> None:
        self._url = connection_url or settings.POSTGRES_URL
        self._initialized = False

    async def _get_connection(self) -> psycopg.AsyncConnection:
        """Establish async connection to PostgreSQL Neon."""
        return await psycopg.AsyncConnection.connect(
            self._url,
            connect_timeout=10,
            row_factory=dict_row,
        )

    async def initialize(self) -> None:
        """Ensure users and api_keys relational tables and indexes exist."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    # 1. Users table
                    await cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS users (
                            user_id VARCHAR(64) PRIMARY KEY,
                            email VARCHAR(255) UNIQUE NOT NULL,
                            hashed_password TEXT NOT NULL,
                            full_name VARCHAR(255),
                            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                        );
                        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                        """
                    )

                    # 2. API Keys table with foreign key cascade
                    await cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS api_keys (
                            key_id VARCHAR(64) PRIMARY KEY,
                            user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                            key_hash VARCHAR(128) UNIQUE NOT NULL,
                            key_prefix VARCHAR(16) NOT NULL,
                            name VARCHAR(128) NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            last_used_at TIMESTAMPTZ,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE
                        );
                        CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
                        CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
                        """
                    )
                    await conn.commit()
            self._initialized = True
            logger.info("Relational user and api_keys tables initialized in PostgreSQL Neon.")
        except Exception as exc:
            logger.error("Failed to initialize user tables in PostgreSQL: %s", exc)

    async def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        """Fetch user record by normalized lowercase email."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT user_id, email, hashed_password, created_at FROM users WHERE email = %s LIMIT 1;",
                        (email.lower().strip(),),
                    )
                    row = await cur.fetchone()
                    return dict(row) if row else None
        except Exception as exc:
            logger.error("Error in get_user_by_email: %s", exc)
            return None

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        """Fetch user record by unique user_id."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "SELECT user_id, email, hashed_password, created_at FROM users WHERE user_id = %s LIMIT 1;",
                        (user_id,),
                    )
                    row = await cur.fetchone()
                    return dict(row) if row else None
        except Exception as exc:
            logger.error("Error in get_user_by_id: %s", exc)
            return None

    async def create_user(
        self,
        user_id: str,
        email: str,
        hashed_password: str,
    ) -> dict[str, Any]:
        """Insert a newly registered user account into PostgreSQL Neon."""
        now = datetime.now(timezone.utc)
        clean_email = email.lower().strip()
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO users (user_id, email, hashed_password, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING user_id, email, created_at;
                    """,
                    (user_id, clean_email, hashed_password, now, now),
                )
                row = await cur.fetchone()
                await conn.commit()
                return dict(row)

    async def create_api_key(
        self,
        key_id: str,
        user_id: str,
        key_hash: str,
        key_prefix: str,
        name: str,
    ) -> dict[str, Any]:
        """Store a newly generated API key in PostgreSQL."""
        now = datetime.now(timezone.utc)
        async with await self._get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO api_keys (key_id, user_id, key_hash, key_prefix, name, created_at, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING key_id, user_id, key_prefix, name, created_at, is_active;
                    """,
                    (key_id, user_id, key_hash, key_prefix, name, now),
                )
                row = await cur.fetchone()
                await conn.commit()
                return dict(row)

    async def get_api_key_by_hash(self, key_hash: str) -> dict[str, Any] | None:
        """Fetch active API key record by SHA-256 hash."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT key_id, user_id, key_prefix, name, is_active, last_used_at
                        FROM api_keys
                        WHERE key_hash = %s AND is_active = TRUE
                        LIMIT 1;
                        """,
                        (key_hash,),
                    )
                    row = await cur.fetchone()
                    if row:
                        now = datetime.now(timezone.utc)
                        await cur.execute(
                            "UPDATE api_keys SET last_used_at = %s WHERE key_id = %s;",
                            (now, row["key_id"]),
                        )
                        await conn.commit()
                        return dict(row)
                    return None
        except Exception as exc:
            logger.error("Error in get_api_key_by_hash: %s", exc)
            return None

    async def list_user_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """List all active API keys belonging to a user."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT key_id, user_id, key_prefix, name, created_at, last_used_at, is_active
                        FROM api_keys
                        WHERE user_id = %s
                        ORDER BY created_at DESC;
                        """,
                        (user_id,),
                    )
                    rows = await cur.fetchall()
                    return [dict(r) for r in rows]
        except Exception as exc:
            logger.error("Error in list_user_api_keys: %s", exc)
            return []

    async def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """Soft-delete / revoke an API key."""
        try:
            async with await self._get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "UPDATE api_keys SET is_active = FALSE WHERE key_id = %s AND user_id = %s;",
                        (key_id, user_id),
                    )
                    await conn.commit()
                    return cur.rowcount > 0
        except Exception as exc:
            logger.error("Error in revoke_api_key: %s", exc)
            return False


user_db = UserDatabase()
