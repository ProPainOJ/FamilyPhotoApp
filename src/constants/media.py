from enum import StrEnum


class FileExtensionType(StrEnum):
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    HEIC = "heic"


FILE_EXTENSION: dict[str, FileExtensionType] = {
    "png": FileExtensionType.PNG,
    "jpeg": FileExtensionType.JPEG,
    "jpg": FileExtensionType.JPG,
    "heic": FileExtensionType.HEIC,
}


class MediaTagFields(StrEnum):
    description = "description_input"
    type = "media_type"
    location = "location"
