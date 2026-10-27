"""Generic CRUD repository base class."""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from careeros.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Provides get / get_all / create / update / delete.
    Subclasses set `model = SomeModel` and add domain-specific queries.
    """

    model: Type[T]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, **kwargs) -> Optional[T]:
        stmt = select(self.model).filter_by(**kwargs)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all(self, **kwargs) -> List[T]:
        stmt = select(self.model).filter_by(**kwargs)
        return list(self.session.execute(stmt).scalars().all())

    def create(self, **kwargs) -> T:
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.flush()
        return obj

    def update(self, obj: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.session.flush()
        return obj

    def delete(self, obj: T) -> None:
        self.session.delete(obj)
        self.session.flush()
