"""
Centralized application configuration.

ALL environment variables must be read through this module. Never call
os.environ / os.getenv anywhere else in the codebase — this keeps secret
rotation and environment auditing a one-file operation.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "AI Research Assistant API"
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # --- Database ---
    DATABASE_URL: str = Field(..., description="postgresql+asyncpg://user:pass@host:5432/db")

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_asyncpg_scheme(cls, v: str) -> str:
        """
        Many hosts (Render, Railway, Heroku-style, Supabase) hand out a plain
        `postgresql://` or `postgres://` connection string. SQLAlchemy's async
        engine requires the `+asyncpg` driver suffix, so normalize it here
        rather than requiring every deploy target to know about this quirk.
        """
        if v.startswith("postgres://"):
            return "postgresql+asyncpg://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    # --- Auth (Clerk) ---
    CLERK_SECRET_KEY: str = Field(..., description="Used server-side to verify session tokens")
    CLERK_JWKS_URL: str = Field(..., description="https://<your-clerk-domain>/.well-known/jwks.json")
    CLERK_ISSUER: str = Field(..., description="https://<your-clerk-domain>")
    CLERK_WEBHOOK_SECRET: str = Field(default="", description="svix secret for /webhooks/clerk")

    # --- OpenAI (required only at call-time, validated lazily so app can boot without it in dev) ---
    OPENAI_API_KEY: str = Field(default="", description="Set via hosting platform env vars in production")
    OPENAI_BASE_URL: str = Field(
        default="",
        description="Leave blank for OpenAI. Set to https://openrouter.ai/api/v1 (or another "
        "OpenAI-compatible endpoint) to use an alternate provider.",
    )
    OPENAI_CHAT_MODEL: str = "gpt-4.1"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # --- Vector store ---
    VECTOR_STORE_PROVIDER: Literal["chroma", "pinecone"] = "chroma"
    CHROMA_DB_PATH: str = "./chroma_data"
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = ""

    # --- Storage ---
    STORAGE_PROVIDER: Literal["s3", "supabase"] = "s3"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = ""
    AWS_REGION: str = "us-east-1"

    # --- Billing ---
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = Field(default="", description="Stripe Price ID for the Pro plan")
    STRIPE_PRICE_ID_TEAM: str = Field(default="", description="Stripe Price ID for the Team plan")

    # --- Rate limiting ---
    RATE_LIMIT_PER_MINUTE: int = 60

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — import this, not Settings() directly."""
    return Settings()
