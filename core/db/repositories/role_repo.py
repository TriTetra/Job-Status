"""Role repository — search and retrieve canonical roles."""

from typing import Optional, List
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.db.models.role import Role
from core.db.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    model = Role

    def __init__(self, session: Session):
        super().__init__(session)

    def search(self, query: str, limit: int = 10) -> List[Role]:
        """Fuzzy search roles by title + aliases + category."""
        query_lower = query.lower().strip()
        
        return (
            self.session.query(Role)
            .filter(
                or_(
                    Role.title.ilike(f"%{query_lower}%"),
                    Role.category.ilike(f"%{query_lower}%"),
                    # JSONB aliases search (PostgreSQL-specific)
                    Role.aliases.cast(str).ilike(f"%{query_lower}%"),
                )
            )
            .limit(limit)
            .all()
        )

    def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        return self.session.query(Role).filter(Role.id == role_id).first()

    def get_all_by_category(self, category: str) -> List[Role]:
        """Get all roles in a category."""
        return (
            self.session.query(Role)
            .filter(Role.category == category)
            .order_by(Role.title)
            .all()
        )
