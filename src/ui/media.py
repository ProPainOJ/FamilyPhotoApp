import os
from typing import TypeAlias
from uuid import uuid4

import dearpygui.dearpygui as dpg

import src.utils.dir as dir_utils
import src.utils.position as pos_utils
from src import App
from src.core.modals.modals import Media
from src.core.services.media_service import MediaService
from src.external.image.base import ImageHandler, DearImage
from src.ui import BaseAppWindow, AppTagHelper, MainAppCallbackHandlerABC

TagName: TypeAlias = str | int


class GetContentWindowCallbackHandler(MainAppCallbackHandlerABC):
    pass


class GetContentWindow(BaseAppWindow, GetContentWindowCallbackHandler):
    CURRENT_MEDIA: Media = None
    CREATED_MEDIA: set[TagName] = {}
    MIN_MEDIA_CONTENT_WIDTH: int = 570
    MIN_MEDIA_CONTENT_HEIGHT: int = 438

    def __init__(self, main_app: App) -> None:
        super().__init__(main_app, self.__class__.__name__)
        self.media_service = MediaService()
        self.main_parent_container = self.get_el_tag(tag_target="MainWindow", tag_name=("container",))
        self.texture_reg_tag = self.set_new_el_tag(GetContentWindow.__name__, ("texture", "registry"))
        self.raw_texture = self.set_new_el_tag(GetContentWindow.__name__, "raw_dynamic_texture")
        self.image_tag: str | None = None
        self.create_window()

    @staticmethod
    def set_new_image(new_media: Media) -> None:
        """Создание нового изображения в `media` контейнере.

        :param new_media: Объект ``Media`` для отрисовки
        """

        start_tag = f"raw_image"
        new_image_tag = "_".join((start_tag, new_media.id.__str__()))
        old_image_tag = "_".join((start_tag, GetContentWindow.CURRENT_MEDIA.id.__str__()))

        if old_image_tag in AppTagHelper.WINDOW_ELEMENTS_TAG[GetContentWindow.__name__]:
            current_image_tag = AppTagHelper.get_el_tag(
                GetContentWindow.__name__,
                old_image_tag,
            )
            dpg.configure_item(
                current_image_tag,
                show=False,
            )
            GetContentWindow.CURRENT_MEDIA = new_media
            if new_image_tag in AppTagHelper.WINDOW_ELEMENTS_TAG[GetContentWindow.__name__]:
                show_tag = AppTagHelper.get_el_tag(GetContentWindow.__name__, new_image_tag)
                dpg.configure_item(
                    show_tag,
                    show=True,
                )
                return
        left_sidebar_tag = AppTagHelper.get_el_tag(tag_target="MainWindow", tag_name="sidebar_left")
        max_width = dpg.get_viewport_width() - dpg.get_item_width(left_sidebar_tag)
        max_height = dpg.get_item_height(
            AppTagHelper.get_el_tag(tag_target="MainWindow", tag_name="container")
        )

        resized_image = ImageHandler.resize_image_keep_ratio(
            image_binary_data=new_media.data,
            resize_max_width=max_width,
            resize_max_height=max_height,
        )
        raw_image = ImageHandler.convert_bites_to_raw_list(
            dear_image=resized_image,
            is_raw_data=True,
            mode="RGBA",
        )

        AppTagHelper.delete_tag(GetContentWindow.__name__, "raw_dynamic_texture", del_obj_by_tag=True)
        dpg.add_raw_texture(
            id=AppTagHelper.set_new_el_tag(GetContentWindow.__name__, "raw_dynamic_texture"),
            parent=AppTagHelper.get_el_tag(GetContentWindow.__name__, ("texture", "registry")),
            width=resized_image.re_width,
            height=resized_image.re_height,
            default_value=raw_image.data,
            format=dpg.mvFormat_Float_rgba,
        )

        dpg.add_image(
            id=AppTagHelper.set_new_el_tag(GetContentWindow.__name__, new_image_tag),
            parent=AppTagHelper.get_el_tag(GetContentWindow.__name__, BaseAppWindow.MAIN_CONTAINER_TAG_NAME),
            texture_tag=AppTagHelper.get_el_tag(GetContentWindow.__name__, "raw_dynamic_texture"),
            width=resized_image.re_width,
            height=resized_image.re_height,
            user_data=resized_image,
        )

    def resize_media_content_callback(self) -> None:
        """Изменение положения и размера медиа."""
        left_sidebar_tag = self.get_el_tag(tag_target="MainWindow", tag_name="sidebar_left")

        max_width = dpg.get_viewport_width() - dpg.get_item_configuration(left_sidebar_tag)["width"]
        max_height = dpg.get_item_configuration(self.main_parent_container)["height"]

        image_tag = AppTagHelper.get_el_tag(GetContentWindow.__name__, f"raw_image_{GetContentWindow.CURRENT_MEDIA.id}")
        media_user_data: DearImage = dpg.get_item_user_data(image_tag)

        if media_user_data.or_width > max_width or media_user_data.or_height > max_height:
            new_size = ImageHandler.calculate_new_size(
                original_width=media_user_data.or_width,
                original_height=media_user_data.or_height,
                max_width=max_width,
                max_height=max_height,
            )
        else:
            new_size = (media_user_data.or_width, media_user_data.or_height)

        new_image_center_pos = pos_utils.get_element_pos(
            pos_utils.RectangularImageElement(
                width=new_size[0],
                height=new_size[1],
                wrap_width=max_width,
                wrap_height=max_height,
            ),
        )
        dpg.configure_item(
            image_tag,
            width=new_size[0],
            height=new_size[1],
            pos=new_image_center_pos.to_pos,
        )

    def create_window(self):
        """Заполнение основного контейнер данными о медиа."""
        pepe_path = dir_utils.join_exist_path(os.getcwd(), ("src", "resources", "images", "pepe.png"))

        with open(pepe_path, "rb") as default_image:
            default_image = default_image.read()
            start_media = Media(
                id=uuid4(),
                data=default_image,
            )

        with dpg.child_window(tag=self.main_content_tag, parent=self.main_parent_container, show=False, border=False):
            dpg.add_texture_registry(id=self.texture_reg_tag)

        GetContentWindow.CURRENT_MEDIA = start_media
        self.set_new_image(new_media=start_media)
        self.app.insert_item_resize_callback(self.texture_reg_tag, self.resize_media_content_callback, True)
