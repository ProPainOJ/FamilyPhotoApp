import uuid
from typing import TYPE_CHECKING

import dearpygui.dearpygui as dpg

from src.constants.application import ColorsEnum
from src.constants.modals import GenderTypeEnum
from src.ui import AppWindowABC

if TYPE_CHECKING:
    from src.ui.content import ContentWindow


class PersonContent(AppWindowABC):
    """Работа с сущностью `Person`"""

    def __init__(self, main_frame: "ContentWindow") -> None:
        self.main_frame = main_frame

    def __create_person_fields(self):
        """Создание полей ввода для формы `Person`"""
        dpg.add_input_text(
            label="ID",
            tag="person_id",
            default_value=str(uuid.uuid4()),
            readonly=True,
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person"),
            show=False
        )
        dpg.add_input_text(
            label="Имя",
            tag="person_name",
            hint="Введите имя",
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person")
        )
        dpg.add_input_text(
            label="Фамилия",
            tag="person_surname",
            hint="Введите фамилию",
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person")
        )

        dpg.add_input_text(
            label="Отчество",
            tag="person_patronymic",
            hint="Введите отчество",
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person")
        )
        dpg.add_input_text(
            label="Дата рождения (ГГГГ-ММ-ДД)",
            tag="person_birth_date",
            hint="YYYY-MM-DD",
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person")
        )
        dpg.add_input_text(
            label="Дата смерти (ГГГГ-ММ-ДД)",
            tag="person_death_date",
            hint="YYYY-MM-DD",
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person")
        )

        dpg.add_input_text(
            label="Биография",
            tag="person_bio",
            hint="Введите биографию",
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person"),
            height=100,
            multiline=True,
        )
        dpg.add_combo(
            label="Пол",
            tag="person_gender",
            items=[gender for gender in GenderTypeEnum],
            default_value=GenderTypeEnum.MALE,
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person")
        )
        dpg.add_input_text(
            label="ID вероисповедания",
            tag="person_faith_id",
            hint="Введите ID вероисповедания",
            parent=self.main_frame.get_el_tag(self.main_frame.class_name, "person")
        )

    def create_window(self):
        """Создание окна для работы с `Person`"""
        with dpg.child_window(
                tag=self.main_frame.set_new_el_tag(self.main_frame.class_name, "person"),
                parent=self.main_frame.main_parent_container,
                show=True,
                border=False,
                horizontal_scrollbar=False,
        ):
            dpg.add_text("Создание новой персоны", color=ColorsEnum.GREEN.value.to_tuple(), bullet=False)
            self.__create_person_fields()

    def create_children_windows(self):
        raise NotImplementedError
