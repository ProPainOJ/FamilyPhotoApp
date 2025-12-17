import dearpygui.dearpygui as dpg

from src import App
from src.constants.application import NotificationLevelEnum, ColorsEnum
from src.constants.media import MediaTagFields
from src.constants.types import DPGTag
from src.core.modals.modals import MediaTypeEnum
from src.core.services.media_service import MediaService
from src.external.image.media_file import MediaFile
from src.external.image.work_sys_media_file import FileExtensionType, WorkWithSystemMedia
from src.ui import BaseAppWindow, MainAppCallbackHandlerABC
from src.ui.media import GetContentWindow
from src.utils.position import get_element_pos, RectangularImageElement


class NewContentWindowThemesHandler:
    pass


class NewContentWindowResizeCallbacks(MainAppCallbackHandlerABC):
    pass


class NewContentWindowHandler(NewContentWindowResizeCallbacks,
                              NewContentWindowThemesHandler):

    @staticmethod
    def show_file_dialog(file_dialog_tag: DPGTag, _instance: "ContentWindow") -> None:
        App.CUSTOM_SIDEBAR_LINE_ACTIVE = False
        dpg.show_item(file_dialog_tag)

    @staticmethod
    def resize_file_dialog() -> None:
        father_tag = BaseAppWindow.get_el_tag(ContentWindow.__name__, BaseAppWindow.MAIN_CONTAINER_TAG_NAME)
        dialog_tag = BaseAppWindow.get_el_tag(ContentWindow.__name__, ("file", "dialog"))
        dpg.configure_item(
            dialog_tag,
            height=dpg.get_item_height(father_tag),
            width=dpg.get_item_width(father_tag),
        )

    @staticmethod
    def save_media_info() -> None:
        if ContentWindow.MEDIA_FILE is None:
            return
        print(
            MediaService().create_media(
                name=ContentWindow.MEDIA_FILE.name,
                media_type=MediaTypeEnum.PHOTO,
                size_bytes=ContentWindow.MEDIA_FILE.size,
                extension=ContentWindow.MEDIA_FILE.extension,
                data=ContentWindow.MEDIA_FILE.data,
                description=dpg.get_value(BaseAppWindow.get_el_tag("ContentWindow", MediaTagFields.description)),
                location=dpg.get_value(BaseAppWindow.get_el_tag("ContentWindow", MediaTagFields.location)),
            )
        )

    @staticmethod
    def close_clear_alert(alert_win: str, clear: bool) -> None:
        dpg.configure_item(alert_win, show=False)
        if clear:
            NewContentWindowHandler.clear_fields()

    @staticmethod
    def clear_fields():
        for filed_tag in MediaTagFields:
            filed_to_clear = BaseAppWindow.get_el_tag("ContentWindow", filed_tag)
            if filed_tag == MediaTagFields.type:
                dpg.configure_item(filed_to_clear, default_value=MediaTypeEnum.PHOTO)
            else:
                dpg.set_value(filed_to_clear, "")
        ContentWindow.MEDIA_FILE = None

    @staticmethod
    def save_file_dialog(sender, app_data, user_data: "GetContentWindow") -> None:
        App.CUSTOM_SIDEBAR_LINE_ACTIVE = True
        selected_files: dict[str, str] = app_data['selections']

        if not selected_files:
            return

        for file_name, file_path in selected_files.items():
            try:
                ContentWindow.MEDIA_FILE = WorkWithSystemMedia.create_media_file(file_path)
            except FileNotFoundError as e:
                print(e.__str__())

    @staticmethod
    def toggle_selection(sender, app_data, user_data: DPGTag):
        selected_tags_window = BaseAppWindow.get_el_tag(ContentWindow.__name__, ("selected", "tags"))

        label = dpg.get_item_label(sender)

        dpg.configure_item(sender, show=not dpg.is_item_shown(sender))
        dpg.configure_item(user_data, show=not dpg.is_item_shown(user_data))

        if label in ContentWindow.SELECTED_TAGS:
            ContentWindow.SELECTED_TAGS.remove(user_data)
            if not ContentWindow.SELECTED_TAGS:
                dpg.configure_item(selected_tags_window, show=False)
        else:
            ContentWindow.SELECTED_TAGS.append(sender)
            if not dpg.is_item_shown(selected_tags_window):
                dpg.configure_item(selected_tags_window, show=True)
        dpg.set_value(
            "selected_text",
            f"Выбранные: {', '.join(ContentWindow.SELECTED_TAGS) if ContentWindow.SELECTED_TAGS else 'Ничего не добавлено...'}"
        )


