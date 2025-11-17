from typing import Type, Iterable, Optional
from uuid import UUID

from sqlalchemy import select, Sequence

from .base_repository import ModelType
from ..modals.modals import Media
from ..repositories.base_repository import BaseRepository
from ... import App


class MediaRepository(BaseRepository[Media]):

    def __init__(self):
        super().__init__(session=App.get_db_session(), model=Media)

    def create(self, entity: ModelType) -> ModelType:
        return super().create(entity)

    def get_by_id(self, id: UUID) -> Type[Media]:
        return self.session.query(Media).filter(Media.id == id).one()

    def update(self, id: UUID, user_data):
        media = self.get_by_id(id)

        for key, value in user_data.items():
            setattr(media, key, value)
        self.session.commit()
        return media

    def delete(self, id: UUID) -> None:
        media = self.get_by_id(id)
        self.session.delete(media)
        self.session.commit()

    def get_by_ids(self, ids: Optional[Iterable[UUID]]) -> Sequence[Media]:
        if ids:
            stmt = select(
                Media
            ).where(
                Media.id.in_(ids)
            )
        else:
            stmt = select(
                Media
            )
        return self.session.execute(stmt).scalars().all()

    def get_one(self) -> Media | None:
        return self.session.execute(select(Media)).scalars().first()
