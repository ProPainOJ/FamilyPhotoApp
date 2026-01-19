import math
from typing import Optional, TypeVar

import dearpygui.dearpygui as dpg
from dearpygui.dearpygui import get_value

from src import App
from src import WinConstEnum as WCE
from src.constants.types import DPGTag
from src.core.base import MouseActionCallbackEnum
from src.core.modals.modals import Media
from src.core.repositories.media_repository import MediaRepository
from src.core.services.media_service import MediaService
from src.ui import BaseAppWindow, MainAppCallbackHandler
from src.ui.media import GetContentWindow

POSITION = TypeVar('POSITION', int, float)
ElementName = TypeVar('ElementName', str, int)

Point = tuple[POSITION, POSITION]


class MainWindowThemesHandler:
    @staticmethod
    def theme_delete_media_pop() -> DPGTag:
        pass


class MainWindowEventHandler(MainAppCallbackHandler):
    _instance: "MainWindow"

    @staticmethod
    def set_deleted_media(sender, app_data, user_data: DPGTag):
        """Сокрытие медиа-файла"""
        media: Media = dpg.get_item_user_data(user_data)
        MediaRepository().set_deleted(media.id)
        dpg.delete_item(user_data)
        popup = dpg.get_item_parent(sender)
        dpg.delete_item(popup)
        MainWindowEventHandler._instance.update_media_tree()

    @staticmethod
    def set_new_media_callback(sender, app_data, user_data) -> None:
        """Отображение медиа в форме контента"""
        main_content_container = BaseAppWindow.get_el_tag(
            GetContentWindow.__name__,
            BaseAppWindow.MAIN_CONTAINER_TAG_NAME,
        )
        show_status_cont_media: bool = dpg.is_item_shown(main_content_container)
        user_data: Media = dpg.get_item_user_data(sender)

        if GetContentWindow.CURRENT_MEDIA == user_data:
            show_status_cont_media = not show_status_cont_media
        else:
            GetContentWindow.set_new_image(new_media=user_data)
            show_status_cont_media = True

        texture_resize_name = BaseAppWindow.get_el_tag(GetContentWindow.__name__, ("texture", "registry"))
        MainWindowEventHandler._instance.app.run_resize_callback_by_name(texture_resize_name)

        dpg.configure_item(
            main_content_container,
            show=show_status_cont_media,
        )

    @classmethod
    def on_mouse_move_callback(cls, _instance: "MainWindow") -> None:
        if dpg.is_item_shown(_instance.sidebar_left_tag):
            active_window = dpg.get_active_window()

            if 0 <= active_window <= 10 or _instance.new_line.dragging:
                return

            try:
                item_type = dpg.get_item_type(active_window)
            except SystemError:
                return

            if App.CUSTOM_SIDEBAR_LINE_ACTIVE and "mvMenu" not in item_type and InnerLineSeparation.is_mouse_near_line(
                    mouse_pos=dpg.get_mouse_pos(local=False),
                    line_p1=_instance.new_line.point1,
                    line_p2=_instance.new_line.point2,
                    threshold=_instance.new_line.thickness,
            ):
                _instance.new_line.hovered = True
                _instance.new_line.configurate_line({"show": True})
            else:
                _instance.new_line.hovered = False
                _instance.new_line.configurate_line({"show": False})

    @classmethod
    def on_mouse_click_callback(cls, _instance: "MainWindow"):
        if _instance.new_line.hovered:
            _instance.new_line.dragging = True
            _instance.new_line.thickness *= 2
            _instance.new_line.configurate_line({"thickness": _instance.new_line.thickness})

    @classmethod
    def on_mouse_release_callback(cls, _instance: "MainWindow"):
        if _instance.new_line.dragging:
            _instance.new_line.dragging = False

            _instance.new_line.hovered = InnerLineSeparation.is_mouse_near_line(
                mouse_pos=dpg.get_mouse_pos(local=False),
                line_p1=_instance.new_line.point1,
                line_p2=_instance.new_line.point2,
                threshold=_instance.new_line.thickness,
            )

            if _instance.new_line.hovered:
                _instance.new_line.configurate_line({"show": True})
            else:
                _instance.new_line.configurate_line({"show": False})

            _instance.new_line.thickness /= 2
            _instance.new_line.configurate_line(
                {
                    "color": _instance.new_line.color,
                    "thickness": _instance.new_line.thickness,
                }
            )

    @classmethod
    def on_mouse_drag_callback(cls, _instance: "MainWindow") -> None:
        mouse_x_position_by_dragging = dpg.get_mouse_pos(local=False)[0]
        if _instance.new_line.dragging:
            accept_max_sidebar_width = dpg.get_viewport_width() // 5
            if mouse_x_position_by_dragging < WCE.SIDE_BAR_WIDTH.value:
                mouse_x_position_by_dragging = WCE.SIDE_BAR_WIDTH.value
                p1 = (mouse_x_position_by_dragging, _instance.new_line.point1[1])
                p2 = (mouse_x_position_by_dragging, _instance.new_line.point2[1])
            elif mouse_x_position_by_dragging >= accept_max_sidebar_width:
                mouse_x_position_by_dragging = accept_max_sidebar_width

                p1 = (mouse_x_position_by_dragging, _instance.new_line.point1[1])
                p2 = (mouse_x_position_by_dragging, _instance.new_line.point2[1])
            else:
                p1 = (mouse_x_position_by_dragging, _instance.new_line.point1[1])
                p2 = (mouse_x_position_by_dragging, _instance.new_line.point2[1])

            line_color = _instance.new_line.color
            dragging_color = (*line_color[:-1], min(255, int(line_color[-1] * 1.25)))

            _instance.new_line.configurate_line({"p1": p1, "p2": p2, "color": dragging_color})
            _instance.new_line.point1 = p1
            _instance.new_line.point2 = p2

            _instance.SIDEBAR_WIDTH = mouse_x_position_by_dragging
            _instance.app.run_resize_callback_by_name(name="sidebar", match=True)
            _instance.app.run_resize_callback_by_name(name=_instance.container, match=False)
        else:
            _instance.new_line.dragging = False

    @classmethod
    def resize_transfer_line_callback(cls, _instance: "MainWindow") -> None:
        _instance.new_line.hovered = _instance.new_line.dragging = False
        p2 = (_instance.new_line.point2[0], dpg.get_viewport_height() - _instance.FOOTER_HEIGHT - 1)
        _instance.new_line.point2 = p2
        _instance.new_line.configurate_line({"p2": p2})

    @classmethod
    def resize_footer_callback(cls, _instance: "MainWindow") -> None:
        dpg.configure_item(_instance.footer_tag, width=dpg.get_viewport_width())
        dpg.set_item_pos(_instance.footer_tag, [0, dpg.get_viewport_height() - _instance.FOOTER_HEIGHT])

    @classmethod
    def resize_sidebar_callback(cls, _instance: "MainWindow") -> None:
        dpg.configure_item(
            _instance.sidebar_left_tag,
            width=_instance.SIDEBAR_WIDTH,
            height=dpg.get_viewport_height() - (_instance.FOOTER_HEIGHT + _instance.UPPER_HEIGHT),
        )

    @classmethod
    def resize_container_callback(cls, _instance: "MainWindow") -> None:
        dpg.configure_item(
            _instance.container,
            pos=(_instance.SIDEBAR_WIDTH, _instance.UPPER_HEIGHT),
            height=dpg.get_viewport_height() - (_instance.FOOTER_HEIGHT + _instance.UPPER_HEIGHT),
        )

    @classmethod
    def hide_footer_callback(cls, _instance: "MainWindow") -> None:
        _instance.FOOTER_HEIGHT = WCE.FOOTER_HEIGHT.value if not _instance.FOOTER_HEIGHT else 0

        dpg.configure_item(
            _instance.footer_tag,
            show=not dpg.get_item_configuration(_instance.footer_tag)["show"],
        )

        _instance.app.force_all_resize_callbacks()

    @classmethod
    def hide_sidebar_callback(cls, _instance: "MainWindow") -> None:
        _instance.SIDEBAR_WIDTH = WCE.SIDE_BAR_WIDTH.value if not _instance.SIDEBAR_WIDTH else 0

        p1 = (_instance.SIDEBAR_WIDTH, _instance.new_line.point1[1])
        p2 = (_instance.SIDEBAR_WIDTH, _instance.new_line.point2[1])
        _instance.new_line.configurate_line({"p1": p1, "p2": p2})
        _instance.new_line.point1 = p1
        _instance.new_line.point2 = p2

        dpg.configure_item(
            _instance.sidebar_left_tag,
            show=not dpg.get_item_configuration(_instance.sidebar_left_tag)["show"],
        )

        _instance.app.force_all_resize_callbacks()


