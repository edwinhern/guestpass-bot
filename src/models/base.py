from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from src.config import get_config

config = get_config()


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


engine = create_engine(
    config.database.url,
    poolclass=NullPool if config.environment == "development" else None,
    echo=config.environment == "development",
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
