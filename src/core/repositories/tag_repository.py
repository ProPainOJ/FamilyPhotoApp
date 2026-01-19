from typing import Iterable, Sequence
from uuid import UUID

from sqlalchemy import select

from src import App
from src.core.modals.modals import Tag
from src.core.repositories.base_repository import BaseRepository, ModelType


class TagRepository(BaseRepository[Tag]):
    def __init__(self) -> None:
        super().__init__(session=App.get_db_session(), model=Tag)

    def create(self, entity: ModelType) -> ModelType:
        return super().create(entity)

    def all_create(self, entities: Sequence[Tag]) -> None:
        return self.session.add_all(entities)

    def update(self, id: UUID, entity: ModelType) -> ModelType:
        raise NotImplementedError

    def delete(self, id: UUID) -> None:
        raise NotImplementedError

    def get_by_id(self, id: UUID) -> ModelType:
        raise NotImplementedError

    def get_by_ids(self, ids: Iterable[UUID] | None) -> Sequence[Tag]:
        if ids:
            stmt = select(
                Tag
            ).where(
                Tag.id.in_(ids)
            )
        else:
            stmt = select(
                Tag
            )
        return self.session.execute(stmt).scalars().all()
