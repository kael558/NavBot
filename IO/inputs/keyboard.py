import queue

from IO.inputs import Input


class Keyboard(Input):
    _instance = None

    def __new__(cls, queue: queue.Queue, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, output_queue: queue.Queue):
        super().__init__(output_queue)

    def _start(self):
        pass

    def _stop(self):
        pass

    def _input(self):
        return input("YOUR INPUT: ")