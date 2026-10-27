"""Database plumbing shared by every feature.

    base.py        declarative Base + TimestampMixin
    connection.py  engine, session_scope (registers all models)
    models.py      registry of every ORM model (Alembic, mapper configuration)
    repository.py  BaseRepository[T]
    legacy/        tables kept in the DB but no longer used by code
    migrations/    Alembic (alembic -c careeros/db/alembic.ini upgrade head)

Each feature owns its models/ and repositories/ (e.g. careeros.jobs.models).
"""
