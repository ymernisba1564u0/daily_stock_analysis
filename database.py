"""Database connection and session management for daily stock analysis."""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import QueuePool

from config import Config, validate

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def create_db_engine(config: Config):
    """Create and configure the SQLAlchemy engine.

    Args:
        config: Application configuration instance.

    Returns:
        Configured SQLAlchemy engine.
    """
    db_url = config.get_db_url()

    engine_kwargs = {
        "poolclass": QueuePool,
        "pool_size": config.DB_POOL_SIZE if hasattr(config, "DB_POOL_SIZE") else 5,
        "max_overflow": config.DB_MAX_OVERFLOW if hasattr(config, "DB_MAX_OVERFLOW") else 10,
        "pool_pre_ping": True,
        "pool_recycle": 1800,  # Reduced from 3600 to 30 min; my DB drops idle connections sooner
        "echo": config.DEBUG if hasattr(config, "DEBUG") else False,
    }

    # SQLite doesn't support connection pooling options the same way
    if db_url.startswith("sqlite"):
        engine_kwargs.pop("poolclass", None)
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs["connect_args"] = {"check_same_thread": False}

    engine = create_engine(db_url, **engine_kwargs)

    # Enable WAL mode for SQLite to improve concurrent read performance
    if db_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info("Database engine created for: %s", db_url.split("@")[-1] if "@" in db_url else db_url)
    return engine


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, config: Config):
        """Initialize the database manager.

        Args:
            config: Application configuration instance.
        """
        validate(config)
        self.config = config
        self.engine = create_db_engine(config)
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    def create_tables(self) -> None:
        """Create all tables defined in ORM models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully.")
        except SQLAlchemyError as e:
            logger.error("Failed to create database tables: %s", e)
            raise

    def drop_tables(self) -> None:
        """Drop all tables — use with caution in production."""
        