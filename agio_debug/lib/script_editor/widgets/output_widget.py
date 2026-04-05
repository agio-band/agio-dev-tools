"""Console output widget for displaying execution results."""

from PySide6.QtWidgets import QTextBrowser
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor, QTextOption, QFontMetrics, QColor, QAction, QTextCharFormat

MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 30
DEFAULT_FONT_NAME = "Courier New"


class OutputWidget(QTextBrowser):
    """Output widget for displaying console output with font scaling support."""

    def __init__(self):
        super().__init__()
        self.setWordWrapMode(QTextOption.NoWrap)
        
        # Setup font
        font = QFont(DEFAULT_FONT_NAME, 12)
        font.setFixedPitch(True)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        
        # Setup tab stops
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(4 * font_metrics.horizontalAdvance(' '))
        
        self.setMouseTracking(True)
        self.setReadOnly(True)

    def get_font_size(self) -> int:
        """Get current font size."""
        return self.font().pointSize()

    def change_font_size(self, increase: bool):
        """Change font size up or down."""
        current_size = self.get_font_size()
        if increase:
            new_size = min(MAX_FONT_SIZE, current_size + 1)
        else:
            new_size = max(MIN_FONT_SIZE, current_size - 1)
        
        font = self.font()
        font.setPointSize(new_size)
        self.setFont(font)

    def append_output(self, text: str):
        """Append output text to the console (normal gray color)."""
        # Replace Qt paragraph separator
        text = text.replace('\u2029', '\n')
        
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        
        # Insert a new block first (ensure we start on a new line)
        cursor.insertBlock()
        
        # Set gray color for output
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(210, 210, 210))
        cursor.setCharFormat(fmt)
        
        # Insert each line
        lines = text.rstrip('\n').split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                cursor.insertBlock()  # New line
            if line:
                cursor.insertText(line)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_prompt(self, text: str):
        """Append prompt text (e.g., '>>> code')."""
        # Replace Qt paragraph separator and format
        text = text.replace('\u2029', '\n')
        lines = text.split('\n')
        
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        
        # Insert a new block first
        cursor.insertBlock()
        
        # Set gray color
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(210, 210, 210))
        cursor.setCharFormat(fmt)
        
        # First line gets >>> prefix
        cursor.insertText(f">>> {lines[0]}")
        
        # Remaining lines are indented continuation
        for line in lines[1:]:
            cursor.insertBlock()
            cursor.insertText(f"    {line}")
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_error(self, text: str):
        """Append error text with red color formatting, then reset to gray."""
        # Replace Qt paragraph separator
        text = text.replace('\u2029', '\n')
        lines = text.rstrip('\n').split('\n')
        
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        
        # Insert a new block first (ensure we're on a new line)
        cursor.insertBlock()
        
        # Set red color for error
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(255, 100, 100))
        cursor.setCharFormat(fmt)
        
        # Append each error line in red
        for i, line in enumerate(lines):
            if i > 0:
                cursor.insertBlock()
            if line:
                cursor.insertText(line)
        
        # Insert a new block after error and reset to gray
        cursor.insertBlock()
        reset_fmt = QTextCharFormat()
        reset_fmt.setForeground(QColor(210, 210, 210))
        cursor.setCharFormat(reset_fmt)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_output(self):
        """Clear all output."""
        self.clear()

    def contextMenuEvent(self, event):
        """Show context menu with Clear option added to default menu."""
        # Get the default context menu
        menu = self.createStandardContextMenu()
        
        # Add separator and Clear action
        menu.addSeparator()
        clear_action = QAction("Clear Console", self)
        clear_action.triggered.connect(self.clear_output)
        menu.addAction(clear_action)
        
        menu.exec_(event.globalPos())
        menu.deleteLater()

    def wheelEvent(self, event):
        """Handle mouse wheel for font size changes."""
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.change_font_size(increase=True)
            else:
                self.change_font_size(increase=False)
            event.accept()
        else:
            super().wheelEvent(event)
