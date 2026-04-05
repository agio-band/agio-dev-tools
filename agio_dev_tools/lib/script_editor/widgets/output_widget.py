from PySide6.QtWidgets import QTextBrowser
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor, QTextOption, QFontMetrics, QColor, QAction, QTextCharFormat

MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 30
DEFAULT_FONT_NAME = "Courier New"


class OutputWidget(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setWordWrapMode(QTextOption.NoWrap)
        
        font = QFont(DEFAULT_FONT_NAME, 12)
        font.setFixedPitch(True)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Setup tab stops
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(4 * font_metrics.horizontalAdvance(' '))
        
        self.setMouseTracking(True)
        self.setReadOnly(True)

    def get_font_size(self) -> int:
        return self.font().pointSize()

    def change_font_size(self, increase: bool):
        current_size = self.get_font_size()
        if increase:
            new_size = min(MAX_FONT_SIZE, current_size + 1)
        else:
            new_size = max(MIN_FONT_SIZE, current_size - 1)
        
        font = self.font()
        font.setPointSize(new_size)
        self.setFont(font)

    def append_output(self, text: str):
        text = text.replace('\u2029', '\n')
        
        self.moveCursor(QTextCursor.End)
        cursor = self.textCursor()
        cursor.insertBlock()
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(210, 210, 210))
        cursor.setCharFormat(fmt)
        
        lines = text.rstrip('\n').split('\n')
        for i, line in enumerate(lines):
            if i > 0:
                cursor.insertBlock()  # New line
            if line:
                cursor.insertText(line)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_prompt(self, text: str):
        text = text.replace('\u2029', '\n')
        lines = text.split('\n')
        
        self.moveCursor(QTextCursor.MoveOperation.End)
        cursor = self.textCursor()
        
        # Insert a new block first
        cursor.insertBlock()
        
        # Set gray color
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(210, 210, 210))
        cursor.setCharFormat(fmt)
        
        cursor.insertText(f">>> {lines[0]}")
        
        for line in lines[1:]:
            cursor.insertBlock()
            cursor.insertText(f"    {line}")
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_error(self, text: str):
        text = text.replace('\u2029', '\n')
        lines = text.rstrip('\n').split('\n')
        
        self.moveCursor(QTextCursor.MoveOperation.End)
        cursor = self.textCursor()
        
        cursor.insertBlock()
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(255, 100, 100))
        cursor.setCharFormat(fmt)
        
        for i, line in enumerate(lines):
            if i > 0:
                cursor.insertBlock()
            if line:
                cursor.insertText(line)
        
        cursor.insertBlock()
        reset_fmt = QTextCharFormat()
        reset_fmt.setForeground(QColor(210, 210, 210))
        cursor.setCharFormat(reset_fmt)
        
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_output(self):
        self.clear()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        
        menu.addSeparator()
        clear_action = QAction("Clear Console", self)
        clear_action.triggered.connect(self.clear_output)
        menu.addAction(clear_action)
        
        menu.exec_(event.globalPos())
        menu.deleteLater()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.change_font_size(increase=True)
            else:
                self.change_font_size(increase=False)
            event.accept()
        else:
            super().wheelEvent(event)
