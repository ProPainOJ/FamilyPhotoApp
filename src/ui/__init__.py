from abc import ABC, abstractmethod


class MainAppElement(ABC):

    @abstractmethod
    def crate_main_template(self): pass

    @abstractmethod
    def create_main_window(self): pass
