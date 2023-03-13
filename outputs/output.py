from abc import abstractmethod, ABC


class Output(ABC):
    @abstractmethod
    def output(self, html_content: str):
        pass