class InnerLineSeparation:
    def __init__(
            self,
            label: str,
            point1: Point,
            point2: Point,
            color: tuple[float | int, ...] = None,
            thickness: float | int = 1,
            parent: Optional[ElementName] = None,
            extra_configuration: Optional[dict] = None,
    ) -> None:

        self.hovered: bool = False
        self.dragging: bool = False

        self.color = color
        self.parent: Optional[ElementName] = parent
        self.extra_configuration: Optional[dict] = extra_configuration

        self.label = label
        self.tag = self.label + "_tag"
        self.point1 = point1
        self.point2 = point2
        self.thickness = thickness

    def __repr__(self) -> str:
        return (
            f"Line - <{self.tag}> "
            f"<Points: <{self.point1}-{self.point2}> "
            f"Length: {self.count_line_length(self.point1, self.point2)}>"
        )

    @staticmethod
    def count_line_length(point1: Point, point2: Point) -> float:
        return math.hypot(point2[0] - point1[0], point2[1] - point1[1])

    @staticmethod
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

    def configurate_line(self, configuration: dict) -> None:
        dpg.configure_item(item=self.tag, **configuration)

    def draw_line(self) -> ElementName:
        dpg.draw_line(
            tag=self.label + "_tag",
            label=self.label,
            p1=self.point1,
            p2=self.point2,
            thickness=self.thickness,
        )

        if self.parent:
            self.configurate_line({"parent": self.parent})
        if self.color:
            self.configurate_line({"color": self.color})
        if self.extra_configuration:
            self.configurate_line(self.extra_configuration)

        return self.tag


