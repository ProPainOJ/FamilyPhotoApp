from dataclasses import dataclass
from types import NoneType
from typing import TypeAlias, NamedTuple

from src.core.exceptions.application_exception import ArgValueError

Float0To1: TypeAlias = float
Position: TypeAlias = tuple[int, int]


@dataclass
class PointCoordinate:
    """Точка координат."""
    x: int
    """Позиция по оси `x`"""
    y: int
    """Позиция по оси `y`"""

    def __post_init__(self) -> None:
        if self.x < 0 or self.y < 0:
            raise ArgValueError(msg="x и y не могут быть менее 0!")
        self.to_pos = (self.x, self.y)

    def __iter__(self) -> tuple[int, int]:
        return self.x, self.y

    def __str__(self) -> str:
        return f"coordinate: {self.to_pos}"


class Rectangle(NamedTuple):
    left_up_point: PointCoordinate
    right_down_point: PointCoordinate

    def __str__(self) -> str:
        return f"<lu: {self.left_up_point}, rd: {self.right_down_point}>"


@dataclass
class Quadrilateral:
    """Четырёхугольник."""
    width: int
    """Ширина изображения."""
    height: int
    """Высота изображения."""

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ArgValueError(
                msg="Неверно указаны размеры изображения!",
                targets=[f"{self.width}", f"{self.height}"],
            )


@dataclass
class RectangularImageElement(Quadrilateral):
    """Размеры и позиция прямоугольного изображения."""

    pos: Rectangle = None
    """Позиция относительного позиционирования во внешнем контейнере."""
    wrap_width: int | None = None
    """Ширина внешнего контейнера."""
    wrap_height: int | None = None
    """Длинна внешнего контейнера."""

    def __post_init__(self) -> None:
        if self.wrap_width is None:
            self.wrap_width = self.width
        else:
            if self.wrap_width < self.width:
                raise ArgValueError(
                    msg="Неверно заданы размера внешнего контейнера!",
                    targets=[f"{self.wrap_width}"],
                    pre_decision=f"Укажите {self.wrap_width} более {self.width}",
                )

        if self.wrap_height is None:
            self.wrap_height = self.height
        else:
            if self.wrap_height < self.height:
                raise ArgValueError(
                    msg="Неверно заданы размера внешнего контейнера!",
                    targets=[f"{self.wrap_height}"],
                    pre_decision=f"Укажите {self.wrap_height} более {self.height}",
                )

        if self.pos is None:
            lu_pos = PointCoordinate(x=0, y=self.wrap_height)
            rd_pos = PointCoordinate(x=lu_pos.x + self.width, y=lu_pos.y - self.height)
            self.pos = Rectangle(lu_pos, rd_pos)
        else:
            if (
                    self.pos.left_up_point.x > self.pos.right_down_point.x
                    or self.pos.left_up_point.y < self.pos.right_down_point.y
            ):
                raise ArgValueError(
                    msg="Прямоугольник не правильный!",
                    comment="Координаты должны образовывать корректный прямоугольник.",
                    targets=[self.pos.left_up_point, self.pos.right_down_point, 12.4],
                    pre_decision=f"Укажите {self.pos.left_up_point} левее {self.pos.right_down_point}",
                )
            elif (
                    self.pos.left_up_point.x + self.pos.right_down_point.x > self.wrap_width
                    or self.pos.left_up_point.y + self.pos.right_down_point.y > self.wrap_height
            ):
                raise ArgValueError(
                    msg="Координаты углов не соответствуют длине и ширине прямоугольника!",
                    targets=[self.pos.left_up_point, self.pos.right_down_point],
                    pre_decision=f"Укажите другие {self.pos.left_up_point}, {self.pos.right_down_point}",
                )
            elif not (self.wrap_height - self.height) >= self.pos.left_up_point.y - self.height:
                free_height = self.wrap_height - self.height
                raise ArgValueError(
                    msg="Позиции углов не могу выходить за размеры внешнего контейнера!",
                    comment=f"Не влезает по высоте! {self.pos.left_up_point.y - self.height} < {free_height}",
                )
            elif not (self.wrap_width - self.width) >= self.pos.right_down_point.x - self.width:
                free_height = self.wrap_width - self.width
                raise ArgValueError(
                    msg="Позиции углов не могу выходить за размеры внешнего контейнера!",
                    comment=f"Не влезает по ширине! {self.pos.right_down_point.x - self.width} < {free_height}",
                )

    def get_lu_pos(self) -> PointCoordinate:
        return PointCoordinate(
            x=self.pos.left_up_point.x,
            y=self.wrap_height - self.pos.left_up_point.y,
        )


def get_element_pos(
        el_settings: RectangularImageElement, perc_padding: Float0To1 = 0.5, left_padding: int = 0, top_padding: int = 0
) -> PointCoordinate:
    """Получение позиции элемента в окне.

    :param el_settings: Изображение в контейнере
    :param perc_padding: (0.0 - 1.0) Отступ от левого верхнего угла в проценте от всего свободного пространства (Игнорирует ручные отступы)
    :param left_padding: Левый отступ
    :param top_padding: Верхний отступ

    :return: Позиция элемента
    """  # noqa: E501
    args = (left_padding, top_padding)

    if any(args):
        if left_padding + el_settings.width > el_settings.wrap_width:
            left_padding = el_settings.wrap_width - el_settings.width
        if top_padding + el_settings.height > el_settings.wrap_height:
            top_padding = el_settings.wrap_height - el_settings.height
        return PointCoordinate(x=0 + left_padding, y=0 + top_padding)
    if perc_padding is not None:
        perc_padding = max(0.0, min(1.0, perc_padding))
        all_x_free_space = el_settings.wrap_width - el_settings.width
        all_y_free_space = el_settings.wrap_height - el_settings.height
        x_padding, y_padding = int(all_x_free_space * perc_padding), int(all_y_free_space * perc_padding)
        pos = el_settings.get_lu_pos()
        new_pos = PointCoordinate(x=pos.x + x_padding, y=pos.y + y_padding)
        return new_pos
    raise ValueError(f"Не указаны аргументы <{[arg for arg in args if not isinstance(arg, NoneType)]}>")
