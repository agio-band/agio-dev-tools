"""Completion widget for displaying autocomplete suggestions.

Uses a plain widget (not a separate window) to avoid focus issues.
"""

from PySide6.QtWidgets import QListWidget, QListWidgetItem, QAbstractItemView, QFrame
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QFontMetrics


class CompletionWidget(QListWidget):
    """Autocomplete popup widget for code completion suggestions."""

    def __init__(self, parent=None, editor=None):
        super().__init__(parent)
        self.editor = editor
        self.line_height = 20

        # Start hidden
        self.hide()

        # No window flags - this is a regular child widget
        # This prevents focus stealing issues
        self.setFrameStyle(QFrame.NoFrame)

        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFont(QFont("Courier New", 10))

        self.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                color: #d0d0d0;
                border: 1px solid #555555;
                outline: none;
            }
            QListWidget::item {
                padding: 2px 8px;
                min-height: 18px;
            }
            QListWidget::item:selected {
                background-color: #5a5a5a;
                color: #ffffff;
            }
            QListWidget::item:alternate {
                background-color: #333333;
            }
            QListWidget::item:hover {
                background-color: #4a4a4a;
            }
        """)

        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemActivated.connect(self._on_item_activated)
        self._completions = []

    def _on_item_double_clicked(self, item):
        self._apply_completion(item)

    def _on_item_activated(self, item):
        self._apply_completion(item)

    def _apply_completion(self, item):
        if item and self.editor:
            comp = item.data(Qt.UserRole)
            if comp:
                self.editor.apply_completion(comp)
        self.hide()

    def update_completions(self, completions=None):
        self.clear()
        self._completions = []

        if completions:
            self._completions = completions
            for comp in completions:
                item = QListWidgetItem(comp.name)
                item.setData(Qt.UserRole, comp)
                type_icon = {'function': 'ƒ', 'method': 'ƒ', 'class': 'C', 'module': 'M',
                             'keyword': 'K', 'instance': 'I', 'param': 'P', 'property': '@'}
                icon = type_icon.get(comp.type, '•')
                item.setText(f"{comp.name}  {icon}")
                tooltip = comp.signature or comp.docstring
                if tooltip:
                    item.setToolTip(tooltip[:200])
                self.addItem(item)

            self._resize_to_content()
            self.setCurrentRow(0)
            self.show()
        else:
            self.hide()

    def _resize_to_content(self):
        font = QFont("Courier New", 10)
        fm = QFontMetrics(font)
        max_width = 200
        for comp in self._completions:
            w = fm.horizontalAdvance(f"{comp.name}  ƒ  ") + 20
            max_width = max(max_width, w)
        max_width = min(max_width, 500)
        item_count = min(self.count(), 12)
        height = item_count * self.line_height + 4
        self.resize(max_width, height)

    def navigate(self, key):
        if not self.isVisible():
            return
        current_row = self.currentRow()
        count = self.count()
        if count == 0:
            return
        if key == Qt.Key_Up:
            self.setCurrentRow((current_row - 1) % count)
        elif key == Qt.Key_Down:
            self.setCurrentRow((current_row + 1) % count)
        elif key == Qt.Key_PageUp:
            self.setCurrentRow(max(0, current_row - 5))
        elif key == Qt.Key_PageDown:
            self.setCurrentRow(min(count - 1, current_row + 5))
        self.scrollToItem(self.currentItem())

    def keyPressEvent(self, event):
        """Handle key events without stealing focus from editor."""
        key = event.key()

        # If not visible, ignore completely
        if not self.isVisible():
            event.ignore()
            return

        if key == Qt.Key_Escape:
            self.hide()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            self._apply_completion(self.currentItem())
        elif key == Qt.Key_Tab:
            self._apply_completion(self.currentItem())
        elif key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
            self.navigate(key)
        elif key == Qt.Key_Backspace:
            self.hide()
        else:
            # For all other keys, hide and let editor handle them
            self.hide()

    def show_at(self, pos: QPoint):
        if self.width() == 0 or self.height() == 0:
            self._resize_to_content()

        # Position relative to parent
        self.move(pos)
        self.show()
        self.raise_()

        # Ensure editor keeps focus
        if self.editor:
            self.editor.setFocus()
