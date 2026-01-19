from collections.abc import Iterable
from uuid import UUID

from src import App
from src.core.modals.modals import MediaTagAssociation
from src.core.repositories.base_repository import BaseRepository, ModelType


class MediaTagRepository(BaseRepository[MediaTagAssociation]):
    def __init__(self):
        super().__init__(session=App.get_db_session(), model=MediaTagAssociation)

    def create(self, entity: ModelType) -> Iterable[ModelType]:
        return super().create(entity)

    def all_create(self, entities: Iterable[ModelType]) -> Iterable[ModelType]:
        self.session.add_all(entities)
        self.session.commit()
        return entities

    def update(self, id: UUID, entity: ModelType) -> ModelType:
        pass

    def delete(self, id: UUID) -> None:
        pass

    def get_by_id(self, id: UUID) -> ModelType:
        pass
