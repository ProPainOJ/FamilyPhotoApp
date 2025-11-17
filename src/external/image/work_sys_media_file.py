import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import LiteralString

from src.constants.media import FileExtensionType, FILE_EXTENSION
from src.core.exceptions.application_exception import FileSuffixError
from src.external.image.media_file import MediaFile


class WorkWithSystemMedia:
    @staticmethod
    def get_media_file_info(file: MediaFile | Path) -> type[os.stat]:
        if isinstance(file, MediaFile):
            file = file.path

        if not os.path.exists(file):
            raise FileNotFoundError

        return os.stat(file)

    @staticmethod
    def create_media_file(path: Path | LiteralString | str) -> MediaFile | FileNotFoundError:
        """Получаем информацию о файл из системы"""
        suffix: FileExtensionType | None = None

        path = Path(path)
        real_name = path.name.rstrip(path.suffix)
        real_suffix = path.suffix[1:]

        for suf in FileExtensionType:
            if real_suffix == suf:
                suffix = FILE_EXTENSION[suf]
                break

        if suffix is None:
            raise FileSuffixError(
                msg=f"Выбрано недопустимое расширение файла!",
                comment=f"Доступные расширения: {[str(suffix) for suffix in FileExtensionType]}"
            )

        try:
            file_stats = WorkWithSystemMedia.get_media_file_info(path)

            binary_file = open(path, "rb").read()
            blob = sqlite3.Binary(binary_file)

            return MediaFile(
                name=real_name,
                path=path,
                extension=suffix,
                created_at=datetime.fromtimestamp(file_stats.st_ctime),
                modified_at=datetime.fromtimestamp(file_stats.st_mtime),
                loaded_at=None,
                data=blob,
            )
        except FileNotFoundError:
            raise FileNotFoundError(f"Файл '{path}' не найдет! \nВозможно файл был удалён или перемешён!")
