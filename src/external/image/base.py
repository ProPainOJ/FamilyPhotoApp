import io
from dataclasses import dataclass
from typing import Literal

import numpy as np
from PIL import Image
from PIL.ImageFile import ImageFile

from src import AppConstEnum
from src.constants.media import FileExtensionType, FILE_EXTENSION

Image_Ratio = tuple[int, int]


@dataclass
class DearImage:
    data: ImageFile
    re_width: int
    re_height: int
    or_width: int
    or_height: int
    format: FileExtensionType


@dataclass
class DearRawImage(DearImage):
    data: tuple[float, ...] | np.dtype[np.float32]


class ImageHandler:
    """Класс для обработки фото из БД."""

    @staticmethod
    def convert_bites_to_raw_list(dear_image: DearImage, is_raw_data: bool, mode: Literal["RGB", "RGBA"],
                                  show_image: bool = False) -> DearRawImage:
        """Преобразует ``bytes`` изображение в `1D` список пикселей для
         `add_static_texture`/`add_dynamic_texture`/`add_raw_texture`.

        :param dear_image: Изображение
        :param is_raw_data: Преобразовать-ли в виде сырых данных
        :param mode: Формат изображения.
        :param show_image: Отобразить-ли изображение

        :return: float значения пикселей в одномерном массиве
        """
        pil_img = dear_image.data
        image_size = pil_img.size
        if pil_img.mode != mode:
            try:
                pil_img = pil_img.convert(mode)
            except Exception as e:
                raise ValueError(f"Ошибка конвертации {pil_img.mode} в {mode}: {str(e)}")

        if show_image and AppConstEnum.DEBUG.value:
            pil_img.show()
        if is_raw_data:
            image_array = np.array(pil_img)
            texture_data = image_array.ravel().astype(np.float32) / 255.0
        else:
            pixel_data = pil_img.tobytes()
            texture_data = tuple(byte / 255.0 for byte in pixel_data)

        return DearRawImage(
            data=texture_data,
            or_width=image_size[0],
            or_height=image_size[1],
            re_width=image_size[0],
            re_height=image_size[1],
            format=FILE_EXTENSION[dear_image.format],
        )

    @staticmethod
    def resize_image_keep_ratio(image_binary_data: bytes, resize_max_width: int = None, resize_max_height: int = None,
                                target_width: int = None, target_height: int = None,
                                mode: FileExtensionType = FileExtensionType.PNG) -> DearImage:
        """Изменяет размер изображения с сохранением соотношения сторон.

        :param image_binary_data: Бинарные данные изображения
        :param resize_max_width: Максимальная ширина
        :param resize_max_height: Максимальная высота
        :param target_width: Требуемая ширина (если указано, игнорирует max_width)
        :param target_height: Требуемая ширина (если указано, игнорирует max_height)
        :param mode: Формат изображения

        :return: Бинарные данные измененного изображения

        :raise: ValueError: Ошибка при изменении размера
        """

        pil_image = Image.open(io.BytesIO(image_binary_data))
        original_width, original_height = pil_image.size

        if target_width and target_height:
            new_width, new_height = target_width, target_height
        elif resize_max_width and resize_max_height:
            new_width, new_height = ImageHandler.calculate_new_size(
                original_width,
                original_height,
                resize_max_width,
                resize_max_height,
            )
        elif resize_max_width:
            new_width = min(resize_max_width, original_width)
            new_height = int((new_width / original_width) * original_height)
        elif resize_max_height:
            new_height = min(resize_max_height, original_height)
            new_width = int((new_height / original_height) * original_width)
        else:
            raise ValueError("Не указаны параметры изменения размера")

        try:
            resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except Exception as e:
            raise ValueError(f"Ошибка при изменении размера изображения: {str(e)}")
        return DearImage(
            data=resized_image,
            or_width=original_width,
            or_height=original_height,
            re_width=resized_image.size[0],
            re_height=resized_image.size[1],
            format=mode
        )

    @staticmethod
    def calculate_new_size(original_width: int, original_height: int,
                           max_width: int, max_height: int) -> Image_Ratio:
        """Рассчитывает новые размеры с сохранением пропорций.

        :param original_width: Оригинальная ширина
        :param original_height: Оригинальная высота
        :param max_width: Допустимая ширина
        :param max_height: Допустимая высота

        :return: Новый размер изображения
        """
        ratio = min(
            max_width / original_width,
            max_height / original_height
        )
        return int(original_width * ratio), int(original_height * ratio)
