from typing import Final
from uuid import uuid4, UUID

import dearpygui.dearpygui as dpg

from src import App
from src.constants.application import NotificationLevelEnum, ColorsEnum
from src.constants.media import MediaTagFields
from src.constants.types import DPGTag
from src.core.exceptions.application_exception import FileSuffixError
from src.core.modals.modals import MediaTypeEnum, Tag
from src.core.services.media_service import MediaService
from src.core.services.tag_service import TagService
from src.external.image.media_file import MediaFile
from src.external.image.work_sys_media_file import FileExtensionType, WorkWithSystemMedia
from src.ui import BaseAppWindow, BaseAppCallbackHandler, BaseAppThemeHandler
from src.ui.main import MainWindow
from src.ui.media import GetContentWindow
from src.ui.person import PersonContent
from src.utils.position import get_element_pos, RectangularImageElement


class ContentWindowThemesHandler(BaseAppThemeHandler):
    @staticmethod
    def theme_rounded_btn() -> None:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 15)

    @staticmethod
    def theme_error_input_text() -> None:
        with dpg.theme_component(dpg.mvInputText):
            dpg.add_theme_color(dpg.mvThemeCol_Text, ColorsEnum.RED.value.to_tuple())

    @staticmethod
    def theme_opacity_win() -> None:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_color(
                dpg.mvThemeCol_ChildBg,
                value=ColorsEnum.TRANSPARENT.value.to_tuple(),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 15, category=dpg.mvThemeCat_Core)

    @staticmethod
    def theme_clear_field_alert() -> None:
        with dpg.theme_component(dpg.mvWindowAppItem):
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
            dpg.add_theme_color(dpg.mvThemeCol_Border, [255, 165, 0, 255], category=dpg.mvThemeCat_Core)


