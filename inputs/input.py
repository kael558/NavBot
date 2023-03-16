from abc import ABC, abstractmethod

import queue
import threading

class Input(ABC):
    def __init__(self, output_queue: queue.Queue):
        self._output_queue = output_queue
        self._stop_event = threading.Event()
        
    def start(self):
        self._start()
        t = threading.Thread(target=self.start_running_thread)
        t.start()
        return t

    def start_running_thread(self):
        while not self._stop_event.is_set():
            res = self._get_input()
            if res is None:
                break
            self._output_queue.put(res)

    def stop(self):
        self._stop()
        self._stop_event.set()

    @abstractmethod
    def _start(self):
        pass

    @abstractmethod
    def _stop(self):
        pass

    @abstractmethod
    def _get_input(self):
        pass
    





