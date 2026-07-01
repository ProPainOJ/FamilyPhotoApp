from enum import StrEnum


class FileExtensionType(StrEnum):
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    HEIC = "heic"
    MP4 = "mp4"


FILE_EXTENSION: dict[str, FileExtensionType] = {
    "png": FileExtensionType.PNG,
    "jpeg": FileExtensionType.JPEG,
    "jpg": FileExtensionType.JPG,
    "heic": FileExtensionType.HEIC,
    "mp4": FileExtensionType.MP4,
}


class MediaTagFields(StrEnum):
    description = "description_input"
    type = "media_type"
    location = "location"
