from abc import abstractmethod
from typing import TypeVar, Generic
from uuid import UUID

from sqlalchemy.orm import Session

from ..modals.modals import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):

    def __init__(self, session: Session, model: type[ModelType]) -> None:
        self.modal = model
        self.session = session

    def get_model_instance(self) -> ModelType:
        return self.modal

    @abstractmethod
    def create(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    @abstractmethod
    def update(self, id: UUID, entity: ModelType) -> ModelType:
        pass

    @abstractmethod
    def delete(self, id: UUID) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: UUID) -> ModelType:
        pass
