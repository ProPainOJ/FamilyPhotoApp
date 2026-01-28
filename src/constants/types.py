from typing import TypeAlias, TypeVar

# TypeAlias
DPGColor: TypeAlias = tuple[int, int, int, int] | tuple[int, int, int]
DPGTag: TypeAlias = int | str

# TypeVar
POSITION = TypeVar('POSITION', int, float)
ElementName = TypeVar('ElementName', str, int)

Point = tuple[POSITION, POSITION]
