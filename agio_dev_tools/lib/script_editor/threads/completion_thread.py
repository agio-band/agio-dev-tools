from PySide6.QtCore import QRunnable, QObject, Signal, QThreadPool

from ..core.completion_engine import CompletionEngine


class _EmitterBridge(QObject):
    """Signal bridge: lets QRunnable emit signals back to the main thread."""
    completions_ready = Signal(list, int)

    def send(self, completions, request_id):
        self.completions_ready.emit(completions, request_id)


class _CompletionTask(QRunnable):
    def __init__(self, text, line, column, request_id, emitter):
        super().__init__()
        self._text = text
        self._line = line
        self._column = column
        self._request_id = request_id
        self._emitter = emitter
        self.setAutoDelete(True)

    def run(self):
        engine = CompletionEngine()
        completions = engine.get_completions(self._text, self._line, self._column)
        self._emitter.send(completions, self._request_id)


class CompletionThread(QObject):
    completions_ready = Signal(list, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop = False
        self._bridge = _EmitterBridge()
        self._bridge.completions_ready.connect(self.completions_ready)

    def request_completions(self, text: str, line: int, column: int, request_id: int):
        if self._stop:
            return
        task = _CompletionTask(text, line, column, request_id, self._bridge)
        QThreadPool.globalInstance().start(task)

    def stop(self):
        self._stop = True

    def cleanup(self):
        self.stop()
