from abc import ABC, abstractmethod


class Input(ABC):
    @abstractmethod
    def input(self):
        pass



