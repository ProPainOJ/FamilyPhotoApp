from enum import Enum
from typing import LiteralString


class AppConstEnum(Enum):
    NAME: str = "FamilyPhoto"
    SHORT_NAME: str = "FP"
    START_FPS: int = 30
    DB_NAME: LiteralString = "family_data.db"