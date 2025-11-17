from enum import Enum, IntEnum
from typing import LiteralString


class AppConstEnum(Enum):
    NAME: str = "FamilyPhoto"
    SHORT_NAME: str = "FP"
    START_FPS: int = 30
    DB_NAME: LiteralString = "family_data.db"
    DEBUG: bool = False


class MouseActionCallbackEnum(IntEnum):
    moving = 1
    click = 2
    release = 3
    drag = 4
