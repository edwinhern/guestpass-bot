from functools import lru_cache

from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseModel):
    user: str = Field(..., description="Postgres username")
    password: str = Field(..., description="Postgres password")
    host: str = Field(..., description="Postgres host")
    port: int = Field(..., description="Postgres port")
    database: str = Field(..., description="Postgres database name")

    @property
    def url(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DiscordConfig(BaseModel):
    bot_token: str = Field(..., description="Discord Bot Token")
    admin_role_id: str = Field(..., description="Discord Admin Role ID")


class PPOAConfig(BaseModel):
    registration_code: str = Field(..., description="PPOA registration code")
    default_apartment: str = Field(..., description="Default apartment for guests")


class NotificationConfig(BaseModel):
    hours_before_expiry: int = Field(..., ge=1)
    auto_reregister_hours_before_expiry: int = Field(..., ge=1)


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
    )

    database: DatabaseConfig
    discord: DiscordConfig
    ppoa: PPOAConfig
    notification: NotificationConfig

    environment: str = Field(..., description="Environment name")


@lru_cache
def get_config() -> AppConfig:
    try:
        return AppConfig()
    except ValidationError as err:
        print("\n CONFIGURATION ERROR — Missing or Invalid Environment Variables\n")
        print(err)
        raise SystemExit(1) from err


config = get_config()
