from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QTabWidget, QWidget, QHBoxLayout,
    QPushButton, QInputDialog, QApplication
)
from PySide6.QtWidgets import QMenu
from PySide6.QtGui import QCursor, QAction
from .completion_widget import CompletionWidget
from .input_widget import InputWidget
from .line_number_widget import LineNumberWidget
from ..threads.completion_thread import CompletionWorker


class TabContainer(QWidget):
    def __init__(self, parent_editor, text="", desk=None):
        super().__init__()
        self.parent_editor = parent_editor
        self.completion_thread = CompletionWorker()
        self.completer = CompletionWidget(editor=None)
        hbox = QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.edit = InputWidget(parent_editor)
        self.edit.completer = self.completer
        self.edit.completion_thread = self.completion_thread
        self.completer.editor = self.edit
        # parent the popup to the viewport: its coordinates then match
        # cursorRect() directly (which is viewport-relative)
        self.completer.setParent(self.edit.viewport())
        self.completion_thread.results_ready.connect(self.edit.on_completions_ready)
        self.completion_thread.start()
        if text:
            self.edit.append_text(text)
        self.line_num = LineNumberWidget(self.edit, self)
        self.edit.verticalScrollBar().valueChanged.connect(lambda: self.line_num.update())
        self.edit.input_signal.connect(lambda: self.line_num.update())
        hbox.addWidget(self.line_num)
        hbox.addWidget(self.edit)
        self.edit.execute_signal.connect(parent_editor.execute_selected)

    def cleanup(self):
        if self.completion_thread:
            self.completion_thread.stop()
            self.completion_thread = None


class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.tabBar().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._open_menu)
        new_tab_button = QPushButton("+")
        new_tab_button.setMaximumWidth(30)
        new_tab_button.setCursor(Qt.CursorShape.ArrowCursor)
        new_tab_button.setToolTip("Add Tab")
        new_tab_button.clicked.connect(self.add_new_tab)
        self.setCornerWidget(new_tab_button, Qt.Corner.TopLeftCorner)
        
        self.desk = QApplication.desktop() if hasattr(QApplication, 'desktop') else None
        
        self.currentChanged.connect(self._on_tab_changed)

    def _open_menu(self):
        """Open context menu for tab bar."""

        
        menu = QMenu(self)
        rename_action = QAction('Rename Current Tab', self)
        rename_action.triggered.connect(self.rename_tab)
        menu.addAction(rename_action)
        menu.exec_(QCursor.pos())

    def add_new_tab(self, name="Untitled", text=""):
        container = TabContainer(self.parent_editor, text, self.desk)
        self.addTab(container, str(name))
        container.edit.moveCursor(QTextCursor.End)
        self.setCurrentIndex(self.count() - 1)
        # Save session when a new tab is added
        if hasattr(self.parent_editor, '_save_session'):
            self.parent_editor._save_session()
        return container.edit

    def close_tab(self, index):
        if self.count() <= 1:
            return
        container: TabContainer = self.widget(index)
        container.cleanup()
        self.removeTab(index)
        # Notify parent dialog to save session after tab removal
        if hasattr(self.parent_editor, '_save_session'):
            self.parent_editor._save_session()

    def rename_tab(self):
        index = self.currentIndex()
        current_name = self.tabText(index)
        result = QInputDialog.getText(self, 'New Name', 'Enter New Name', text=current_name)
        if result[1]:
            self.setTabText(index, result[0])
            if hasattr(self.parent_editor, '_save_session'):
                self.parent_editor._save_session()

    def get_tab_text(self, index=None):
        if index is None:
            index = self.currentIndex()
        if 0 <= index < self.count():
            return self.widget(index).edit.toPlainText()
        return ""

    def set_tab_text(self, text, index=None):
        if index is None:
            index = self.currentIndex()
        if 0 <= index < self.count():
            self.widget(index).edit.setPlainText(text)

    def get_tab_selected_text(self):
        index = self.currentIndex()
        if 0 <= index < self.count():
            return self.widget(index).edit.get_selected_text()
        return ""

    def add_to_current(self, text):
        index = self.currentIndex()
        if 0 <= index < self.count():
            self.widget(index).edit.insertPlainText(text)

    def _on_tab_changed(self, index):
        for i in range(self.count()):
            widget = self.widget(i)
            if hasattr(widget, 'edit') and hasattr(widget.edit, 'completer'):
                if widget.edit.completer:
                    widget.edit.completer.hide()
        # Save session on tab switch
        if hasattr(self.parent_editor, '_save_session'):
            self.parent_editor._save_session()

    def current_editor(self):
        return self.widget(self.currentIndex()).edit

    def cleanup_all(self):
        for i in range(self.count()):
            container = self.widget(i)
            if hasattr(container, 'cleanup'):
                container.cleanup()
