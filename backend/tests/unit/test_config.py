"""Unit tests for Settings, in particular DATABASE_URL normalization."""
from app.core.config import Settings


def _make_settings(database_url: str) -> Settings:
    return Settings(
        DATABASE_URL=database_url,
        CLERK_SECRET_KEY="sk_test_x",
        CLERK_JWKS_URL="https://example.clerk.accounts.dev/.well-known/jwks.json",
        CLERK_ISSUER="https://example.clerk.accounts.dev",
    )


def test_postgres_scheme_normalized_to_asyncpg():
    settings = _make_settings("postgres://user:pass@host:5432/db")
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/db"


def test_postgresql_scheme_normalized_to_asyncpg():
    settings = _make_settings("postgresql://user:pass@host:5432/db")
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/db"


def test_already_asyncpg_scheme_left_untouched():
    settings = _make_settings("postgresql+asyncpg://user:pass@host:5432/db")
    assert settings.DATABASE_URL == "postgresql+asyncpg://user:pass@host:5432/db"
