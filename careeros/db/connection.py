"""PostgreSQL connection pool manager (singleton)."""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from careeros.shared.config import get_settings

import careeros.db.models  # noqa: F401 — registers every ORM model on Base.metadata
from careeros.db.base import Base

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Singleton that owns the engine + session factory.

    pool_pre_ping=True  — auto-reconnect on stale connections
    pool_recycle=3600   — recycle connections after 1 hour
    expire_on_commit=False — objects stay usable after session.commit()
    """

    _instance: "DatabaseConnection | None" = None
    _engine: Engine | None = None
    _session_factory: sessionmaker | None = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        settings = get_settings()
        url = settings.database_url
        if not url:
            raise ValueError(
                "DATABASE_URL not set — check your .env file.\n"
                "Expected: postgresql+psycopg://career_os:<pw>@localhost:5432/career_os"
            )

        self._engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.db_echo,
            # Fail fast when the DB is unreachable instead of hanging the request
            connect_args={"connect_timeout": settings.db_connect_timeout},
        )

        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def get_session(self) -> Session:
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Auto-commit on success, rollback on error, always closes."""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_all_tables(self) -> None:
        """Development helper — prefer Alembic in production."""
        Base.metadata.create_all(self._engine)
        logger.info("All tables created")

    def drop_all_tables(self) -> None:
        """DANGER: development only."""
        Base.metadata.drop_all(self._engine)
        logger.warning("All tables dropped")


# Module-level singleton
db = DatabaseConnection()


def get_session() -> Session:
    return db.get_session()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    with db.session_scope() as session:
        yield session
