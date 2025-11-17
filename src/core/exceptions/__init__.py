from typing_extensions import Protocol


class HasStr(Protocol):
    def __str__(self) -> str: ...


class BaseError(Exception):
    """Основной класс ошибки."""

    def __init__(self, msg: str, targets: list[HasStr] | None = None, comment: str | None = None,
                 pre_decision: str | None = None) -> None:
        """Создание описания ошибки.

        :param msg: Текст ошибки
        :param targets: Объект ошибки
        :param comment: Комментарий к ошибке
        :param pre_decision: Возможное решение
        """
        self.msg = msg
        self.target = targets or ("",)
        self.comment = comment
        self.pre_decision = pre_decision

    def __str__(self) -> str:
        return (
            f"\n>>> ERROR MESSAGE: {self.msg}"
            f"\n\tERROR comment: {self.comment}"
            f"\n\tERROR TARGET: <{[target.__str__() for target in self.target]}>"
            f"\n\tPreliminary ERROR decision: {self.pre_decision}\n"
        )
