import dearpygui.dearpygui as dpg

from core.base import App
from src.ui.create_media import NewContentWindow
from src.ui.main import MainWindow
from src.ui.media import GetContentWindow

if __name__ == "__main__":
    dpg.create_context()

    main_app = App()
    MainWindow(main_app)
    NewContentWindow(main_app)
    GetContentWindow(main_app)
    dpg.setup_dearpygui()
    dpg.show_viewport()

    main_app.control_frames()

    dpg.start_dearpygui()
    dpg.destroy_context()
