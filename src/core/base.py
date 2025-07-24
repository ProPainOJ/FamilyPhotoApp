import time
from pathlib import Path

import dearpygui.dearpygui as dpg
import psutil as ps
from screeninfo import get_monitors, Monitor, ScreenInfoError

from src import WinConstEnum, AppConstEnum

CURRENT_PATH = Path(__file__)


class App:
    """Основной класс, реализовывающий логику инициализации окна приложения и его основных настроек."""

    _instance = None

    WIDTH: int
    HEIGHT: int
    TAG: str = "tag"
    PRIMARY_WINDOW: str | int = None
    TARGET_FPS: int = AppConstEnum.START_FPS.value
    APP_ELEMENT_LABELS: dict[str, int | str] = {}  # `Tag` элемента по его `label`.
    RESIZE_ITEM_CALLBACKS: dict[str, callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(App, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self.__create_viewport()
            self.__configurate_global_themes()
            dpg.set_viewport_resize_callback(self.__run_item_callbacks)
            self._initialized = False

    @staticmethod
    def __configurate_global_themes() -> None:
        """Применение глобальных настроек приложения."""

        # Фон.
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 55))  # Тёмно-синий фон
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 0)
            dpg.bind_theme(global_theme)

        # Шрифт.
        with dpg.font_registry():
            ttf_fonts = CURRENT_PATH.parent.parent / "resources" / "fonts" / "Cornerita.ttf"

            with dpg.font(ttf_fonts.__str__(), size=18, tag="global_font") as dg_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.bind_font(dg_font)

    def __create_viewport(self) -> None:
        monitor_params = self.get_monitor_params(only_prime=True)[0]

        self.WIDTH = int(monitor_params.width - (monitor_params.width * WinConstEnum.X_PADDING.value // 100))
        self.HEIGHT = int(monitor_params.height - (monitor_params.height * WinConstEnum.Y_PADDING.value // 100))

        dpg.create_viewport(
            title=AppConstEnum.NAME.value,
            width=self.WIDTH,
            height=self.HEIGHT,
            x_pos=(monitor_params.width // 2) - (self.WIDTH // 2),
            y_pos=(monitor_params.height // 2) - (self.HEIGHT // 2),
            resizable=True,
            always_on_top=False,
            min_width=WinConstEnum.MIN_WIDTH.value,
            min_height=WinConstEnum.MIN_HEIGHT.value,
        )

    def __run_item_callbacks(self):
        for name, callback in self.RESIZE_ITEM_CALLBACKS.items():
            print(f"INFO >>> Run <{name}> callback")
            callback()
        print("-" * 120)

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

        while dpg.is_dearpygui_running():  # Основной цикл рендеринга
            frame_time = 1.0 / self.TARGET_FPS if self.TARGET_FPS else 0
            start_time = time.perf_counter()
            fps_counter += 1
            current_time = time.perf_counter()
            if current_time - last_fps_update >= 1.0:
                if dpg.does_item_exist("app_fps_tag"):
                    dpg.set_value("app_fps_tag", f"FPS:{fps_counter}")
                    dpg.set_value("cpu_data_tag", f"CPU:{ps.cpu_percent()}%")
                fps_counter = 0
                last_fps_update = current_time

            dpg.render_dearpygui_frame()  # Рендер кадра

            elapsed = time.perf_counter() - start_time  # Ограничение FPS

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
