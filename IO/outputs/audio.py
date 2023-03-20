import queue

import pyttsx3

from IO.outputs.output import Output
from settings.settings import Settings


class Audio(Output):
    _instance = None

    def __new__(cls, input_queue: queue.Queue, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, settings: Settings, input_queue: queue.Queue):
        super().__init__(input_queue)
        self.engine = pyttsx3.init()
        self.settings = settings

    def _start(self):
        pass

    def _stop(self):
        pass

    def _output(self, text: str):
        self.engine.say(text)
        self.engine.runAndWait()
