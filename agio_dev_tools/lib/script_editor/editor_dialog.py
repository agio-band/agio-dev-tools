from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QSplitter
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt

from .core.code_manager import CodeManager
from .core.executor import CodeExecutor
from .widgets.output_widget import OutputWidget
from .widgets.tab_widget import TabWidget


class ScriptEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("agio Python Script Editor")
        self.resize(1000, 700)
        self.code_manager = CodeManager()
        self.executor = CodeExecutor()
        self._setup_ui()
        self._setup_shortcuts()
        self.executor.stdout_signal.connect(self.output_widget.append_output)
        self.executor.stderr_signal.connect(self.output_widget.append_error)

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.output_widget = OutputWidget()
        splitter.addWidget(self.output_widget)

        self.tab_widget = TabWidget(self)
        splitter.addWidget(self.tab_widget)

        splitter.setSizes([210, 490])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # self.tab_widget.add_new_tab("Script 1")

    def _setup_shortcuts(self):
        ctrl_n = QShortcut(QKeySequence("Ctrl+N"), self)
        ctrl_n.activated.connect(self.tab_widget.add_new_tab)

    def execute_selected(self):
        editor = self.tab_widget.current_editor()
        selected_text = editor.get_selected_text()

        if selected_text.strip():
            self.output_widget.append_prompt(selected_text)
            self.executor.execute(selected_text)
        else:
            cursor = editor.textCursor()
            cursor.movePosition(cursor.StartOfLine)
            cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)
            line_text = cursor.selectedText().replace('\u2029', '\n')

            if line_text.strip():
                self.output_widget.append_prompt(line_text)
                self.executor.execute(line_text)

    def execute_code(self, code: str = None):
        if code is None:
            code = self.get_current_code()

        if code and code.strip():
            self.output_widget.append_prompt(code)
            self.executor.execute(code)

    # ========== Public API Methods ==========

    def add_tab(self, title: str = "Untitled", code: str = "") -> object:
        """
        Add a new tab with optional title and code.

        Args:
            title: Tab title
            code: Initial code text

        Returns:
            InputWidget for the new tab
        """
        return self.tab_widget.add_new_tab(title, code)

    def get_current_code(self) -> str:
        return self.tab_widget.get_tab_text()

    def get_tab_code(self, index: int) -> str:
        return self.tab_widget.get_tab_text(index)

    def set_current_code(self, code: str):
        self.tab_widget.set_tab_text(code)

    def set_tab_code(self, code: str, index: int):
        self.tab_widget.set_tab_text(code, index)

    def get_tab_count(self) -> int:
        return self.tab_widget.count()

    def get_tab_title(self, index: int) -> str:
        return self.tab_widget.tabText(index)

    def set_tab_title(self, index: int, title: str):
        self.tab_widget.setTabText(index, title)

    def get_active_tab_index(self) -> int:
        return self.tab_widget.currentIndex()

    def set_active_tab(self, index: int):
        self.tab_widget.setCurrentIndex(index)

    def close_tab(self, index: int):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)

    def get_output(self) -> str:
        return self.output_widget.toPlainText()

    def clear_output(self):
        self.output_widget.clear_output()

    def clear_namespace(self):
        self.executor.clear_namespace()

    def update_namespace(self, updates: dict):
        self.executor.update_namespace(updates)

    def get_editor(self, index: int = None):
        if index is None:
            return self.tab_widget.current_editor()
        return self.tab_widget.widget(index).edit

    def showEvent(self, event):
        super().showEvent(event)
        if self.tab_widget.count() > 0:
            self.tab_widget.current_editor().setFocus()

    def closeEvent(self, event):
        self.tab_widget.cleanup_all()
        super().closeEvent(event)
