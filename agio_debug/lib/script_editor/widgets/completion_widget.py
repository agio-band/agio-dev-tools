"""Completion widget for displaying autocomplete suggestions."""

from PySide6.QtWidgets import QListWidget, QListWidgetItem
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QFontMetrics


class CompletionWidget(QListWidget):
    """Autocomplete popup widget for code completion suggestions."""

    def __init__(self, parent=None, editor=None):
        super().__init__(parent)
        self.editor = editor
        self.setAlternatingRowColors(True)
        self.line_height = 18
        
        # Set window flags for popup behavior
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # Connect signals
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, item):
        """Handle double-click on completion item."""
        if item:
            completion_text = item.data(Qt.UserRole)
            self._insert_completion(completion_text)
            self.hide()

    def update_completion_list(self, completions=None):
        """Update the completion list with new items."""
        self.clear()
        
        if completions:
            self.show()
            
            # Add items to list
            for comp in completions:
                item = QListWidgetItem(comp.name)
                item.setData(Qt.UserRole, comp.complete)
                
                # Style based on type
                if comp.type in ('function', 'method'):
                    item.setToolTip(comp.signature or comp.name)
                elif comp.docstring:
                    item.setToolTip(comp.docstring)
                
                self.addItem(item)
            
            # Calculate width based on longest item
            font = QFont("monospace", self.line_height)
            fm = QFontMetrics(font)
            max_width = 250
            if completions:
                max_name_len = max(len(c.name) for c in completions)
                width = fm.horizontalAdvance(' ') * max_name_len + 40
                max_width = max(max_width, width)
            
            self.resize(max_width, 250)
            self.setCurrentRow(0)
        else:
            self.hide()

    def apply_current_completion(self):
        """Apply the currently selected completion."""
        items = self.selectedItems()
        if items:
            completion_text = items[0].data(Qt.UserRole)
            self._insert_completion(completion_text)
        self.hide()

    def _insert_completion(self, text):
        """Insert completion text into the editor."""
        if self.editor:
            self.editor.insertText(text)

    def navigate(self, key):
        """Navigate through completion list."""
        items = self.selectedItems()
        if not items:
            return
        
        current_row = self.row(items[0])
        
        if key == Qt.Key_Up:
            if current_row == 0:
                self.setCurrentRow(self.count() - 1)
            else:
                self.setCurrentRow(current_row - 1)
        elif key == Qt.Key_Down:
            if current_row + 1 == self.count():
                self.setCurrentRow(0)
            else:
                self.setCurrentRow(current_row + 1)

    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.editor:
                self.editor.setFocus()
            self.apply_current_completion()
            return
        elif event.key() == Qt.Key_Up:
            sel = self.selectedItems()
            if sel:
                i = self.row(sel[0])
                if i == 0:
                    super().keyPressEvent(event)
                    self.setCurrentRow(self.count() - 1)
                    return
        elif event.key() == Qt.Key_Down:
            sel = self.selectedItems()
            if sel:
                i = self.row(sel[0])
                if i + 1 == self.count():
                    super().keyPressEvent(event)
                    self.setCurrentRow(0)
                    return
        elif event.key() == Qt.Key_Backspace:
            if self.editor:
                self.editor.setFocus()
                self.editor.activateWindow()
        elif event.text():
            if self.editor:
                self.editor.keyPressEvent(event)
            return
        
        super().keyPressEvent(event)

    def request_completions(self, text, line, column):
        """Request completions from the editor."""
        # This will be called by InputWidget
        # The actual completion request should be handled by a thread
        pass
