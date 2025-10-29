from __future__ import annotations

import datetime as dt
import uuid
from enum import Enum as PyEnum
from typing import Optional, Any, cast

from sqlalchemy import ForeignKey, Enum, String, TEXT, Date, DateTime, BigInteger, \
    CheckConstraint, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class GenderType(PyEnum):
    MALE = "male"
    FEMALE = "female"


class MediaType(PyEnum):
    VIDIO = "vidio"
    PHOTO = "photo"
    AUDIO = "audio"


class EventType(PyEnum):
    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    FUNERAL = "funeral"
    OTHER = "other"


class RelationshipType(PyEnum):
    BIOLOGICAL = "biological"
    ADOPTED = "adopted"
    STEP = "step"
    MARRIED = "married"


class Base(DeclarativeBase):
    pass


class Person(Base):
    __tablename__ = "person"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Имя")
    surname: Mapped[str] = mapped_column(String(100), nullable=True, comment="Фамилия")
    patronymic: Mapped[str] = mapped_column(String(100), nullable=True, comment="Отчество")
    created_at: Mapped[Optional[dt.date]] = mapped_column(Date, default=dt.datetime.now)
    birth_date: Mapped[Optional[dt.date]] = mapped_column(Date)
    death_date: Mapped[Optional[dt.date]] = mapped_column(Date)
    bio: Mapped[Optional[str]] = mapped_column(TEXT)
    gender: Mapped[GenderType] = mapped_column(Enum(GenderType))
    faith_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("faith.id", ondelete="SET NULL"),
        nullable=True,
        comment="Вероисповедание",
    )
    faith: Mapped[Optional["Faith"]] = relationship(back_populates="persons")

    father_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("person.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID отца",
    )
    father: Mapped[Optional[uuid.UUID]] = relationship(
        "Person",
        foreign_keys=[father_id],
        remote_side="Person.id",
        backref="father_child",
    )

    mother_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("person.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID матери",
    )
    mother: Mapped[Optional[uuid.UUID]] = relationship(
        "Person",
        foreign_keys=[mother_id],
        remote_side="Person.id",
        backref="mother_child",
    )

    # Для связи родителей/детей через отдельную таблицу
    subordinate_associations: Mapped[Optional[list["PersonPersonAssociation"]]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        foreign_keys="PersonPersonAssociation.leader_id"
    )

    leader_associations: Mapped[Optional[list["PersonPersonAssociation"]]] = relationship(
        back_populates="child",
        cascade="all, delete-orphan",
        foreign_keys="PersonPersonAssociation.subordinate_id"
    )

    # Для связи персона/медиа через отдельную таблицу
    media_associations: Mapped[Optional[list["PersonMediaAssociation"]]] = relationship(
        back_populates="person",
        cascade="all, delete-orphan",
    )

    def __init__(
            self,
            name,
            gender: GenderType,
            surname=None,
            patronymic=None,
            birth_date=None,
            death_date=None,
            bio=None,
            faith_id=None,
            **kw: Any
    ):
        super().__init__(**kw)

        self.name = name
        self.surname = surname
        self.patronymic = patronymic

        if all([
            isinstance(birth_date, dt.datetime),
            isinstance(death_date, dt.datetime),
        ]) and death_date < birth_date:
            raise ValueError(f"Неверно указаны даты! `{death_date}` < `{birth_date}`")

        self.birth_date = birth_date
        self.death_date = death_date
        self.bio = bio
        self.gender = cast(Mapped[GenderType], gender)
        self.faith_id = faith_id

    def __repr__(self):
        return (
            f"<{'👨' if self.gender == GenderType.MALE else '👩‍🦳'}"
            f" | ID: {self.id} | NAME: {self.name} | BERTH_DAY: {self.birth_date}>"
            f"{'' if not self.death_date else f" | DEATH_DATE: {self.death_date}"}"
        )


