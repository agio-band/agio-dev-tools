from PySide6.QtCore import QThread, Signal, QMutex, QWaitCondition

from ..core.completion_engine import CompletionEngine


class CompletionThread(QThread):
    completions_ready = Signal(list, int)  # (completions_list, request_id)

    def __init__(self):
        super().__init__()
        self._mutex = QMutex()
        self._wait_condition = QWaitCondition()
        self._text = None
        self._line = 0
        self._column = 0
        self._request_id = 0
        self._stop = False

    def request_completions(self, text: str, line: int, column: int, request_id: int):
        self._mutex.lock()
        self._text = text
        self._line = line
        self._column = column
        self._request_id = request_id
        self._wait_condition.wakeOne()
        self._mutex.unlock()

    def run(self):
        engine = CompletionEngine()

        while not self._stop:
            self._mutex.lock()
            if self._text is None:
                self._wait_condition.wait(self._mutex)

            if self._stop:
                self._mutex.unlock()
                break

            text = self._text
            line = self._line
            column = self._column
            req_id = self._request_id

            self._text = None
            self._mutex.unlock()

            completions = engine.get_completions(text, line, column)
            self.completions_ready.emit(completions, req_id)

    def stop(self):
        self._mutex.lock()
        self._stop = True
        self._text = ""
        self._wait_condition.wakeOne()
        self._mutex.unlock()
        self.wait()
