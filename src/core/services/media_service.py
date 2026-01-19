from typing import Sequence, Type, Iterable
from uuid import UUID

from src.constants.error_messages import DataBaseMessagesEnum
from src.core.modals.modals import Media, MediaTypeEnum, Tag, MediaTagAssociation
from src.core.repositories.media_repository import MediaRepository
from src.core.repositories.media_tag_repository import MediaTagRepository
from src.core.repositories.tag_repository import TagRepository
from src.external.image.work_sys_media_file import FileExtensionType


class MediaService:
    def __init__(self, media_repo: MediaRepository | None = None) -> None:
        self.repo = MediaRepository() if media_repo is None else media_repo
        self.tag_repo = TagRepository()

    @staticmethod
    def media_forming(media: None | Media = None, **kwargs) -> Media:
        if not media:
            media = Media()
        for arg in kwargs:
            if arg not in Media.__table__.columns:
                continue
            setattr(media, arg, kwargs[arg])

        return media

    def create_media(self,
                     name: str,
                     media_type: MediaTypeEnum,
                     extension: FileExtensionType,
                     size_bytes: int,
                     data: bytes,
                     **kwargs) -> Media:

        if extension not in FileExtensionType:
            raise TypeError(DataBaseMessagesEnum.file_extension.format(
                [accept_type for accept_type in FileExtensionType]
            ))

        media = self.media_forming(
            Media(name=name, type=media_type, size_bytes=size_bytes, extension=extension, data=data),
            **kwargs
        )

        return self.repo.create(entity=media)

    @staticmethod
    def create_media_with_tags(media: Media, tags: Iterable[Tag]) -> Iterable[MediaTagAssociation]:
        """Создание Ассоциативной связи между меди и тегами.

        :param media: Объект меди
        :param tags: Медия теги
        :return:
        """
        media_tag_assoc = []
        for tag in tags:
            media_tag_assoc.append(MediaTagAssociation(media_id=media.id, tag_id=tag.id))
        return MediaTagRepository().all_create(media_tag_assoc)

    def get_media_by_id(self, id: UUID) -> Type[Media]:
        return self.repo.get_by_id(id)

    def get_first_media(self) -> Media | None:
        return self.repo.get_one()

    def get_weak_media_files(self) -> Sequence[Media]:
        return self.repo.get_by_ids(None)

    def get_active_media_files(self) -> Sequence[Media]:
        return self.repo.get_active()
