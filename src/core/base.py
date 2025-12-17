import os
import time
from dataclasses import dataclass
from functools import wraps
from pathlib import Path
from typing import Callable, Optional, Final

import dearpygui.dearpygui as dpg
import psutil as ps
from screeninfo import get_monitors, Monitor, ScreenInfoError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing_extensions import TypeVar

from src import WinConstEnum, AppConstEnum
from src.constants.application import MouseActionCallbackEnum, NotificationLevelEnum, ColorsEnum, RGBA
from src.constants.types import DPGTag, DPGColor
from src.core.modals.modals import Base
from src.utils.data_structure import Stack
from src.utils.dir import join_exist_path

CURRENT_PATH = Path(__file__)
T = TypeVar("T")


@dataclass
class Notification:
    tag: DPGTag
    level: NotificationLevelEnum
    duration: int


class ConfigApp:
    """Общие настройки приложения."""
    TAG: Final[str] = "tag"
    VIEWPORT_WIDTH: int
    VIEWPORT_HEIGHT: int
    MIN_WIDTH: Final[int] = WinConstEnum.MIN_WIDTH.value
    MIN_HEIGHT: Final[int] = WinConstEnum.MIN_HEIGHT.value
    DEBUG_STATUS: bool = AppConstEnum.DEBUG.value
    TARGET_FPS: int = AppConstEnum.START_FPS.value


class ResizeHandler(ConfigApp):
    """Работа с обработчиками изменения размера элементов приложения."""
    RESIZE_ITEM_CALLBACKS: dict[str, callable] = {}

    @classmethod
    def insert_item_resize_callback(cls, callback_name: str, new_callback: callable, force_run: bool = False) -> None:
        """Зарегистрировать новый обратный вызов изменения положения/размера элемента приложения.

        :param callback_name: Имя вызова
        :param new_callback: Функция обработки
        :param force_run: Запуск обратного вызова при создании?
        """
        if callback_name in cls.RESIZE_ITEM_CALLBACKS:
            raise ValueError(f"Callback c именем <{callback_name}> уже существует!")

        cls.RESIZE_ITEM_CALLBACKS[callback_name] = new_callback
        if force_run:
            new_callback()

    @classmethod
    def delete_item_resize_callback(cls, callback_name: str) -> None:
        """Удаление обратного вызова.

        :param callback_name: Имя обратного вызова (Обычно tag элемента).
        """
        if callback_name not in cls.RESIZE_ITEM_CALLBACKS:
            return
        del cls.RESIZE_ITEM_CALLBACKS[callback_name]

    @classmethod
    def run_resize_callback_by_name(cls, name: str, match: bool = False, count_match: int = 1):
        """Форсированный запуск изменения по имени.

        :param name: Имя callback.
        :param match: Простой поиск совпадению по имени обратного вызова.
        :param count_match: Количество совпадений.
        """
        if not match:
            if name not in cls.RESIZE_ITEM_CALLBACKS:
                raise KeyError(f"Callback c именем <{name}> не зарегистрирован!")
            cls.RESIZE_ITEM_CALLBACKS[name]()
            return

        if count_match == 0:
            count_match = 1
        if count_match < 0:
            count_match = len(cls.RESIZE_ITEM_CALLBACKS)

        for callback_name, callback in cls.RESIZE_ITEM_CALLBACKS.items():
            if name in callback_name:
                callback()
                count_match -= 1
            if not count_match:
                return

    @classmethod
    def force_all_resize_callbacks(cls) -> None:
        """Запуск всех обратных вызовов."""
        for name, callback in cls.RESIZE_ITEM_CALLBACKS.items():
            callback()
            if cls.DEBUG_STATUS:
                print(f"INFO >>> Run resize callback <{name}>")
        else:
            if cls.DEBUG_STATUS:
                print("-" * 120)


