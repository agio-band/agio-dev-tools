"""Tab widget for managing multiple code editor tabs."""

from PySide6.QtWidgets import (
    QTabWidget, QWidget, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from .input_widget import InputWidget
from .line_number_widget import LineNumberWidget
from .completion_widget import CompletionWidget
from ..threads.completion_thread import CompletionThread


class TabContainer(QWidget):
    """Container widget for a single tab with editor and line numbers."""

    def __init__(self, parent_editor, text="", desk=None):
        super().__init__()
        self.parent_editor = parent_editor

        # Create completion thread and widget
        self.completion_thread = CompletionThread()
        self.completer = CompletionWidget(editor=None)

        # Create horizontal layout
        hbox = QHBoxLayout(self)
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)

        # Create input widget
        self.edit = InputWidget(parent_editor)

        # Wire completer to editor
        self.edit.completer = self.completer
        self.edit.completion_thread = self.completion_thread
        self.completer.editor = self.edit
        # Set editor as parent so completer is positioned relative to it
        self.completer.setParent(self.edit)

        # Connect completion thread signals
        self.completion_thread.completions_ready.connect(self.edit.on_completions_ready)

        # Start the completion thread
        self.completion_thread.start()
        
        if text:
            self.edit.append_text(text)
        
        # Create line number widget
        self.line_num = LineNumberWidget(self.edit, self)
        self.edit.verticalScrollBar().valueChanged.connect(lambda: self.line_num.update())
        self.edit.input_signal.connect(lambda: self.line_num.update())
        
        # Add widgets to layout
        hbox.addWidget(self.line_num)
        hbox.addWidget(self.edit)
        
        # Connect execute signal
        self.edit.execute_signal.connect(parent_editor.execute_selected)

    def cleanup(self):
        """Clean up resources when tab is closed."""
        if self.completion_thread:
            self.completion_thread.stop()


class TabWidget(QTabWidget):
    """Multi-tab container for code editors."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        
        # Setup tab properties
        self.setTabsClosable(True)
        self.setMovable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabBar().customContextMenuRequested.connect(self._open_menu)
        
        # Add new tab button
        new_tab_button = QPushButton("+")
        new_tab_button.setMaximumWidth(30)
        new_tab_button.setCursor(Qt.ArrowCursor)
        new_tab_button.setToolTip("Add Tab")
        new_tab_button.clicked.connect(self.add_new_tab)
        self.setCornerWidget(new_tab_button, Qt.TopLeftCorner)
        
        # Get desktop for positioning
        self.desk = QApplication.desktop() if hasattr(QApplication, 'desktop') else None
        
        # Connect signals
        self.currentChanged.connect(self._on_tab_changed)

    def _open_menu(self):
        """Open context menu for tab bar."""
        from PySide6.QtWidgets import QMenu, QAction
        from PySide6.QtGui import QCursor
        
        menu = QMenu(self)
        rename_action = QAction('Rename Current Tab', self)
        rename_action.triggered.connect(self.rename_tab)
        menu.addAction(rename_action)
        menu.exec_(QCursor.pos())

    def add_new_tab(self, name="Untitled", text=""):
        """Add a new tab and return the InputWidget."""
        container = TabContainer(self.parent_editor, text, self.desk)
        container.edit.save_signal.connect(self._save_session)
        
        # Use widget index since we haven't added it yet
        self.addTab(container, str(name))
        container.edit.moveCursor(QTextCursor.End)
        self.setCurrentIndex(self.count() - 1)
        return container.edit

    def close_tab(self, index):
        """Close tab at given index."""
        if self.count() <= 1:
            return
        
        # Get the container to clean up
        container = self.widget(index)
        
        # Check if tab has unsaved content
        text = self.get_tab_text(index)
        if text.strip():
            reply = QMessageBox.question(
                self, 'Close Tab',
                f'Close this tab without saving?\n{self.tabText(index)}',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Cleanup resources
        container.cleanup()
        self.removeTab(index)

    def rename_tab(self):
        """Rename the current tab."""
        index = self.currentIndex()
        current_name = self.tabText(index)
        
        result = QInputDialog.getText(self, 'New Name', 'Enter New Name', text=current_name)
        if result[1]:  # User clicked OK
            self.setTabText(index, result[0])

    def get_tab_text(self, index=None):
        """Get text from tab at index (or current tab if None)."""
        if index is None:
            index = self.currentIndex()
        if 0 <= index < self.count():
            return self.widget(index).edit.toPlainText()
        return ""

    def set_tab_text(self, text, index=None):
        """Set text for tab at index (or current tab if None)."""
        if index is None:
            index = self.currentIndex()
        if 0 <= index < self.count():
            self.widget(index).edit.setPlainText(text)

    def get_tab_selected_text(self):
        """Get selected text from current tab."""
        index = self.currentIndex()
        if 0 <= index < self.count():
            return self.widget(index).edit.get_selected_text()
        return ""

    def add_to_current(self, text):
        """Add text to current tab at cursor position."""
        index = self.currentIndex()
        if 0 <= index < self.count():
            self.widget(index).edit.insertPlainText(text)

    def _on_tab_changed(self, index):
        """Handle tab change - hide all completers."""
        for i in range(self.count()):
            widget = self.widget(i)
            if hasattr(widget, 'edit') and hasattr(widget.edit, 'completer'):
                if widget.edit.completer:
                    widget.edit.completer.hide()

    def current_editor(self):
        """Get the current InputWidget."""
        return self.widget(self.currentIndex()).edit

    def _save_session(self):
        """Save session signal handler (placeholder)."""
        pass

    def cleanup_all(self):
        """Clean up all tab resources. Call before closing the dialog."""
        for i in range(self.count()):
            container = self.widget(i)
            if hasattr(container, 'cleanup'):
                container.cleanup()
