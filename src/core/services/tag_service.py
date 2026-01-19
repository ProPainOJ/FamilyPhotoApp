from typing import Sequence

from src.core.modals.modals import Tag
from src.core.repositories.tag_repository import TagRepository


class TagService:
    def __init__(self, media_repo: TagRepository | None = None) -> None:
        self.repo = TagRepository() if media_repo is None else media_repo

    def get_weak_tags(self) -> Sequence[Tag]:
        return self.repo.get_by_ids(None)

    def create_new_tag(self, name: str, **kwargs) -> Tag:
        tag = Tag(name=name)

        if kwargs.get("id"):
            tag.id = kwargs["id"]
        if kwargs.get("description"):
            tag.description = kwargs["description"]

        return self.repo.create(tag)
