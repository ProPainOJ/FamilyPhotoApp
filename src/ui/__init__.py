from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Final

import dearpygui.dearpygui as dpg

from src import App
from src import WinConstEnum as WCE
from src.constants.types import DPGTag, MyIterType
from src.core.exceptions.application_exception import TagWindowError, NotImplementClassError


class BaseAppThemeHandler:
    """Основной класс для всех тем-классов окон приложения"""

    _cache: dict[DPGTag, DPGTag] = {}

    @classmethod
    def create_theme(cls, theme_func: Callable) -> DPGTag:
        """Создает или возвращает кэшированную тему по тегу"""
        tag = theme_func.__name__

        if tag in cls._cache:
            return cls._cache[tag]

        with dpg.theme(tag=tag) as created_tag:
            theme_func()

        cls._cache[tag] = created_tag
        return created_tag

    @classmethod
    def set_theme(cls, app_element: DPGTag | None, theme_func: Callable) -> None:
        """Применение темы к элементу приложения

        :param app_element: Элемент приложения к которой применяется тема
        :param theme_func: Функция определения компонент-темы
        """
        if app_element is None:
            app_element = dpg.last_item()
        dpg.bind_item_theme(app_element, cls.create_theme(theme_func))

    @classmethod
    def clear_theme_cache(cls) -> None:
        """Удаление всего кеша тем приложения"""
        for theme_tag in cls._cache:
            dpg.delete_item(theme_tag)
            dpg.remove_alias(theme_tag)
        cls._cache = {}


class BaseAppCallbackHandler:
    """Основной класс для всех коллбек классов окон приложения"""

    @classmethod
    def check_parent_instance_state(cls, attr_name: str = "_instance") -> bool:
        """Проверка наличие ссылки на объект класса управления.

        :param attr_name: Название атрибута
        :return: Флаг наличие состояния
        """
        return True if hasattr(cls, attr_name) else False


class AppWindowABC(ABC):
    """Основной абстрактный класс для всех окон приложения."""

    @abstractmethod
    def create_window(self):
        """Создание основного фрейма приложения"""
        pass

    @abstractmethod
    def create_children_windows(self):
        """Создание дочерних фреймов основного окна приложения"""
        ...


