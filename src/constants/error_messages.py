from enum import StrEnum


class ErrorMessagesEnum(StrEnum):
    pass


class FieldsMessagesEnum(ErrorMessagesEnum):
    description: str = "Описание: "
    non_selected: str = "Ничего не добавлено..."


class NewFileFieldsMessagesEnum(ErrorMessagesEnum):
    no_tags: str = f"Выбранные теги: {FieldsMessagesEnum.non_selected}"


class DataBaseMessagesEnum(ErrorMessagesEnum):
    file_extension = f'Incorrect file extension type! Accept types: <{0}>'