class ContentWindowEventHandler(BaseAppCallbackHandler):
    """Обработка обратных вызовов"""
    _instance: "ContentWindow"

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
        """Сохранение нового медиа-объекта"""
        user_tags: dict[UUID, Tag] = {tag.id: tag for tag in ContentWindow.user_tags}
        all_tags: dict[UUID, Tag] = {tag.id: tag for tag in ContentWindow.all_accepted_tags}
        media_service = MediaService()

        new_media = {
            "name": ContentWindow.media_file.name,
            "media_type": dpg.get_value(BaseAppWindow.get_el_tag("ContentWindow", MediaTagFields.type)),
            "size_bytes": ContentWindow.media_file.size,
            "extension": ContentWindow.media_file.extension,
            "data": ContentWindow.media_file.data,
            "description": dpg.get_value(BaseAppWindow.get_el_tag("ContentWindow", MediaTagFields.description)),
            "location": dpg.get_value(BaseAppWindow.get_el_tag("ContentWindow", MediaTagFields.location)),
        }

        if ContentWindow.selected_tags:
            tags: list[Tag] = []
            for tag_uuid in ContentWindow.selected_tags:
                if tag_uuid in user_tags:
                    new_tag = TagService().create_new_tag(id=tag_uuid, name=user_tags[tag_uuid].name)
                    tags.append(new_tag)
                else:
                    tags.append(all_tags[tag_uuid])
            media_obj = media_service.create_media(**new_media)
            media_service.create_media_with_tags(media_obj, tags)
        else:
            media_service.create_media(**new_media)

    @staticmethod
    def close_clear_alert(alert_win: str, clear: bool) -> None:
        dpg.configure_item(alert_win, show=False)
        if clear:
            ContentWindowEventHandler.clear_input_fields()

    @staticmethod
    def save_file_dialog(sender, app_data, user_data: "GetContentWindow") -> None:
        file_name_len: Final[int] = 20
        App.CUSTOM_SIDEBAR_LINE_ACTIVE = True
        selected_files: dict[str, str] = app_data['selections']

        if not selected_files:
            return

        for _, file_path in selected_files.items():
            try:
                media_file = WorkWithSystemMedia.create_media_file(file_path)
            except FileNotFoundError:
                ContentWindowEventHandler._instance.app.create_notification(
                    message="Файл был удалён или перемешен!",
                    duration=5,
                    lvl=NotificationLevelEnum.WARNING,
                )
            except FileSuffixError as e:
                ContentWindowEventHandler._instance.app.create_notification(
                    message=f"Неверный формат файла ({e.target[0]})!",
                    duration=5,
                    lvl=NotificationLevelEnum.WARNING,
                )
            else:
                ContentWindow.media_file = media_file
                if len(media_file.name) > file_name_len:
                    short_name = media_file.name[:file_name_len] + "..."
                else:
                    short_name = media_file.name
                ContentWindowEventHandler._instance.app.create_notification(
                    message=f"Файл `{short_name}` успешно выбран!",
                    duration=4,
                    lvl=NotificationLevelEnum.DEFAULT,
                )

    @staticmethod
    def clear_input_fields() -> None:
        """Очистка полей ввода формы создания медиа-файла"""
        for filed_tag in MediaTagFields:
            filed_to_clear = BaseAppWindow.get_el_tag("ContentWindow", filed_tag)
            if filed_tag == MediaTagFields.type:
                dpg.configure_item(filed_to_clear, default_value=MediaTypeEnum.PHOTO)
            else:
                dpg.set_value(filed_to_clear, "")

    @staticmethod
    def toggle_selection(sender: str, app_data: None, user_data: str) -> None:
        """Выбор тега для меди-файла

        :param sender: UUID.__str__() Нажатый тег
        :param app_data: None
        :param user_data: UUID.__str__() Связанный ответный тег
        """
        shown_win_tag = BaseAppWindow.get_el_tag(ContentWindow.__name__, ("selected", "tags"))
        non_shown_win_tag = BaseAppWindow.get_el_tag(ContentWindow.__name__, ("available", "tags"))

        dpg.configure_item(sender, show=not dpg.is_item_shown(sender))
        dpg.configure_item(user_data, show=not dpg.is_item_shown(user_data))
        user_data: UUID = UUID(user_data)
        if user_data in ContentWindow.selected_tags:
            ContentWindow.selected_tags.remove(user_data)
            ContentWindow.active_tag_counter += 1

            if ContentWindow.active_tag_counter > 0:
                dpg.configure_item(non_shown_win_tag, show=True)
            if not ContentWindow.selected_tags:
                dpg.configure_item(shown_win_tag, show=False)
        else:
            ContentWindow.selected_tags.append(UUID(sender))
            ContentWindow.active_tag_counter -= 1

            if ContentWindow.active_tag_counter <= 0:
                ContentWindow.active_tag_counter = 0
                dpg.configure_item(non_shown_win_tag, show=False)
            if not dpg.is_item_shown(shown_win_tag):
                dpg.configure_item(shown_win_tag, show=True)

    def add_new_tag(self, sender: DPGTag, app_data: str, user_data: None) -> None:
        """Добавление нового тега пользователя.

        :param sender: ID поля для ввода тега.
        :param app_data: Название нового тега пользователя.
        :param user_data: None.
        """
        for tag in self._instance.user_tags:
            if tag.name == app_data:
                break
        else:
            self._instance.update_tag_selector(Tag(id=UUID(uuid4().__str__()), name=dpg.get_value(sender)))
        dpg.set_value(sender, ""),


