import dearpygui.dearpygui as dpg

from core.base import App
from src.ui.main import MainWindow

if __name__ == "__main__":
    dpg.create_context()

    main_app = App()
    MainWindow(main_app)

    dpg.setup_dearpygui()
    dpg.show_viewport()

    main_app.control_frames()

    dpg.start_dearpygui()
    dpg.destroy_context()
