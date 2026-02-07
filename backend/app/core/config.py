from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "NumberSense"
    DATABASE_URL: str = "postgresql://numbersense:numbersense@localhost:5432/numbersense"
    SECRET_KEY: str = "change-me-to-a-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8-hour school day
    ALGORITHM: str = "HS256"

    # Clever SSO
    CLEVER_CLIENT_ID: str = ""
    CLEVER_CLIENT_SECRET: str = ""
    CLEVER_REDIRECT_URI: str = "http://localhost:8000/api/auth/clever/callback"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
