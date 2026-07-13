"""PostgreSQL connection pool manager (singleton)."""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from .models import Base


def _load_dotenv() -> None:
    """Load .env from project root into os.environ (no external deps)."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


_load_dotenv()


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
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError(
                "DATABASE_URL not set — check your .env file.\n"
                "Expected: postgresql+psycopg://career_os:<pw>@localhost:5432/career_os"
            )

        self._engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
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
        print("All tables created")

    def drop_all_tables(self) -> None:
        """DANGER: development only."""
        Base.metadata.drop_all(self._engine)
        print("WARNING: all tables dropped")


# Module-level singleton
db = DatabaseConnection()


def get_session() -> Session:
    return db.get_session()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    with db.session_scope() as session:
        yield session
