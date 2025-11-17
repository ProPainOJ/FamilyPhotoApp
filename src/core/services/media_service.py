from typing import Sequence, Type
from uuid import UUID

from src.external.image.work_sys_media_file import FileExtensionType
from src.core.modals.modals import Media, MediaTypeEnum
from src.core.repositories.media_repository import MediaRepository


class MediaService:
    def __init__(self, media_repo: MediaRepository = MediaRepository()) -> None:
        self.repo = media_repo

    def create_media(self,
                     name: str,
                     media_type: MediaTypeEnum,
                     extension: FileExtensionType,
                     size_bytes: int,
                     data: bytes,
                     **kwargs) -> Media:

        if extension not in FileExtensionType:
            raise TypeError(f'Incorrect file extension type!'
                            f'Accept types: <{[accept_type for accept_type in FileExtensionType]}>')

        media = Media(name=name, type=media_type, size_bytes=size_bytes, extension=extension, data=data)

        for arg in kwargs:
            if arg not in Media.__table__.columns:
                continue
            setattr(media, arg, kwargs[arg])

        return self.repo.create(entity=media)

    def get_media_by_id(self, id: UUID) -> Type[Media]:
        return self.repo.get_by_id(id)

    def get_first_media(self) -> Media | None:
        return self.repo.get_one()

    def get_weak_media_files(self) -> Sequence[Media]:
        return self.repo.get_by_ids(None)