class MouseHandler(ConfigApp):
    """Работа с обработчиками мыши приложения."""
    MOUSE_CALLBACKS: dict[str, dict[str, callable]] = {action.name: {} for action in MouseActionCallbackEnum}

    @classmethod
    def run_callbacks_by_mouse_type(cls, callback_type: MouseActionCallbackEnum) -> None:
        """Запуск обработчиков мыши по типу действия."""
        for callback_name in cls.MOUSE_CALLBACKS[callback_type.name].copy():
            cls.MOUSE_CALLBACKS[callback_type.name][callback_name]()

    @classmethod
    def _update_handle_mouse_registry(cls) -> None:
        """Обновление регистрации обработчиков в DearPyGui."""
        _mouse_reg_tag = "global_mouse_reg"
        if dpg.does_item_exist(_mouse_reg_tag):
            dpg.delete_item(_mouse_reg_tag)

        with dpg.handler_registry(tag="global_mouse_reg"):
            dpg.add_mouse_move_handler(callback=lambda: cls.run_callbacks_by_mouse_type(MouseActionCallbackEnum.moving))
            dpg.add_mouse_click_handler(
                button=dpg.mvMouseButton_Left,
                callback=lambda: cls.run_callbacks_by_mouse_type(MouseActionCallbackEnum.click),
            )
            dpg.add_mouse_release_handler(
                button=dpg.mvMouseButton_Left,
                callback=lambda: cls.run_callbacks_by_mouse_type(MouseActionCallbackEnum.release),
            )
            dpg.add_mouse_drag_handler(
                button=dpg.mvMouseButton_Left,
                callback=lambda: cls.run_callbacks_by_mouse_type(MouseActionCallbackEnum.drag),
                threshold=1,
            )

    @classmethod
    def insert_mouse_callback(cls, name: str, callback: callable,
                              mouse_action_type: MouseActionCallbackEnum) -> callable:
        """Создание обработчика мыши по типу действия.

        :param name: Имя обработчика (Обычно tag элемента).
        :param callback: Функция обработчика.
        :param mouse_action_type: Тип действия.

        :return: Обработчик
        """
        cls.MOUSE_CALLBACKS[mouse_action_type.name][name] = callback
        cls._update_handle_mouse_registry()
        return callback

    @classmethod
    def delete_mouse_callback(cls, callback_type: MouseActionCallbackEnum, name: str) -> bool:
        """Удаление обработчика мыши.

        :param callback_type: Тип обработчика.
        :param name: Имя обработчика (Обычно tag элемента).

        :return: Состояние удаление.
        """
        if cls.MOUSE_CALLBACKS[callback_type.name].get(name, False):
            del cls.MOUSE_CALLBACKS[callback_type.name][name]
            cls._update_handle_mouse_registry()
            return True
        return False


class AppHandlers(ResizeHandler, MouseHandler):
    pass


class NotificationSystem:
    """Уведомления приложения."""
    WIDTH: Final[int] = 350
    HEIGHT: int = 60
    notification_counter = 0
    active: Notification | None = None
    notifications: dict[NotificationLevelEnum, Stack[Notification]] = {
        lvl: Stack[Notification]()
        for lvl in NotificationLevelEnum
    }

    @staticmethod
    def _get_notify_theme(level_type: NotificationLevelEnum, color: RGBA) -> DPGTag:
        """Применения тем для уведомлений приложения.

        :param level_type: Уровень уведомления
        :param color: Цвет текста уведомления
        """
        notify_theme_color: DPGColor
        with dpg.theme() as notify_theme_tag:
            if level_type == NotificationLevelEnum.ERROR:
                notify_theme_color = ColorsEnum.RED.value.to_tuple()
            elif level_type == NotificationLevelEnum.WARNING:
                notify_theme_color = ColorsEnum.ORANGE.value.to_tuple()
            else:
                notify_theme_color = ColorsEnum.GREY.value.to_tuple()
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_color(
                    dpg.mvThemeCol_WindowBg,
                    value=notify_theme_color,
                    category=dpg.mvThemeCat_Core,
                )
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, 0.5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, color.to_tuple(), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(
                    dpg.mvThemeCol_Button, ColorsEnum.TRANSPARENT.value.to_tuple(), category=dpg.mvThemeCat_Core
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered, ColorsEnum.TRANSPARENT.value.to_tuple(), category=dpg.mvThemeCat_Core
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive, ColorsEnum.TRANSPARENT.value.to_tuple(), category=dpg.mvThemeCat_Core
                )
        return notify_theme_tag

    @classmethod
    def show_notification(cls) -> DPGTag:
        """Показать активное уведомление"""
        dpg.configure_item(cls.active.tag, show=True)
        return cls.active.tag

    @classmethod
    def remove_notification(cls) -> DPGTag:
        """Удаление уведомления."""
        tag, lvl = cls.active.tag, cls.active.level
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, show=False)
            dpg.delete_item(tag)
        cls.notifications[lvl].pop()
        cls.active = None

        return tag

    @classmethod
    def create_notification(cls, message: str, lvl: NotificationLevelEnum = NotificationLevelEnum.DEFAULT,
                            duration: int = 3,
                            text_color: RGBA = ColorsEnum.BLACK.value, action: callable = None) -> str:
        """Отображение уведомления.

        :param message: Текст уведомления.
        :param lvl: Уровень важности уведомления.
        :param duration: Время удаление.
        :param text_color: Цвет уведомления.
        :param action:

        :return: Тег окна уведомления в DearPyGui.
        """
        cls.notification_counter += 1
        notification_tag = f"notification_{cls.notification_counter}_tag"

        with dpg.window(
                tag=notification_tag,
                label=f"Notification №{cls.notification_counter}",
                width=cls.WIDTH,
                height=cls.HEIGHT,
                pos=(dpg.get_viewport_width() - (cls.WIDTH + 1), 25),
                no_title_bar=True,
                no_resize=True,
                no_move=True,
                no_collapse=True,
                no_background=False,
                no_scroll_with_mouse=True,
                no_scrollbar=True,
                horizontal_scrollbar=False,
                show=False,
        ) as notification_tag:
            if action:
                dpg.add_button(pos=(0, 0), label=message, width=cls.WIDTH, height=100, callback=action)
                dpg.add_text("> подробнее...", pos=(0, cls.HEIGHT + int(dpg.get_text_size("> подробнее...")[1])))
            else:
                dpg.add_button(pos=(0, 0), label=message, width=cls.WIDTH, height=100)

        dpg.bind_item_theme(item=notification_tag, theme=cls._get_notify_theme(level_type=lvl, color=text_color))

        cls.notifications[lvl].push(Notification(tag=notification_tag, level=lvl, duration=duration))
        App.insert_item_resize_callback(
            notification_tag,
            lambda: dpg.configure_item(
                item=notification_tag,
                pos=(dpg.get_viewport_width() - (cls.WIDTH + 1), 25)
            )
        )

        return notification_tag


