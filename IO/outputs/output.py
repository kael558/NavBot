from abc import ABC, abstractmethod

from IO.IO import IO


class Output(IO, ABC):
    def start_running_thread(self):
        while not self._stop_event.is_set():
            res = self._queue.get(block=True)
            if res is None:
                break
            self._output(res)

    @abstractmethod
    def _output(self, text: str):
        pass