class ContentWindow(BaseAppWindow, NewContentWindowHandler):
    MEDIA_FILE: MediaFile = None
    SELECTED_TAGS: list = []
    SELECTED_TAGS_ROW_WIDTH: int = 0

    def __init__(self, main_app: App) -> None:
        super().__init__(main_app, self.__class__.__name__)

        self.main_parent_container = self.get_el_tag(tag_target="MainWindow", tag_name=("container",))

        self._create_clear_alert_window()
        self.create_window()
        self.create_update_media_window()
        self.create_del_media_window()

    def __create_media_fields(self) -> None:
        with dpg.theme() as rounded_btn_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 15)

        with dpg.theme() as opacity_win_theme_tag:
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_color(
                    dpg.mvThemeCol_ChildBg,
                    value=ColorsEnum.TRANSPARENT.value.to_tuple(),
                    category=dpg.mvThemeCat_Core,
                )
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 15, category=dpg.mvThemeCat_Core)

        dpg.add_spacer(height=10)
        dpg.add_text("Тип файла: ")
        dpg.add_combo(
            tag=self.set_new_el_tag(self.class_name, MediaTagFields.type),
            items=(MediaTypeEnum.PHOTO, MediaTypeEnum.VIDIO, MediaTypeEnum.AUDIO),
            default_value=MediaTypeEnum.PHOTO,
        )

        dpg.add_spacer(height=10)
        dpg.add_text("Место действия: ")
        dpg.add_input_text(tag=self.set_new_el_tag(self.class_name, MediaTagFields.location), hint="Москва")

        dpg.add_spacer(height=10)
        dpg.add_text("Описание: ")
        dpg.add_input_text(
            tag=self.set_new_el_tag(self.class_name, MediaTagFields.description),
            hint="Моё просто описание файла.",
            height=100,
            multiline=True,
            always_overwrite=True,
        )

        options = ["Тег"] * 125

        dpg.add_spacer(height=5)
        dpg.add_text("Выбранные теги: Ничего не добавлено...", tag="selected_text")
        dpg.bind_item_theme(
            dpg.add_child_window(
                tag=self.set_new_el_tag(self.class_name, ("selected", "tags")),
                height=80,
                width=int(App.MIN_WIDTH // 1.5),
                border=False,
                horizontal_scrollbar=False,
                show=False,
            ),
            opacity_win_theme_tag
        )

        dpg.add_text("Доступные теги: ")
        dpg.bind_item_theme(
            dpg.add_child_window(
                tag=self.set_new_el_tag(self.class_name, ("non", "selected", "tags")),
                height=80,
                width=int(App.MIN_WIDTH // 1.5),
                border=False,
                horizontal_scrollbar=False,
                show=True,
            ),
            opacity_win_theme_tag
        )

        selectable_row_group, non_selected_row_group = None, None
        current_row_width = 0
        for i, option in enumerate(options):
            option = f"#{option} {i}"
            if selectable_row_group is None or current_row_width > 500:
                non_selected_row_group = dpg.add_group(
                    horizontal=True, parent=self.get_el_tag(self.class_name, ("non", "selected", "tags")))
                selectable_row_group = dpg.add_group(
                    horizontal=True, parent=self.get_el_tag(self.class_name, ("selected", "tags")))
                current_row_width = 0

            button_width = len(option) * 10 + 10

            selectable_btn = dpg.add_button(
                label=option,
                parent=selectable_row_group,
                callback=self.toggle_selection,
                show=False,
            )
            non_selectable_btn = dpg.add_button(
                tag=option,
                label=option,
                parent=non_selected_row_group,
                callback=self.toggle_selection,
                show=True,
                user_data=selectable_btn,
            )
            dpg.configure_item(selectable_btn, user_data=non_selectable_btn)
            dpg.bind_item_theme(
                selectable_btn,
                rounded_btn_theme
            )
            dpg.bind_item_theme(
                non_selectable_btn,
                rounded_btn_theme
            )
            current_row_width += button_width + 10

    def _create_clear_alert_window(self):
        with dpg.window(
                tag=self.set_new_el_tag(self.class_name, ("media", "clear")),
                label="Очистить все поля?",
                show=False,
                no_scrollbar=True,
                no_resize=True,
                no_scroll_with_mouse=True,
                modal=True,
                no_close=True,
                no_title_bar=True,
                height=100,
                width=424,
        ) as alert_win:
            dpg.add_text("Все поля будут очищены!", indent=100)
            dpg.add_spacer()
            dpg.add_text("Продолжить операцию?")
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="OK",
                    width=200,
                    callback=lambda: self.close_clear_alert(alert_win, True),
                )
                dpg.add_button(
                    label="Cancel",
                    width=200,
                    callback=lambda: self.close_clear_alert(alert_win, False),
                )

        with dpg.theme() as item_theme:
            with dpg.theme_component(dpg.mvWindowAppItem):
                dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
                dpg.add_theme_color(dpg.mvThemeCol_Border, [255, 165, 0, 255], category=dpg.mvThemeCat_Core)
        dpg.bind_item_theme(alert_win, item_theme)

    def _create_file_dialog_window(self) -> DPGTag:
        """Создание модального окна для выбора файла."""
        with dpg.file_dialog(
                tag=self.set_new_el_tag(self.class_name, ("file", "dialog")),
                directory_selector=False,
                callback=self.save_file_dialog,
                file_count=0,
                modal=True,
                show=False,
                width=self.app.MIN_WIDTH,
                height=self.app.MIN_HEIGHT,
                min_size=(self.app.MIN_WIDTH, self.app.MIN_HEIGHT),
                user_data=self,
                cancel_callback=lambda: setattr(App, "CUSTOM_SIDEBAR_LINE_ACTIVE", True)

        ) as file_dialog_tag:
            dpg.add_file_extension(".*")
            for extension in FileExtensionType:
                dpg.add_file_extension(f".{extension}")

        self.app.insert_item_resize_callback(callback_name=file_dialog_tag, new_callback=self.resize_file_dialog)
        return file_dialog_tag

    def create_window(self):
        with dpg.child_window(
                tag=self.main_content_tag,
                parent=self.main_parent_container,
                label=self.main_content_tag.rstrip(f"_{self.app.TAG}"),
                show=False,
                border=False,
                horizontal_scrollbar=False,
        ):
            dpg.add_text("Создание нового файла", color=ColorsEnum.GREEN.value.to_tuple(), bullet=True, indent=25)
            dpg.add_separator()
            with dpg.group(indent=25, width=dpg.get_item_width(self.main_parent_container)):
                self.__create_media_fields()

                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Отменить",
                        callback=lambda: (
                            dpg.configure_item(self.main_content_tag, show=False),
                            self.clear_fields(),
                        )
                    )
                    dpg.add_button(
                        label="Очистить",
                        callback=lambda: dpg.configure_item(
                            self.get_el_tag(self.class_name, ("media", "clear")),
                            pos=get_element_pos(
                                RectangularImageElement(
                                    width=dpg.get_item_width(self.get_el_tag(self.class_name, ("media", "clear"))),
                                    height=dpg.get_item_height(self.get_el_tag(self.class_name, ("media", "clear"))),
                                    wrap_width=dpg.get_viewport_width(),
                                    wrap_height=dpg.get_viewport_height()
                                )).to_pos,
                            show=not dpg.is_item_shown(self.get_el_tag(self.class_name, ("media", "clear"))),
                        ),
                    )

                    file_dialog_tag = self._create_file_dialog_window()

                    dpg.add_button(
                        label="Прикрепить файл",
                        callback=lambda: self.show_file_dialog(file_dialog_tag, self),
                    )
                    dpg.add_button(
                        label="Сохранить",
                        callback=lambda: self.app.create_notification(
                            message="Файл не добавлен!",
                            duration=3,
                            lvl=NotificationLevelEnum.DEFAULT,
                        ) if not ContentWindow.MEDIA_FILE else self.save_media_info()
                    )

    def create_del_media_window(self) -> None:
        pass

    def create_update_media_window(self) -> None:
        pass
