from abc import ABC, abstractmethod

from IO.IO import IO


class Input(IO, ABC):
    def start_running_thread(self):
        while not self._stop_event.is_set():
            res = self._input()
            if res is None:
                break
            self._queue.put(res)

    @abstractmethod
    def _input(self):
        pass


