import dearpygui.dearpygui as dpg

from src import App
from src.core.modals.modals import MediaTypeEnum
from src.core.services.media_service import MediaService
from src.external.image.work_sys_media_file import FileExtensionType, WorkWithSystemMedia
from src.ui import BaseAppWindow
from src.ui.main import MainWindow


class NewContentWindow(BaseAppWindow):
    def __init__(self, main_app: App) -> None:
        super().__init__(main_app, MainWindow.__name__)
        self.create_window()
        self.media_service = MediaService()

    def create_window(self):
        def save_callback(sender, app_data, user_data) -> None:

            selected_files: dict[str, str] = app_data['selections']

            if not selected_files: return

            for file_name, file_path in selected_files.items():
                try:
                    file = WorkWithSystemMedia.create_media_file(file_path)
                    self.media_service.create_media(
                        name=file.name,
                        media_type=MediaTypeEnum.PHOTO,
                        size_bytes=file.size,
                        extension=file.extension,
                        data=file.data,
                    )
                except FileNotFoundError as e:
                    print(e.__str__())

        with dpg.file_dialog(
                directory_selector=False,
                tag="file_dialog_tag",
                callback=save_callback,
                file_count=0,
                width=1000,
                height=500,
                modal=True,
                show=False,
        ):
            dpg.add_file_extension(".*")
            for extension in FileExtensionType:
                dpg.add_file_extension(f".{extension}")
            else:
                pass
