"""Main script editor dialog integrating all components."""

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
    """Main script editor dialog with tabs, REPL, and autocomplete."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Python Script Editor")
        self.resize(1000, 700)

        # Initialize core components
        self.code_manager = CodeManager()
        self.executor = CodeExecutor()

        # Create UI
        self._setup_ui()

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Connect executor signals
        self.executor.stdout_signal.connect(self.output_widget.append_output)
        self.executor.stderr_signal.connect(self.output_widget.append_error)

    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Create splitter for editor and output
        splitter = QSplitter(Qt.Vertical)

        # Create output widget (at top)
        self.output_widget = OutputWidget()
        splitter.addWidget(self.output_widget)

        # Create tab widget for code editors (at bottom)
        self.tab_widget = TabWidget(self)
        splitter.addWidget(self.tab_widget)

        # Set initial splitter sizes (30% output, 70% editor)
        splitter.setSizes([210, 490])

        # Show ready message
        # self.output_widget.append_output("Python Script Editor Ready. Press Ctrl+Enter to execute code.")

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Add initial tab
        self.tab_widget.add_new_tab("Script 1")

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Ctrl+N for new tab
        ctrl_n = QShortcut(QKeySequence("Ctrl+N"), self)
        ctrl_n.activated.connect(self.tab_widget.add_new_tab)

    def execute_selected(self):
        """Execute selected code or current line."""
        editor = self.tab_widget.current_editor()
        selected_text = editor.get_selected_text()

        if selected_text.strip():
            # Execute selected text
            self.output_widget.append_prompt(selected_text)
            self.executor.execute(selected_text)
        else:
            # Execute entire line or block
            cursor = editor.textCursor()
            cursor.movePosition(cursor.StartOfLine)
            cursor.movePosition(cursor.EndOfLine, cursor.KeepAnchor)
            line_text = cursor.selectedText().replace('\u2029', '\n')

            if line_text.strip():
                self.output_widget.append_prompt(line_text)
                self.executor.execute(line_text)

    def execute_code(self, code: str = None):
        """Execute code programmatically."""
        if code is None:
            # Get code from current tab
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
        """Get code from current tab."""
        return self.tab_widget.get_tab_text()

    def get_tab_code(self, index: int) -> str:
        """Get code from specific tab index."""
        return self.tab_widget.get_tab_text(index)

    def set_current_code(self, code: str):
        """Set code for current tab."""
        self.tab_widget.set_tab_text(code)

    def set_tab_code(self, code: str, index: int):
        """Set code for specific tab index."""
        self.tab_widget.set_tab_text(code, index)

    def get_tab_count(self) -> int:
        """Get number of tabs."""
        return self.tab_widget.count()

    def get_tab_title(self, index: int) -> str:
        """Get title of tab at index."""
        return self.tab_widget.tabText(index)

    def set_tab_title(self, index: int, title: str):
        """Set title of tab at index."""
        self.tab_widget.setTabText(index, title)

    def get_active_tab_index(self) -> int:
        """Get index of active tab."""
        return self.tab_widget.currentIndex()

    def set_active_tab(self, index: int):
        """Set active tab by index."""
        self.tab_widget.setCurrentIndex(index)

    def close_tab(self, index: int):
        """Close tab at index."""
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)

    def get_output(self) -> str:
        """Get all output from console."""
        return self.output_widget.toPlainText()

    def clear_output(self):
        """Clear console output."""
        self.output_widget.clear_output()

    def clear_namespace(self):
        """Clear execution namespace."""
        self.executor.clear_namespace()

    def update_namespace(self, updates: dict):
        """Update execution namespace with new variables."""
        self.executor.update_namespace(updates)

    def get_editor(self, index: int = None):
        """Get InputWidget for tab at index (or current tab if None)."""
        if index is None:
            return self.tab_widget.current_editor()
        return self.tab_widget.widget(index).edit

    def showEvent(self, event):
        """Handle show event to ensure UI is properly initialized."""
        super().showEvent(event)
        # Focus the first editor
        if self.tab_widget.count() > 0:
            self.tab_widget.current_editor().setFocus()

    def closeEvent(self, event):
        """Handle close event - cleanup all threads."""
        self.tab_widget.cleanup_all()
        super().closeEvent(event)
