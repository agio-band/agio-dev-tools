"""Line number widget for code editor."""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import (
    QPainter, QFont, QFontMetrics, QPalette, QPen, QBrush, QColor,
    QTextBlock, QMouseEvent
)


class LineNumberWidget(QWidget):
    """Line number gutter widget that displays line numbers for the code editor."""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self._padding = 12  # Extra padding for width calculation

        # Connect to editor signals for interactive updates
        self.editor.verticalScrollBar().valueChanged.connect(self.update)
        self.editor.document().blockCountChanged.connect(self.update_width)
        self.editor.cursorPositionChanged.connect(self.update)
        self.editor.selectionChanged.connect(self.update)
        
        # Connect font change signal if available (InputWidget emits this on zoom)
        if hasattr(self.editor, 'font_changed'):
            self.editor.font_changed.connect(self._on_font_changed)

        # Initial setup
        self.update_width()

    def _on_font_changed(self):
        """Handle font size change (zoom)."""
        self.update_width()
        self.update()

    def update_width(self):
        """Update widget width based on line number width."""
        line_count = self.editor.document().blockCount()
        digits = len(str(max(1, line_count)))
        # Use the editor's current font metrics for accurate width
        font = QFont(self.editor.document().defaultFont())
        fm = QFontMetrics(font)
        char_width = fm.horizontalAdvance('9')
        # Width = char_width * digits + padding (extra space for readability)
        width = char_width * digits + self._padding + 4
        width = max(width, 30)  # Minimum width
        self.setFixedWidth(width)

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks to select line."""
        if event.button() == Qt.LeftButton:
            self._select_line_at(event.pos().y())
        super().mousePressEvent(event)

    def _select_line_at(self, y_pos: int):
        """Select the line at the given Y position."""
        contents_y = self.editor.verticalScrollBar().value()
        font = QFont(self.editor.document().defaultFont())
        fm = QFontMetrics(font)
        line_height = fm.height()

        # Calculate which line was clicked
        abs_y = y_pos + contents_y
        block = self.editor.document().findBlockByLineNumber(0)
        line_number = 0

        while block.isValid():
            line_number += 1
            block_rect = self.editor.document().documentLayout().blockBoundingRect(block)
            block_top = block_rect.top()
            block_bottom = block_rect.bottom()

            if block_top <= abs_y <= block_bottom:
                # Move cursor to this line
                cursor = self.editor.textCursor()
                cursor.setPosition(block.position())
                self.editor.setTextCursor(cursor)
                self.editor.setFocus()
                break

            block = block.next()

    def paintEvent(self, event):
        """Paint line numbers."""
        painter = QPainter(self)

        # Get current font metrics
        font = QFont(self.editor.document().defaultFont())
        font_metrics = QFontMetrics(font)
        painter.setFont(font)

        # Get visible area
        contents_y = self.editor.verticalScrollBar().value()
        page_bottom = contents_y + self.editor.viewport().height()

        current_block = self.editor.textCursor().block()
        line_number = 0

        # Iterate through all blocks
        block = self.editor.document().begin()
        while block.isValid():
            line_number += 1

            # Get block position
            position = self.editor.document().documentLayout().blockBoundingRect(block).topLeft()

            # Skip if outside visible area
            if position.y() > page_bottom:
                break

            # Calculate rect for this line
            y_pos = round(position.y()) - contents_y
            line_height = font_metrics.height()
            rect = QRect(0, y_pos, self.width() - 5, line_height)

            # Highlight current line
            if block == current_block:
                bg_color = self.palette().brush(QPalette.Window).color()
                hsv = bg_color.toHsv()
                v = int(hsv.value() * 0.8) if hsv.value() > 20 else int(hsv.value() * 1.1)
                bg = QColor.fromHsv(hsv.hue(), hsv.saturation(), v)
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(bg))
                painter.drawRect(QRect(0, y_pos, self.width(), line_height))
                painter.setPen(QPen(self.palette().color(QPalette.WindowText)))

            # Draw line number
            painter.drawText(rect, int(Qt.AlignRight), str(line_number))

            block = block.next()

        painter.end()
        super().paintEvent(event)