class AppTagHelper:
    TAG: Final[str] = "tag"
    TAG_CONNECTOR: Final[str] = "_"
    _window_elements_tag: dict[str, dict[str, str]] = {"OTHER": {"test": "OTHER_test_tag"}}

    @classmethod
    def set_new_el_tag(cls, class_tag_name: str | None, new_tag_name: str | MyIterType) -> str:
        """Создание нового тега приложения. (Формат: `class_name_tag`).

        :param class_tag_name: Заглавное имя тега (`__class__.__name__`/`OTHER`)
        :param new_tag_name: Имя нового тега

        :return: Тег приложения
        """
        if class_tag_name is None:
            class_tag_name = "OTHER"

        if class_tag_name not in cls._window_elements_tag:
            cls._window_elements_tag[class_tag_name] = {}

        if new_tag_name in cls._window_elements_tag[class_tag_name]:
            tag_name = cls.get_el_tag(class_tag_name, new_tag_name)
            exist_tag_type = dpg.get_item_type(tag_name)
            raise TagWindowError(
                msg="Элемент с таким тегом уже существует!",
                targets=["id"],
                comment=f"Созданный тип элемент: {exist_tag_type}",
                pre_decision=f"Delete tag: {tag_name}",
            )
        else:
            if isinstance(new_tag_name, str):
                if cls.TAG_CONNECTOR in new_tag_name and new_tag_name.split(cls.TAG_CONNECTOR)[-1] == cls.TAG:
                    new_tag_name = new_tag_name.rstrip(cls.TAG_CONNECTOR + cls.TAG)
            else:
                if new_tag_name[-1] == cls.TAG:
                    new_tag_name = new_tag_name[:-1]
                new_tag_name = cls.TAG_CONNECTOR.join(new_tag_name)

            new_tag = cls.TAG_CONNECTOR.join((f"{class_tag_name}", f"{new_tag_name}", cls.TAG))

        cls._window_elements_tag[class_tag_name][new_tag_name] = new_tag

        return cls.get_el_tag(tag_target=class_tag_name, tag_name=new_tag_name)

    @classmethod
    def get_el_tag(cls, tag_target: str, tag_name: MyIterType | str) -> str:
        """Простоя генерация стандартизированного `tag` имени.

        :param tag_target: Начало тега (Обычно имя класса)
        :param tag_name: Основное имя тега

        :return: Имя тега элемента приложения в формате `ClassName_name_tag`
        """
        if isinstance(tag_name, str):
            if cls.TAG_CONNECTOR in tag_name:
                tag_name = tag_name.split(cls.TAG_CONNECTOR)
                if tag_name[-1] == cls.TAG:
                    tag_name = tag_name[-1]
                tag_name = (cls.TAG_CONNECTOR.join(tag_name),)
            else:
                tag_name = (tag_name,)
        try:
            tag = cls._window_elements_tag[tag_target][
                cls.TAG_CONNECTOR.join(tag_name)]
            return tag
        except KeyError:
            raise TagWindowError(
                msg="Тег с данным именем не создан!",
                targets=[tag_target, cls.TAG_CONNECTOR.join(tag_name)],
                pre_decision=f"Создать тег через: {cls.set_new_el_tag.__name__}",
            ) from KeyError

    @classmethod
    def delete_tag(cls, tag_target: str, tag_name: str, del_obj_by_tag: bool = False) -> str:
        """Удаление тега.

        :param tag_target: Имя класса тега
        :param tag_name: Имя тега
        :param del_obj_by_tag: Удалить ли объект вместе с тегом
        """
        if tag_target not in cls._window_elements_tag:
            raise TagWindowError(
                msg="Нет тегов у данного класса!",
                targets=[str(key) for key in cls._window_elements_tag],
                pre_decision=f"Создать первый тег для класса через {cls.set_new_el_tag.__name__}"
            )
        if tag_name not in cls._window_elements_tag[tag_target]:
            raise TagWindowError(
                msg="Данный тег не создан!",
                targets=[f"{tag_name}"]
            )

        deleted_tag = cls.get_el_tag(tag_target, tag_name)
        del cls._window_elements_tag[tag_target][tag_name]

        if dpg.does_alias_exist(deleted_tag):
            if del_obj_by_tag and dpg.does_item_exist(deleted_tag):
                dpg.delete_item(deleted_tag)
                dpg.remove_alias(deleted_tag)
            else:
                dpg.remove_alias(deleted_tag)
        return deleted_tag

    @classmethod
    def get_all_el_tag(cls) -> tuple[str, ...]:
        """Получение всех тегов приложения.

        :return: Список тегов приложения
        """
        all_tags = tuple()

        for main_tag in cls._window_elements_tag:
            for tag in cls._window_elements_tag[main_tag].values():
                all_tags += (tag,)
        return all_tags


class BaseAppWindow(AppWindowABC, AppTagHelper):
    """Базовый класс для создания UI приложения."""
    MAIN_CONTAINER_TAG_NAME: Final[str] = ("main", "content", "container")
    SIDEBAR_WIDTH = WCE.SIDE_BAR_WIDTH.value
    FOOTER_HEIGHT: int = 0 if not WCE.SHOW_FOOTER.value else WCE.FOOTER_HEIGHT.value
    UPPER_HEIGHT: int = None

    def __init_subclass__(cls, **kwargs):
        """Проверка, что класс имеет выделанный обработчик коллбеков."""
        cls.__check_subclasses(BaseAppThemeHandler)
        cls.__check_subclasses(BaseAppCallbackHandler)
        super().__init_subclass__(**kwargs)

    def __init__(self, main_app: App, class_name: str) -> None:
        """Создание UI-класса приложения.

        :param main_app: Базовый класс приложения `App`.
        :param class_name: Имя UI-класса.
        """
        self.app = main_app
        self.class_name = class_name
        self.main_content_tag = self.set_new_el_tag(self.class_name, self.MAIN_CONTAINER_TAG_NAME)

    @classmethod
    def __check_subclasses(cls, subclass: type[BaseAppThemeHandler] | type[BaseAppCallbackHandler]) -> None:
        """Проверка на наличие созданного обработчика у класса наследника `BaseAppWindow`"""
        if not any(base_classes is subclass for base_classes in cls.__mro__[1:-1]):
            raise NotImplementClassError(
                msg=f"Класс {cls.__name__} должен наследоваться от {subclass.__name__}!",
                targets=[cls.__name__],
                pre_decision=f"Создайте класс, наследованный от {subclass.__name__}."
            )

    def create_window(self):
        ...

    def create_children_windows(self):
        ...
