"""Completion thread for running Jedi completions in background."""

from PySide6.QtCore import QThread, Signal

from ..core.completion_engine import CompletionEngine


class CompletionThread(QThread):
    """Background thread for running Jedi code completions."""

    # Signal emitted when completions are ready
    completions_ready = Signal(list)  # List of CompletionItem objects

    def __init__(self):
        super().__init__()
        self.engine = CompletionEngine()
        self.text = ""
        self.line = 0
        self.column = 0
        self._running = True

    def run_completions(self, text: str, line: int, column: int):
        """Request completions for the given position."""
        self.text = text
        self.line = line
        self.column = column
        
        # Start thread if not already running
        if not self.isRunning():
            self.start()
        else:
            # If already running, restart with new parameters
            self._running = False
            self.wait()
            self._running = True
            self.start()

    def run(self):
        """Run the completion query in background thread."""
        self._running = True
        completions = self.engine.get_completions(
            self.text, self.line, self.column
        )
        
        if self._running:
            self.completions_ready.emit(completions)

    def stop(self):
        """Stop the current completion request."""
        self._running = False
        self.wait()
