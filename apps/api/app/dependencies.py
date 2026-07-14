"""FastAPI dependencies — DB session and user identity."""

from typing import Generator

from fastapi import Header

from core.db.connection import db


def get_db_session() -> Generator:
    with db.session_scope() as session:
        yield session


def get_user_id(x_user_id: str = Header(default="default")) -> str:
    return x_user_id