class PersonPersonAssociation(Base):
    __tablename__ = "person_person_assoc"

    leader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), primary_key=True, comment="Ведущий")
    subordinate_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), primary_key=True, comment="Ведомый")

    relationship_type: Mapped[Optional[RelationshipType]] = mapped_column(Enum(RelationshipType), comment="Тип связи")

    parent: Mapped["Person"] = relationship(
        foreign_keys=[leader_id],
        back_populates="subordinate_associations"
    )
    child: Mapped["Person"] = relationship(
        foreign_keys=[subordinate_id],
        back_populates="leader_associations"
    )

    def __str__(self) -> str:
        return f"< 👨/⛓️‍💥/👩‍🦳 | ID: {self.leader_id} | NAME: {self.subordinate_id}>"


class Media(Base):
    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[MediaType] = mapped_column(Enum(MediaType))
    path: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(300))
    date_taken: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.now, onupdate=dt.datetime.now)
    location: Mapped[Optional[str]] = mapped_column(String(50))
    location_latitude: Mapped[Optional[float]] = mapped_column(comment="Широта")
    location_longitude: Mapped[Optional[float]] = mapped_column(comment="Долгота")
    size_bytes: Mapped[int] = mapped_column(BigInteger, CheckConstraint("size_bytes > 1"))

    tag_associations: Mapped[Optional[list["MediaTagAssociation"]]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
    )

    person_associations: Mapped[Optional[list["PersonMediaAssociation"]]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
    )

    event_associations: Mapped[Optional[list["EventMediaAssociation"]]] = relationship(
        back_populates="media",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"< 💽 | ID: {self.id} | NAME: {self.name} | PATH: {self.path} | SIZE: {self.size_bytes}>"


class MediaTagAssociation(Base):
    __tablename__ = "media_tag_assoc"

    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media.id"), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tag.id"), primary_key=True)

    color: Mapped[Optional[int]] = mapped_column(String(7), nullable=True, comment="Hex color")

    media: Mapped["Media"] = relationship(back_populates="tag_associations")
    tag: Mapped["Tag"] = relationship(back_populates="media_associations")

    def __str__(self) -> str:
        return f"< 💽/⛓️‍💥/🔖 | ID: {self.media_id} | NAME: {self.tag_id}>"


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=True)

    media_associations: Mapped[Optional[list["MediaTagAssociation"]]] = relationship(
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    def __str__(self) -> str:
        return f"< 🔖 | ID: {self.id} | NAME: {self.name}>"


class PersonMediaAssociation(Base):
    __tablename__ = "person_media_assoc"

    person_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("person.id"), primary_key=True)
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media.id"), primary_key=True)

    role: Mapped[Optional[str]] = mapped_column(String(25))
    confirmed: Mapped[bool] = mapped_column(default=False, comment="Подтверждена ли личность на фото?")

    person: Mapped["Person"] = relationship("Person", back_populates="media_associations")
    media: Mapped["Media"] = relationship("Media", back_populates="person_associations")

    def __str__(self) -> str:
        return f"< 👨/⛓️‍💥/💽 | ID: {self.person_id} | NAME: {self.media_id}>"


class Event(Base):
    __tablename__ = "event"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date)
    location: Mapped[Optional[str]] = mapped_column(String(50))
    location_latitude: Mapped[Optional[float]] = mapped_column(comment="Широта")
    location_longitude: Mapped[Optional[float]] = mapped_column(comment="Долгота")
    type: Mapped[EventType] = mapped_column(Enum(EventType))

    media_associations: Mapped[Optional[list["EventMediaAssociation"]]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"< ✨ | ID: {self.id} | NAME: {self.name} | TYPE: {self.type} | LOCATION: {self.location}>"


class EventMediaAssociation(Base):
    __tablename__ = "event_media_assoc"

    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("event.id"), primary_key=True)
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media.id"), primary_key=True)

    event: Mapped["Event"] = relationship(back_populates="media_associations")
    media: Mapped["Media"] = relationship(back_populates="event_associations")

    def __str__(self) -> str:
        return f"< ✨/⛓️‍💥/💽 | ID: {self.event_id} | NAME: {self.media_id}>"


class Faith(Base):
    __tablename__ = "faith"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="Название")
    persons: Mapped[list[Person]] = relationship(back_populates="faith")

    def __str__(self) -> str:
        return f"< ☁️ | ID: {self.id} | NAME: {self.name}>"
