from abc import ABC, abstractmethod

import src


class MainApp(ABC):


    def __int__(self) -> None:
        self.app = src.App()

    @abstractmethod
    def crate_main_template(self): pass

    @abstractmethod
    def create_main_window(self): pass
