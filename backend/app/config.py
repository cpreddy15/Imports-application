import os


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./tradeflow.db")
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
    cors_origins: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    seed_demo_data: bool = os.getenv("SEED_DEMO_DATA", "true").lower() == "true"


settings = Settings()
