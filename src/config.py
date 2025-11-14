"""Configuration management using environment variables."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class DatabaseConfig:
    """Database configuration."""

    user: str
    password: str
    host: str
    port: int
    database: str

    @property
    def url(self) -> str:
        """Get the database connection URL."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class DiscordConfig:
    """Discord bot configuration."""

    bot_token: str
    admin_role_id: str


@dataclass
class PPOAConfig:
    """PPOA parking registration configuration."""

    registration_code: str
    default_apartment: str


@dataclass
class NotificationConfig:
    """Notification settings."""

    hours_before_expiry: int
    auto_reregister_hours_before_expiry: int


@dataclass
class Config:
    """Application configuration."""

    database: DatabaseConfig
    discord: DiscordConfig
    ppoa: PPOAConfig
    notification: NotificationConfig
    environment: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            database=DatabaseConfig(
                user=os.getenv("POSTGRES_USER", "guestpass_user"),
                password=os.getenv("POSTGRES_PASSWORD", ""),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                database=os.getenv("POSTGRES_DB", "guestpass_db"),
            ),
            discord=DiscordConfig(
                bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
                admin_role_id=os.getenv("ADMIN_ROLE_ID", ""),
            ),
            ppoa=PPOAConfig(
                registration_code=os.getenv("PPOA_REGISTRATION_CODE", "MAVP"),
                default_apartment=os.getenv("DEFAULT_APARTMENT", "215"),
            ),
            notification=NotificationConfig(
                hours_before_expiry=int(os.getenv("NOTIFICATION_HOURS_BEFORE_EXPIRY", "2")),
                auto_reregister_hours_before_expiry=int(os.getenv("AUTO_REREGISTER_HOURS_BEFORE_EXPIRY", "2")),
            ),
            environment=os.getenv("ENVIRONMENT", "development"),
        )


# Global config instance
config = Config.from_env()
