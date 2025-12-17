from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import LiteralString


@dataclass(frozen=True)
class RGBA:
    r: int
    g: int
    b: int
    a: int = field(default=255)

    def __post_init__(self):
        for channel in (self.r, self.g, self.b, self.a):
            if not 0 <= channel <= 255:
                raise ValueError("RGBA values must be between 0 and 255")

    def __repr__(self):
        return f"{self.__class__.__name__}(r={self.r}, g={self.g}, b={self.b}, a={self.a})"

    def to_tuple(self) -> tuple[int, int, int, int]:
        return self.r, self.g, self.b, self.a


class BaseColorEnumMixin(Enum):
    """Базовый класс для"""

    def __new__(cls, value: RGBA, *args, **kwargs):
        obj = object.__new__(cls)
        if not isinstance(value, RGBA):
            raise TypeError(f"Цвет указан в неверном формате {type(value)}. Допустимо: {type[RGBA]}")
        obj._value_ = value
        return obj


class AppConstEnum(Enum):
    NAME: str = "FamilyPhoto"
    SHORT_NAME: str = "FP"
    START_FPS: int = 60
    DB_NAME: LiteralString = "family_data.db"
    DEBUG: bool = True


class MouseActionCallbackEnum(IntEnum):
    moving = 1
    click = 2
    release = 3
    drag = 4


class NotificationLevelEnum(IntEnum):
    DEFAULT = 1
    WARNING = 2
    ERROR = 3


class ColorsEnum(BaseColorEnumMixin):
    BLACK = RGBA(0, 0, 0)
    WHITE = RGBA(255, 255, 255, 255)
    GREEN = RGBA(0, 255, 0, 255)
    RED = RGBA(255, 0, 0, 255)
    GREY = RGBA(255 // 2, 255 // 2, 255 // 2)
    ORANGE = RGBA(255, 132, 0, 255)
    TRANSPARENT = RGBA(0, 0, 0, 0)
