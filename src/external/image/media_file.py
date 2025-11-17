import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.constants.media import FileExtensionType


@dataclass
class MediaFile:
    name: str
    path: Path
    data: bytes | memoryview
    extension: FileExtensionType
    created_at: datetime | None
    loaded_at: type[datetime.timestamp]
    modified_at: datetime | None
    encoding: str | None = "utf-8"
    is_readonly: bool = True

    @property
    def size(self) -> int:
        return os.stat(self.path).st_size

    def exists(self) -> bool:
        """Проверяет, существует ли файл"""
        return self.path.exists()

    def is_directory(self) -> bool:
        """Проверяет, является ли путь директорией"""
        return self.path.is_dir()

    def write_content(self, content: str | bytes) -> None:
        """Записывает содержимое в файл"""
        if self.is_readonly:
            raise PermissionError("Файл доступен только для чтения")

        if isinstance(content, str):
            self.path.write_text(content, encoding=self.encoding)
        else:
            self.path.write_bytes(content)

        self.modified_at = datetime.now()

    def save(self, path_to_copy: Path):
        """Копирует файл в директорию"""
        new_saves_path = shutil.copyfile(self.path, path_to_copy)
        self.path = Path(new_saves_path)
        return self.path

    def delete(self) -> bool:
        """Удаляет файл"""
        if self.exists and self.is_readonly:
            self.path.unlink()
            return True
        return False
