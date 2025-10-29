import os
from glob import glob

from typing import LiteralString, NewType, Union

FileName = NewType("FileName", Union[str | LiteralString])


def join_exist_path(start_path: FileName, dirs_path: tuple[str, ...]) -> LiteralString:
    for dir_path in dirs_path:
        if not os.path.exists(os.path.join(start_path, dir_path)):
            raise FileNotFoundError(f"Каталог {dir_path} не был найден по указанному пути: {start_path}!")
        start_path = os.path.join(start_path, dir_path)

    return start_path


def delete_all_files_in_dir(dir_path: LiteralString, extension: str = ".png") -> None:
    for file in list(glob(os.path.join(dir_path, f"*{extension}"))):
        os.remove(file)


def delete_files_in_dir_by_names(
        dir_path: LiteralString,
        file_names: tuple[LiteralString, ...]
) -> tuple[LiteralString, ...] | None:
    non_existent_file: tuple[LiteralString, ...] = tuple()

    for file in file_names:
        dir_file = os.path.join(dir_path, file)
        if not os.path.exists(dir_file):
            os.path.exists(dir_file)
            non_existent_file += (file,)
        else:
            os.remove(dir_file)
    return non_existent_file or None


def get_dir_files(dir_path: str) -> list[str]:
    return os.listdir(dir_path)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    if not all(0 <= color_val <= 255 for color_val in (r, g, b)):
        raise ValueError("RGB значения должны быть между 0 и 255!")
    return f'#{r:02X}{g:02X}{b:02X}'