class ContentWindow(BaseAppWindow, ContentWindowEventHandler, ContentWindowThemesHandler):
    """Основное окно приложения"""
    TAG_ROW_WIDTH: Final[int] = 500
    media_file: MediaFile | None = None
    selected_tags: list[UUID] = []
    user_tags: list[Tag] = []
    all_accepted_tags: list[Tag] = []
    active_tag_counter: int = 0

    def __init__(self, main_app: App) -> None:
        super().__init__(main_app=main_app, class_name=self.__class__.__name__)
        ContentWindowEventHandler._instance = self
        self.current_row_width: int = 0
        self.selected_row_group, self.available_row_group = None, None
        self.main_parent_container = self.get_el_tag(tag_target="MainWindow", tag_name=("container",))

        self._create_clear_alert_window()
        self.create_window()
        self.create_children_windows()

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
                height=120,
                width=424,
        ) as alert_win:
            dpg.add_text("Все поля для ввода будут очищены!", indent=100)
            dpg.add_spacer()
            dpg.add_text("Теги будут сохранены, но поля для ввода очищены.\n Продолжить операцию?")
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

        self.set_theme(alert_win, self.theme_clear_field_alert)

    def _create_file_dialog_window(self) -> DPGTag:
        """Создание модального окна для выбора файла"""
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

    def __create_media_fields(self) -> None:
        """Создание полей для ввода данных медиа-файла"""
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

        dpg.add_spacer(height=5)
        self.set_theme(
            dpg.add_child_window(
                tag=self.set_new_el_tag(self.class_name, ("selected", "tags")),
                height=80,
                width=int(App.MIN_WIDTH // 1.5),
                border=False,
                horizontal_scrollbar=False,
                show=False,
            ),
            self.theme_opacity_win
        )

        non_sel_tag = self.set_new_el_tag(self.class_name, ("available", "tags"))
        dpg.add_text("Доступные теги: ")
        self.set_theme(
            dpg.add_child_window(
                tag=non_sel_tag,
                height=80,
                width=int(App.MIN_WIDTH // 1.5),
                border=False,
                horizontal_scrollbar=False,
                show=False,
            ),
            self.theme_opacity_win
        )

        with dpg.group(horizontal=True):
            dpg.add_text("Добавление нового тега:")
            with dpg.tooltip(
                    dpg.add_input_text(
                        tag=self.set_new_el_tag(self.class_name, "new_tag"),
                        hint="Введите новый тег",
                        callback=self.add_new_tag,
                        no_spaces=True,
                        on_enter=True,
                        auto_select_all=True,
                        always_overwrite=True,
                        width=200,
                    ),
                    delay=.3,
                    hide_on_activity=True
            ):
                dpg.add_text("Нажмите `Enter` для сохранения")

        self.update_tag_selector()

    def update_tag_selector(self, new_tag: Tag | None = None) -> None:
        """Обновление списка доступных тегов медиа-файла

        :param new_tag: Теги добавленные пользователем вручную.
        """
        if new_tag is not None:
            ContentWindow.user_tags.append(new_tag)
            ContentWindow.all_accepted_tags.append(new_tag)
        else:
            ContentWindow.all_accepted_tags = [*TagService().get_weak_tags()]
        ContentWindow.active_tag_counter = len(ContentWindow.all_accepted_tags)

        for media_tag in ContentWindow.all_accepted_tags:
            dpg.configure_item(self.get_el_tag(self.class_name, ("available", "tags")), show=True)
            tag, label = media_tag.id.__str__(), f"#{media_tag.name}"

            if dpg.does_item_exist(tag):
                continue

            button_width = len(label) * 10 + 10

            if self.selected_row_group is None or self.current_row_width + button_width > ContentWindow.TAG_ROW_WIDTH:
                self.available_row_group = dpg.add_group(
                    horizontal=True, parent=self.get_el_tag(self.class_name, ("available", "tags"))
                )
                self.selected_row_group = dpg.add_group(
                    horizontal=True, parent=self.get_el_tag(self.class_name, ("selected", "tags"))
                )
                self.current_row_width = 0

            self.current_row_width += button_width + 10

            selected_tag = dpg.add_button(
                tag=uuid4().__str__(),
                label=label,
                parent=self.selected_row_group,
                callback=self.toggle_selection,
                show=False,
            )
            available_tag = dpg.add_button(
                tag=tag,
                label=label,
                parent=self.available_row_group,
                callback=self.toggle_selection,
                show=True,
                user_data=selected_tag,
            )
            dpg.configure_item(selected_tag, user_data=available_tag)

            self.set_theme(selected_tag, self.theme_rounded_btn)
            self.set_theme(available_tag, self.theme_rounded_btn)

    def clear_input_fields(self) -> None:
        """Полная очистка при выходе из формы создания"""
        super().clear_input_fields()
        ContentWindow.media_file = None
        ContentWindow.user_tags.clear()
        ContentWindow.selected_tags.clear()
        ContentWindow.all_accepted_tags.clear()
        ContentWindow.active_tag_counter = 0
        self.current_row_width, self.selected_row_group, self.available_row_group = 0, None, None
        available_group_tags: list[int] = dpg.get_item_children(
            self.get_el_tag(self.class_name, ("available", "tags"))
        )[1]
        available_group_tags.extend(
            dpg.get_item_children(self.get_el_tag(self.class_name, ("selected", "tags")))[1]
        )
        dpg.configure_item(self.get_el_tag(self.class_name, ("selected", "tags")), show=False)
        for tag in available_group_tags:
            dpg.delete_item(tag)
        self.update_tag_selector()

    def create_window(self):
        """Создание основного контейнера для контента приложения"""
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
                file_dialog_tag = self._create_file_dialog_window()

                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Отменить",
                        callback=lambda: (
                            dpg.configure_item(self.main_content_tag, show=False),
                            self.clear_input_fields(),
                        )
                    )
                    dpg.add_spacer(width=50)
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
                        ) if not ContentWindow.media_file else (
                            dpg.configure_item(self.main_content_tag, show=False),
                            self.save_media_info(),
                            MainWindow.update_media_tree(),
                            self.clear_input_fields(),
                        )
                    )

    def create_children_windows(self):
        PersonContent(self).create_window()
