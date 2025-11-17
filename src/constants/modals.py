from enum import StrEnum, IntEnum


class FileSizeEnum(IntEnum):
    B = 0
    KB = 1
    MB = 2
    GB = 3
    TB = 4


class GenderTypeEnum(StrEnum):
    MALE = "male"
    FEMALE = "female"


class MediaTypeEnum(StrEnum):
    VIDIO = "vidio"
    PHOTO = "photo"
    AUDIO = "audio"


class EventTypeEnum(StrEnum):
    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    FUNERAL = "funeral"
    OTHER = "other"


class RelationshipType(StrEnum):
    BIOLOGICAL = "biological"
    ADOPTED = "adopted"
    STEP = "step"
    MARRIED = "married"
