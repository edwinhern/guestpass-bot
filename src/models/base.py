"""SQLAlchemy Core database setup."""

from sqlalchemy import MetaData, create_engine
from sqlalchemy.pool import NullPool

from src.config import config

# Create SQLAlchemy engine
engine = create_engine(
    config.database.url,
    poolclass=NullPool if config.environment == "development" else None,
    echo=config.environment == "development",
)

# Create metadata object for table definitions
metadata = MetaData()