class App(AppHandlers):
    """Основной класс, реализовывающий логику инициализации окна приложения и его основных настроек."""
    _instance: Optional["App"] = None
    PRIMARY_WINDOW: DPGTag = None
    CUSTOM_SIDEBAR_LINE_ACTIVE: bool = True

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(App, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self.session = self.get_db_session()
            self.__create_viewport()
            self.__configurate_global_themes()
            self._update_handle_mouse_registry()
            dpg.set_viewport_resize_callback(self.force_all_resize_callbacks)

            App._initialized = False

    @classmethod
    def manage_modal_transfer_line(cls, func: Callable[..., T]) -> T:
        """Декоратор, регулирующий активность линии расширения боковой панели `sidebar`.
        Применимо при работе с модальными окнами и т.д."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            cls.CUSTOM_SIDEBAR_LINE_ACTIVE = False
            result = func(*args, **kwargs)
            cls.CUSTOM_SIDEBAR_LINE_ACTIVE = True
            return result

        return wrapper

    @staticmethod
    def __configurate_global_themes() -> None:
        """Применение глобальных настроек приложения."""

        # Фон/Style.
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 55))  # Тёмно-синий фон
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 0)
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
            dpg.bind_theme(global_theme)

        # Шрифт.
        with dpg.font_registry():
            ttf_fonts = CURRENT_PATH.parent.parent / "resources" / "fonts" / "Cornerita.ttf"

            with dpg.font(ttf_fonts.__str__(), size=18, tag="global_font") as dg_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.bind_font(dg_font)

    @staticmethod
    def get_db_session() -> Session:
        """Проверка и создания файла `БД`, а также создание объекта сессии.

        :return: Session
        """
        resources_dir = join_exist_path(os.getcwd(), ("src", "resources"))

        if not os.path.exists(os.path.join(resources_dir, AppConstEnum.DB_NAME.value)):
            with open(os.path.join(resources_dir, AppConstEnum.DB_NAME.value), "x"):
                pass
            db_path = join_exist_path(resources_dir, (AppConstEnum.DB_NAME.value,))
            sqlite_engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(sqlite_engine)
        else:
            db_path = join_exist_path(resources_dir, (AppConstEnum.DB_NAME.value,))
            sqlite_engine = create_engine(f"sqlite:///{db_path}")

        return sessionmaker(sqlite_engine)()

    def __create_viewport(self) -> None:
        monitor_params = self.get_monitor_params(only_prime=True)[0]

        self.VIEWPORT_WIDTH = int(monitor_params.width - (monitor_params.width * WinConstEnum.X_PADDING.value // 100))
        self.VIEWPORT_HEIGHT = int(
            monitor_params.height - (monitor_params.height * WinConstEnum.Y_PADDING.value // 100))

        dpg.create_viewport(
            title=AppConstEnum.NAME.value,
            width=self.VIEWPORT_WIDTH,
            height=self.VIEWPORT_HEIGHT,
            x_pos=(monitor_params.width // 2) - (self.VIEWPORT_WIDTH // 2),
            y_pos=(monitor_params.height // 2) - (self.VIEWPORT_HEIGHT // 2),
            resizable=True,
            always_on_top=False,
            min_width=self.MIN_WIDTH,
            min_height=self.MIN_HEIGHT,
        )

    def __control_notifications(self) -> None:
        """Отображение уведомлений из стека задач."""
        if NotificationSystem.active is None:
            last_warning = NotificationSystem.notifications[NotificationLevelEnum.WARNING].peek()
            last_default = NotificationSystem.notifications[NotificationLevelEnum.DEFAULT].peek()
            NotificationSystem.active = last_warning or last_default
            if not NotificationSystem.active:
                return

        if dpg.is_item_hovered(NotificationSystem.active.tag):
            NotificationSystem.active.duration = 2
            return

        NotificationSystem.show_notification()
        NotificationSystem.active.duration -= 1
        if NotificationSystem.active.duration <= 0:
            deleted_notify = NotificationSystem.remove_notification()
            self.delete_item_resize_callback(deleted_notify)

    @staticmethod
    def get_monitor_params(only_prime: bool = False) -> list[Monitor]:
        """Формирование списка мониторов системы.

        :param only_prime: Запрос только основных мониторов
        :return: Список мониторов
        """
        monitors: list[Monitor] = []
        try:
            wet_monitors = get_monitors()
        except ScreenInfoError:
            return [Monitor(x=0, y=0, width=1920, height=1080, name='error_name')]

        for monitor in wet_monitors:
            if only_prime and monitor.is_primary:
                return [monitor]
            else:
                monitors.append(monitor)
        return monitors

    def control_frames(self) -> None:
        last_fps_update = time.perf_counter()
        fps_counter: int = 0

        while dpg.is_dearpygui_running():
            frame_time = 1.0 / self.TARGET_FPS if self.TARGET_FPS else 0
            start_time = time.perf_counter()
            fps_counter += 1
            current_time = time.perf_counter()
            if current_time - last_fps_update >= 1.0:
                dpg.set_value("app_fps_tag", f"FPS:{fps_counter}")
                dpg.set_value("cpu_data_tag", f"CPU:{ps.cpu_percent()}%")
                fps_counter = 0
                last_fps_update = current_time

                self.__control_notifications()

            dpg.render_dearpygui_frame()

            elapsed = time.perf_counter() - start_time

            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)  # Задержка для выравнивания FPS

    def update_app_fps(self, fps_target: int) -> None:
        if fps_target <= 0:
            return
        self.TARGET_FPS = fps_target

    def set_primary_window(self, windows_id: str | int, is_primary: bool = True) -> None:
        """Установка окна приложения основным.

        :param windows_id: Идентификатор окна
        :param is_primary: Состояние окна
        :return: None
        """
        if not dpg.does_item_exist(windows_id):
            raise ValueError(f"У DearPyGui приложения элемента <{windows_id}> не существует!")
        if self.PRIMARY_WINDOW is not None and windows_id == self.PRIMARY_WINDOW:
            return
        dpg.set_primary_window(window=windows_id, value=is_primary)
        self.PRIMARY_WINDOW = windows_id

    @classmethod
    def create_notification(cls, message: str, lvl: NotificationLevelEnum = NotificationLevelEnum.DEFAULT,
                            duration: int = 3, text_color: RGBA = ColorsEnum.BLACK.value,
                            action: callable = None) -> DPGTag:
        """Вызов метода создания/заполнения стека уведомлений приложения.

        :param message: Текст уведомления
        :param lvl: Уровень уведомления
        :param duration: Секунды для исчезновения
        :param text_color: Цвет текста уведомления
        :param action: Обратный вызов нажатия на уведомление (опционально)

        :return: Тег уведомления
        """
        return NotificationSystem.create_notification(message, lvl, duration, text_color, action)