class MainWindow(BaseAppWindow, MainWindowEventHandler, MainWindowThemesHandler):
    FOOTER_HEIGHT: int = 0 if not WCE.SHOW_FOOTER.value else WCE.FOOTER_HEIGHT.value
    UPPER_HEIGHT: int = None

    def __init__(self, main_app: App) -> None:
        """Реализация основных элементов-контейнеров приложения."""
        super().__init__(main_app, self.__class__.__name__)

        self.WINDOW_NAME = self.__class__.__name__
        self.footer_tag = self.set_new_el_tag(self.class_name, "footer")
        self.upper_tag = self.set_new_el_tag(self.class_name, "upper")
        self.sidebar_left_tag = self.set_new_el_tag(self.class_name, "sidebar_left")
        self.line_tag = self.set_new_el_tag(self.class_name, "line")
        self.container = self.set_new_el_tag(self.class_name, "container")

        self.create_window()
        self.create_upper()
        self.create_footer()
        self.create_sidebar()
        self.create_main_container()

        self._create_setting_window()
        self._create_modal_win()

        self.__bind_main_window_themes()
        MainWindowEventHandler._instance = self

    @staticmethod
    def _create_modal_win():
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

        dpg.bind_item_theme(self.main_content_tag, main_tag)

        with dpg.theme() as main_footer_theme_tag:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (125, 0, 255, 255), category=dpg.mvThemeCat_Core)
            with dpg.theme_component(dpg.mvPlatform_Windows):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 0)

        dpg.bind_item_theme(self.footer_tag, main_footer_theme_tag)

        with dpg.theme() as main_container_theme_tag:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (125, 0, 12, 135), category=dpg.mvThemeCat_Core)

        dpg.bind_item_theme(self.container, main_container_theme_tag)

    def _create_transfer_line(self) -> Optional[ElementName]:
        with dpg.viewport_drawlist() as viewport_drawlist:
            start_line_position: tuple[Point, Point] = (
                (self.SIDEBAR_WIDTH, self.UPPER_HEIGHT + 2),
                (self.SIDEBAR_WIDTH, dpg.get_viewport_height() - self.FOOTER_HEIGHT - 1),
            )
            self.new_line = InnerLineSeparation(
                label=self.line_tag.strip("_" + self.app.TAG),
                point1=start_line_position[0],
                point2=start_line_position[1],
                parent=viewport_drawlist,
                thickness=2,
                color=(255, 255, 255, 255 / 2),
            )
            self.line_tag = self.new_line.draw_line()

        self.app.insert_mouse_callback(
            name=self.line_tag + "moving",
            callback=lambda: self.on_mouse_move_callback(self),
            mouse_action_type=MouseActionCallbackEnum.moving,
        )
        self.app.insert_mouse_callback(
            name=self.line_tag + "click",
            callback=lambda: self.on_mouse_click_callback(self),
            mouse_action_type=MouseActionCallbackEnum.click,
        )
        self.app.insert_mouse_callback(
            name=self.line_tag + "release",
            callback=lambda: self.on_mouse_release_callback(self),
            mouse_action_type=MouseActionCallbackEnum.release,
        )
        self.app.insert_mouse_callback(
            name=self.line_tag + "drag",
            callback=lambda: self.on_mouse_drag_callback(self),
            mouse_action_type=MouseActionCallbackEnum.drag,
        )

        self.app.insert_item_resize_callback(self.line_tag, lambda: self.resize_transfer_line_callback(self))

        return

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
                max_value=60,
                no_input=True,
            )
            dpg.add_button(
                label="Изменить FPS",
                callback=lambda: self.app.update_app_fps(get_value("slider_fps_tag")),
            )

    def _resize_left_line_callback(self):
        self.resize_sidebar_callback(self)
        name = self.get_el_tag(tag_target="GetContentWindow", tag_name=("texture", "registry"))
        self.app.run_resize_callback_by_name(name)

    def create_upper(self) -> str | int:
        """Создание верхнего меню приложения."""
        _upper_name: str = "upper"
        with dpg.menu_bar(
                tag="_".join((self.WINDOW_NAME, _upper_name, self.app.TAG)),
                label=_upper_name,
                parent=self.main_content_tag,
        ) as upper_menu:
            with dpg.menu(label="Меню"):
                dpg.add_menu_item(
                    label="Панель метрик",
                    callback=lambda: self.hide_footer_callback(self),
                )
                dpg.add_menu_item(
                    label="Боковая панель",
                    callback=lambda: self.hide_sidebar_callback(self),
                )
                dpg.add_menu_item(
                    label="Показать фото",
                    callback=lambda: dpg.configure_item(
                        item=self.get_el_tag(GetContentWindow.__name__, GetContentWindow.MAIN_CONTAINER_TAG_NAME),
                        show=not dpg.get_item_configuration(
                            self.get_el_tag(GetContentWindow.__name__, GetContentWindow.MAIN_CONTAINER_TAG_NAME),
                        )["show"],
                    )
                )
                dpg.add_menu_item(
                    label="Загрузить файл",
                    callback=lambda: dpg.configure_item(
                        item=self.get_el_tag("ContentWindow", self.MAIN_CONTAINER_TAG_NAME),
                        show=not dpg.is_item_shown(self.get_el_tag("ContentWindow", self.MAIN_CONTAINER_TAG_NAME))
                    )
                )

            with dpg.menu(label="Настройки"):
                dpg.add_menu_item(
                    label="FPS",
                    callback=lambda: dpg.configure_item("setting_tag", show=True)
                )
                if self.app.DEBUG_STATUS:
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

    def create_footer(self) -> ElementName:
        """Создание нижнего меню состояния приложения."""

        with dpg.child_window(
                tag=self.footer_tag,
                label=self.footer_tag.rstrip("_" + self.app.TAG),
                height=self.FOOTER_HEIGHT,
                width=dpg.get_viewport_width(),
                pos=(0, dpg.get_viewport_height() - self.FOOTER_HEIGHT),
                parent=self.main_content_tag,
                autosize_x=True,
                autosize_y=True,
                show=WCE.SHOW_FOOTER.value,
        ):
            with dpg.group(
                    tag="footer_group_tag",
                    height=self.FOOTER_HEIGHT,
                    horizontal=True,
                    parent=self.footer_tag,
            ) as footer_group:
                with dpg.theme() as main_footer_group_theme_tag:
                    with dpg.theme_component(dpg.mvGroup):
                        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, y=0, x=0, category=dpg.mvThemeCat_Core)
                        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, y=0, x=0, category=dpg.mvThemeCat_Core)
                    dpg.bind_item_theme(footer_group, main_footer_group_theme_tag)
                dpg.add_separator()
                dpg.add_text(tag="app_fps_tag", default_value="FPS:---")
                dpg.add_text(tag="cpu_data_tag", default_value="CPU:---")

        self.app.insert_item_resize_callback(self.footer_tag, lambda: self.resize_footer_callback(self))

        return self.footer_tag

    @classmethod
    def update_media_tree(cls):
        """Обновление контента в боковой панели"""
        sidebar_tree_tag = BaseAppWindow.get_el_tag(cls.__name__, "sidebar_left_tree")
        all_medias = MediaService().get_active_media_files()
        children: dict[int, list[int]] = dpg.get_item_children(sidebar_tree_tag)[1]
        if children:
            for child in children:
                dpg.delete_item(child)

        with dpg.group(horizontal=False, parent=sidebar_tree_tag):
            for button_index, media in enumerate(all_medias):
                btn_tag = dpg.add_button(
                    label=media.name,
                    callback=cls.set_new_media_callback,
                    pos=(2, 26 * button_index),
                    user_data=media,
                )
                with dpg.tooltip(parent=btn_tag, delay=.3, hide_on_activity=True):
                    dpg.add_text("Нажмите `ПКМ` для опций")
                with dpg.popup(
                        parent=btn_tag,
                        tag=f"modal_{btn_tag}",
                        mousebutton=dpg.mvMouseButton_Right,
                        modal=False,
                        no_move=True,
                ) as popup:
                    dpg.add_button(
                        label=f"Удалить {dpg.get_item_label(btn_tag)}",
                        callback=cls.set_deleted_media,
                        user_data=btn_tag,
                        small=False,
                    )
                    dpg.configure_item(popup, min_size=[120, 25])

    def _create_side_bar_media_tree(self) -> None:
        """Создание окна с отображением дерева медиа-контента"""
        with dpg.child_window(
                tag=self.set_new_el_tag(self.class_name, "sidebar_left_tree"),
                parent=self.sidebar_left_tag,
                border=False,
                show=True
        ):
            self.update_media_tree()

    def create_sidebar(self) -> None:
        """Создание бокового окна приложения"""
        with dpg.child_window(
                tag=self.sidebar_left_tag,
                label=self.sidebar_left_tag.rstrip("_" + self.app.TAG),
                parent=self.main_content_tag,
                pos=(0, self.UPPER_HEIGHT),
                width=self.SIDEBAR_WIDTH,
                height=dpg.get_viewport_height() - (self.FOOTER_HEIGHT + self.UPPER_HEIGHT),
                border=False,
        ):
            self._create_side_bar_media_tree()
        self.app.insert_item_resize_callback(self.sidebar_left_tag, lambda: self._resize_left_line_callback())
        self._create_transfer_line()

    def create_main_container(self) -> None:
        """Создание контейнера контента приложения."""

        with dpg.child_window(
                tag=self.container,
                label=self.container.rstrip("_tag"),
                parent=self.main_content_tag,
                border=False,
                menubar=False,
                no_scrollbar=True,
                no_scroll_with_mouse=True,
                horizontal_scrollbar=False,
                pos=(self.SIDEBAR_WIDTH, self.UPPER_HEIGHT),
                height=dpg.get_viewport_height() - (self.FOOTER_HEIGHT + self.UPPER_HEIGHT),
        ):
            pass
        self.app.insert_item_resize_callback(self.container, lambda: self.resize_container_callback(self))

    def create_window(self) -> ElementName:
        """Создание основного окна приложения"""
        with dpg.window(
                tag=self.main_content_tag,
                label="main",
                menubar=True,
                no_move=True,
                no_resize=True,
                no_collapse=True,
                no_title_bar=True,
                no_scroll_with_mouse=True,
                no_scrollbar=True,
                horizontal_scrollbar=False,
                no_background=True,
                no_close=True
        ) as main_window:
            self.app.set_primary_window(main_window)

            return main_window
