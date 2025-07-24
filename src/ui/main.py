import math

import dearpygui.dearpygui as dpg
from dearpygui.dearpygui import get_value

from src import App, WinConstEnum as WCE
from src.ui import MainApp


class MainWindow(MainApp):
    WINDOW_ELEMENTS: set[str] = {
        "footer",
        "upper",
        "sidebar_left",
    }
    FOOTER_HEIGHT: int = None
    UPPER_HEIGHT: int = None
    SIDEBAR_WIDTH = 121
    SIDEBAR_LINE_STATE = {
        "hovered": False,
        "dragging": False,
        "color": (125, 0, 255, 255 // 3),
        "width": SIDEBAR_WIDTH,
        "mouse_start": [],
        "mouse_end": [],
    }

    def __init__(self, main_app: App) -> None:
        """Реализация основных элементов-контейнеров приложения.

        Доступные элементы APP_ELEMENT_LABELS:
            `self.__name__`
            `self.__name__`+`_footer
            `self.__name__`+`_upper`
            `self.__name__`+`_sidebar`
        """
        self.app = main_app
        self.window_name = self.__class__.__name__

        self.FOOTER_HEIGHT: int = 0 if not WCE.SHOW_FOOTER.value else WCE.FOOTER_HEIGHT.value
        self.main_window = self.create_main_window()

        self.app.APP_ELEMENT_LABELS[self.window_name] = self.main_window
        self.app.APP_ELEMENT_LABELS[self.window_name + '_upper'] = self._create_upper()
        self.app.APP_ELEMENT_LABELS[self.window_name + '_footer'] = self._create_footer()

        self._create_sidebar()
        self._create_setting_window()
        self.__create_modal_win()

        self.__bind_main_window_themes()

    @staticmethod
    def __create_modal_win():  # TODO: Не работает, необходимо переделать под модальное окно настроек.
        with dpg.window(
                tag="modal_window_tag",
                label="Delete Files",
                modal=True,
                show=False,
                no_title_bar=True,
        ) as window:
            dpg.add_text("All those beautiful files will be deleted.\nThis operation cannot be undone!")
            dpg.add_separator()
            dpg.add_checkbox(label="Don't ask me next time")
            with dpg.group(horizontal=True):
                dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item(window, show=False))
                dpg.add_button(label="Cancel", width=75, callback=lambda: dpg.configure_item(window, show=False))

    def __bind_main_window_themes(self) -> None:
        """Применение шаблонов для элементов основного окна."""

        with dpg.theme() as main_tag:
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0, category=dpg.mvThemeCat_Core)

            with dpg.theme_component(dpg.mvMenu):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 5, 5, category=dpg.mvThemeCat_Core)

        dpg.bind_item_theme(self.app.APP_ELEMENT_LABELS[self.__class__.__name__], main_tag)

        with dpg.theme() as main_footer_theme_tag:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (125, 0, 255, 255), category=dpg.mvThemeCat_Core)
            with dpg.theme_component(dpg.mvPlatform_Windows):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)

        dpg.bind_item_theme(self.app.APP_ELEMENT_LABELS[self.__class__.__name__ + "_footer"], main_footer_theme_tag)

    def __hide_footer_callback(self) -> None:
        footer = self.app.APP_ELEMENT_LABELS[self.__class__.__name__ + "_footer"]

        self.FOOTER_HEIGHT = WCE.FOOTER_HEIGHT.value if not self.FOOTER_HEIGHT else 0

        dpg.configure_item(footer, show=not dpg.get_item_configuration(footer)["show"])

        [callback() for name, callback in self.app.RESIZE_ITEM_CALLBACKS.items()]

    def __create_transfer_line(self) -> int | str:
        def resize_transfer_line_callback() -> None:
            self.SIDEBAR_LINE_STATE["hovered"] = False
            self.SIDEBAR_LINE_STATE["dragging"] = False
            line_config = dpg.get_item_configuration(line)["p2"]
            dpg.configure_item(item=line, p2=(line_config[0], dpg.get_viewport_height() - self.FOOTER_HEIGHT))

        def is_mouse_near_line(
                mouse_pos: tuple[float | int, ...] | list[float | int, float | int],
                line_p1: tuple[float | int, ...],
                line_p2: tuple[float | int, ...],
                threshold: float | int = 1
        ) -> bool:
            """Рядом ли мышь с линией.

            :param mouse_pos: Позиция мыши по x, y.
            :param line_p1: Точка страта линии.
            :param line_p2: Точка завершения линии.
            :param threshold: Расстояние в px до линии.
            :return: Bool
            """

            x, y = mouse_pos
            x1, y1 = line_p1
            x2, y2 = line_p2

            # Рассчитываем расстояние от точки до линии
            line_length = math.hypot(x2 - x1, y2 - y1)
            if line_length == 0:
                return False

            # Нормализованный проекционный вектор
            vector = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / (line_length ** 2)

            # Ближайшая точка на линии
            if vector < 0:
                closest = (x1, y1)
            elif vector > 1:
                closest = (x2, y2)
            else:
                closest = (x1 + vector * (x2 - x1), y1 + vector * (y2 - y1))

            distance = math.hypot(x - closest[0], y - closest[1])

            return distance <= threshold

        def on_mouse_drag_callback(sender, app_data, user_data) -> None:
            is_near_line_by_dragging = is_mouse_near_line(
                dpg.get_mouse_pos(),
                line_p1=dpg.get_item_configuration(line)["p1"],
                line_p2=dpg.get_item_configuration(line)["p2"],
                threshold=dpg.get_viewport_width() // 2
            )
            if self.SIDEBAR_LINE_STATE["dragging"] and is_near_line_by_dragging:
                mouse_position_by_dragging = dpg.get_mouse_pos()
                line_config = dpg.get_item_configuration(line)
                p1 = (mouse_position_by_dragging[0], line_config["p1"][1])
                p2 = (mouse_position_by_dragging[0], line_config["p2"][1])

                dpg.configure_item(
                    item=line,
                    p1=p1,
                    p2=p2,
                    color=(155, 0, 0, 255),
                    thickness=1,
                )
                self.SIDEBAR_WIDTH = mouse_position_by_dragging[0]
                self.app.RESIZE_ITEM_CALLBACKS[self.app.APP_ELEMENT_LABELS[self.window_name + "_sidebar_left"]]()

        def on_mouse_release_callback(sender, app_data, user_data):
            self.SIDEBAR_LINE_STATE["dragging"] = False
            if self.SIDEBAR_LINE_STATE["hovered"]:
                dpg.configure_item(
                    item=line,
                    color=(155, 0, 255, 255),
                )
                self.SIDEBAR_LINE_STATE["hovered"] = False
            else:
                dpg.configure_item(
                    item=line,
                    show=False,
                )

        def on_mouse_click_callback(sender, app_data, user_data):
            if self.SIDEBAR_LINE_STATE["hovered"]:
                self.SIDEBAR_LINE_STATE["dragging"] = True

                self.SIDEBAR_LINE_STATE["mouse_start"] = dpg.get_mouse_pos()

                dpg.configure_item(
                    item=line,
                    color=(255, 0, 0, 255),
                )

        def on_mouse_move_callback(sender, app_data, user_data):
            sidebar = self.app.APP_ELEMENT_LABELS[self.window_name + "_sidebar_left"]
            if dpg.get_item_configuration(sidebar)["show"]:
                if is_mouse_near_line(
                        app_data,
                        dpg.get_item_configuration(line)["p1"],
                        dpg.get_item_configuration(line)["p2"],
                        3,
                ):
                    self.SIDEBAR_LINE_STATE["hovered"] = True
                    dpg.configure_item(
                        item=line,
                        show=True,
                    )
                else:
                    dpg.configure_item(
                        item=line,
                        show=False,
                    )

        # Creating viewport drawlists.
        with dpg.viewport_drawlist() as viewport_drawlist:
            line_position = (
                (self.SIDEBAR_WIDTH, self.UPPER_HEIGHT),
                (self.SIDEBAR_WIDTH, dpg.get_viewport_height() - self.FOOTER_HEIGHT),
            )
            line = dpg.draw_line(
                tag="line",
                p1=line_position[0],
                p2=line_position[1],
                color=self.SIDEBAR_LINE_STATE["color"],
                thickness=3,
            )

        with dpg.handler_registry():
            dpg.add_mouse_move_handler(callback=on_mouse_move_callback)
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=on_mouse_click_callback)
            dpg.add_mouse_release_handler(button=dpg.mvMouseButton_Left, callback=on_mouse_release_callback)
            dpg.add_mouse_drag_handler(button=dpg.mvMouseButton_Left, callback=on_mouse_drag_callback)

        self.app.RESIZE_ITEM_CALLBACKS[line] = resize_transfer_line_callback

        return line

    def _create_setting_window(self) -> None:
        """Реализация окна с настройками приложения."""
        with dpg.window(
                tag="setting_tag",
                label="Setting",
                pos=(dpg.get_viewport_width() // 4, dpg.get_viewport_height() // 3),
                no_scrollbar=True,
                no_collapse=True,
                no_move=True,
                show=False,
                no_resize=True,
                autosize=False,
                min_size=(400, 200)
        ):
            dpg.add_text(tag="setting_FPS_tag", label="FPS", default_value="FPS: ---")
            dpg.add_button(
                label="Обновить значение fps",
                repeat=True,
                callback=lambda: dpg.set_value("setting_FPS_tag", value=f"FPS: {dpg.get_frame_rate()}")
            )
            dpg.add_slider_int(
                tag="slider_fps_tag",
                label="Значение FPS приложения",
                default_value=self.app.TARGET_FPS,
                min_value=30,
                max_value=144,
                no_input=True,
            )
            dpg.add_button(
                label="Изменить FPS",
                callback=lambda: self.app.update_app_fps(get_value("slider_fps_tag")),
            )

    def _create_upper(self) -> str | int:
        """Создание верхнего меню приложения."""
        _upper_name: str = "upper"
        with dpg.menu_bar(
                tag="_".join((self.window_name, _upper_name, self.app.TAG)),
                label=_upper_name,
                parent=self.main_window,
        ) as upper_menu:
            with dpg.menu(label="Меню"):
                dpg.add_menu_item(
                    label="Боковая панель",
                    callback=lambda: dpg.configure_item(
                        self.app.APP_ELEMENT_LABELS[self.window_name + "_sidebar_left"],
                        show=not dpg.get_item_configuration(
                            self.app.APP_ELEMENT_LABELS[self.window_name + "_sidebar_left"]
                        )["show"],
                    )
                )
                dpg.add_menu_item(
                    label="Modal",
                    callback=lambda: dpg.configure_item("modal_window_tag", show=True)
                )

            with dpg.menu(label="Настройки"):
                dpg.add_menu_item(
                    label="hide footer",
                    callback=self.__hide_footer_callback,
                )
                dpg.add_menu_item(
                    label="FPS",
                    callback=lambda: dpg.configure_item("setting_tag", show=True)
                )
                with dpg.menu(label="Debug Settings"):
                    dpg.add_menu_item(
                        label="Fons",
                        callback=dpg.show_font_manager,
                    )
                    dpg.add_menu_item(
                        label="Styles",
                        callback=dpg.show_style_editor
                    )
                    dpg.add_menu_item(
                        label="Metrix",
                        callback=dpg.show_metrics
                    )
                    dpg.add_menu_item(
                        label="Items",
                        callback=dpg.show_item_registry
                    )
                    dpg.add_menu_item(
                        label="Debug",
                        callback=dpg.show_debug
                    )

        self.UPPER_HEIGHT = dpg.get_item_height(upper_menu)

        return upper_menu

    def _create_footer(self) -> str | int:
        """Создание нижнего меню состояния приложения."""
        _footer_name: str = self.window_name + "_footer"

        def resize_footer_callback() -> None:
            dpg.configure_item(main_footer_tag, width=dpg.get_viewport_width())
            dpg.set_item_pos(main_footer_tag, [0, dpg.get_viewport_height() - self.FOOTER_HEIGHT])

        with dpg.child_window(
                tag="_".join((_footer_name, self.app.TAG)),
                label=_footer_name,
                height=self.FOOTER_HEIGHT,
                width=dpg.get_viewport_width(),
                pos=(0, dpg.get_viewport_height() - self.FOOTER_HEIGHT),
                parent=self.app.APP_ELEMENT_LABELS[self.__class__.__name__],
                autosize_x=True,
                autosize_y=True,
                show=WCE.SHOW_FOOTER.value,
        ) as main_footer_tag:
            with dpg.group(
                    tag="footer_group_tag",
                    height=self.FOOTER_HEIGHT,
                    horizontal=True,
                    parent=main_footer_tag,
            ) as footer_group:
                with dpg.theme() as main_footer_group_theme_tag:
                    with dpg.theme_component(dpg.mvGroup):
                        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, y=0, x=0, category=dpg.mvThemeCat_Core)
                        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, y=0, x=0, category=dpg.mvThemeCat_Core)
                    dpg.bind_item_theme(footer_group, main_footer_group_theme_tag)
                dpg.add_separator()
                dpg.add_text(tag="app_fps_tag", default_value="FPS:---")
                dpg.add_text(tag="cpu_data_tag", default_value="CPU:---")

        self.app.APP_ELEMENT_LABELS[_footer_name] = main_footer_tag
        self.app.RESIZE_ITEM_CALLBACKS[main_footer_tag] = resize_footer_callback

        return main_footer_tag

    def _create_sidebar(self) -> str | int:
        """Создание бокового окна приложения."""

        _side_bar_name = self.window_name + "_sidebar_left"

        def move_sidebar_callback(sender, app_data, user_data):
            window_tag, new_width, new_height = user_data
            if dpg.get_item_pos(window_tag)[0] + self.SIDEBAR_WIDTH + new_width >= dpg.get_viewport_width():
                dpg.configure_item(window_tag, pos=(0, 0))
            else:
                dpg.configure_item(window_tag, pos=(
                    dpg.get_item_pos(window_tag)[0] + new_width, new_height + self.UPPER_HEIGHT))

        def resize_sidebar_callback() -> None:
            dpg.configure_item(
                sidebar_tag,
                width=self.SIDEBAR_WIDTH,
                height=dpg.get_viewport_height() - (self.FOOTER_HEIGHT + self.UPPER_HEIGHT),
            )
            self.SIDEBAR_LINE_STATE["hovered"] = False

        with dpg.child_window(
                tag="_".join((_side_bar_name, self.app.TAG)),
                label=_side_bar_name,
                parent=self.main_window,
                pos=(0, self.UPPER_HEIGHT),
                width=self.SIDEBAR_WIDTH,
                height=dpg.get_viewport_height() - (self.FOOTER_HEIGHT + self.UPPER_HEIGHT),
                border=False,
        ) as sidebar_tag:
            with dpg.group(horizontal=False):
                dpg.add_text(default_value="Боковое окно!")
                with dpg.collapsing_header(label="Настройки"):
                    dpg.add_checkbox(label="Опция 1")
                    dpg.add_checkbox(label="Опция 2")
                    dpg.add_button(
                        label=f"Сдвиг {_side_bar_name}",
                        callback=move_sidebar_callback,
                        user_data=(sidebar_tag, 20, 5),
                    )

        self.app.APP_ELEMENT_LABELS[_side_bar_name] = sidebar_tag
        self.app.RESIZE_ITEM_CALLBACKS[sidebar_tag] = resize_sidebar_callback

        self.__create_transfer_line()

        return sidebar_tag

    def create_main_window(self) -> str | int:
        with dpg.window(
                tag="main_tag",
                label="main",
                menubar=True,
                no_move=True,
                no_resize=True,
                no_collapse=True,
                no_title_bar=True,
                no_scroll_with_mouse=True,
                no_scrollbar=True,
                horizontal_scrollbar=False,
        ) as main_window:
            self.app.set_primary_window(main_window)

            return main_window

    def crate_main_template(self):
        pass
