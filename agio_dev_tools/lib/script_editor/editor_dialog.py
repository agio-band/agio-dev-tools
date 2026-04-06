from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QSplitter
)
from PySide6.QtGui import QKeySequence, QShortcut, QGuiApplication
from PySide6.QtCore import Qt

from .core.code_manager import CodeManager
from .core.executor import CodeExecutor
from .core.session_manager import SessionManager, _get_session_name, DEFAULT_SESSIONS_DIR
from .widgets.output_widget import OutputWidget
from .widgets.tab_widget import TabWidget
from agio.tools import qt


class ScriptEditorDialog(QMainWindow):
    def __init__(self, parent=None, session_name: Optional[str] = None,
                 sessions_dir: Optional[Path] = None,
                 custom_namespace: Optional[dict] = None):
        super().__init__(parent)
        self.session_manager = SessionManager(
            session_name=session_name or _get_session_name(),
            sessions_dir=sessions_dir or DEFAULT_SESSIONS_DIR,
        )
        self.setWindowTitle(f"agio Python Script Editor [{self.session_manager.session_name}]")
        self.resize(1000, 700)
        self.code_manager = CodeManager()
        self.executor = CodeExecutor(custom_namespace=custom_namespace)
        self.executor.set_executor_ref(self.executor)
        self._setup_ui()
        self._setup_shortcuts()
        self._load_session()
        self.executor.stdout_signal.connect(self.output_widget.append_output)
        self.executor.stderr_signal.connect(self.output_widget.append_error)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
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
        central.setLayout(main_layout)

    def _load_session(self):
        """Load tabs from the saved session, or create a default tab."""
        session_data = self.session_manager.load_session()
        if session_data:
            # Restore window geometry if available
            window_info = session_data.get("window", {})
            if window_info:
                self._restore_window_geometry(window_info)
            else:
                qt.center_on_screen(self)
            
            # Load tabs
            tabs = session_data.get("tabs", [])
            if tabs:
                for tab_info in tabs:
                    editor = self.tab_widget.add_new_tab(tab_info["title"], tab_info["code"])
                    font_size = tab_info.get("font_size", 12)
                    editor.change_font_size_to(font_size)
            else:
                self.add_tab("Script 1")
        else:
            qt.center_on_screen(self)
            self.add_tab("Script 1")

    def _setup_shortcuts(self):
        ctrl_n = QShortcut(QKeySequence("Ctrl+N"), self)
        ctrl_n.activated.connect(self.tab_widget.add_new_tab)

    def execute_selected(self):
        self._save_session()
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
            self._save_session()
            self.output_widget.append_prompt(code)
            self.executor.execute(code)

    def _save_session(self):
        """Save all tabs to the session."""
        tabs = []
        for i in range(self.tab_widget.count()):
            title = self.tab_widget.tabText(i)
            code = self.get_tab_code(i)
            editor = self.tab_widget.widget(i).edit
            font_size = editor.get_font_size()
            tabs.append((title, code, font_size))
        
        # Collect window geometry
        window_info = self._get_window_geometry()
        self.session_manager.save_session(tabs, window_info)

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
        self._save_session()
        self.tab_widget.cleanup_all()
        super().closeEvent(event)

    def _get_window_geometry(self) -> dict:
        """Get current window position and size."""
        geometry = self.geometry()
        return {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
        }

    def _restore_window_geometry(self, window_info: dict):
        """Restore window position and size from saved data."""
        x = window_info.get("x")
        y = window_info.get("y")
        width = window_info.get("width", 1000)
        height = window_info.get("height", 700)
        
        if x is not None and y is not None:
            self.setGeometry(x, y, width, height)
        else:
            self.resize(width, height)
