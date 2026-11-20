"""Completion worker thread.

A single QThread processes completion requests sequentially. Requests are
queued by the editor and coalesced: if the user keeps typing, only the
latest request is actually evaluated by jedi. Results are emitted back to
the main thread through a signal (queued connection), so the UI never
blocks on jedi.

The jedi engine is created inside run() so that all jedi work happens in
this single worker thread.
"""

import queue

from PySide6.QtCore import QThread, Signal

from ..core.completion_engine import CompletionEngine


class CompletionWorker(QThread):
    """Runs jedi completions off the main thread."""

    results_ready = Signal(list, int)  # completions, request_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: "queue.SimpleQueue" = queue.SimpleQueue()
        self._stopped = False

    def request_completions(self, text: str, line: int, column: int, request_id: int):
        """Queue a completion request (thread-safe)."""
        if not self._stopped:
            self._queue.put((request_id, text, line, column))

    def stop(self):
        """Stop the worker loop and wait for the thread to finish."""
        self._stopped = True
        self._queue.put(None)  # sentinel
        self.wait(3000)

    def run(self):
        engine = CompletionEngine()
        while True:
            item = self._queue.get()
            if item is None:  # stop sentinel
                return
            # coalesce: drop everything but the newest queued request
            while True:
                try:
                    nxt = self._queue.get_nowait()
                except queue.Empty:
                    break
                if nxt is None:
                    return
                item = nxt
            request_id, text, line, column = item
            completions = engine.get_completions(text, line, column)
            if not self._stopped:
                self.results_ready.emit(completions, request_id)


# Backward-compatible name used by tab_widget
CompletionThread = CompletionWorker
