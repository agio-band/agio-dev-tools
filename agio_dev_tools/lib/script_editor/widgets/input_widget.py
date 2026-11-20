"""InputWidget — kept as a name for backward compatibility.

The actual implementation lives in code_editor.CodeEditor (QPlainTextEdit
based, supports code folding). InputWidget is now a thin alias/subclass.
"""

from .code_editor import CodeEditor


class InputWidget(CodeEditor):
    """Backward-compatible alias for the code editor widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
