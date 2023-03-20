import queue
import threading
from abc import ABC, abstractmethod


class IO(ABC):
    def __init__(self, queue: queue.Queue):
        self._queue = queue
        self._stop_event = threading.Event()
        self._is_started = False

    def start(self):
        self._is_started = True
        self._stop_event.clear()
        self._start()
        t = threading.Thread(target=self.start_running_thread)
        t.start()

    @abstractmethod
    def start_running_thread(self):
        pass

    def stop(self):
        self._is_started = False
        self._stop()
        self._stop_event.set()

    def toggle(self):
        if self.is_started():
            self.stop()
        else:
            self.start()

    def is_started(self):
        return self._is_started

    @abstractmethod
    def _start(self):
        pass

    @abstractmethod
    def _stop(self):

        pass
