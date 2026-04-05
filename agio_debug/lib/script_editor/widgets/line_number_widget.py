"""Line number widget for code editor."""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QFont, QFontMetrics, QPalette, QPen, QBrush, QColor, QTextBlock


class LineNumberWidget(QWidget):
    """Line number gutter widget that displays line numbers for the code editor."""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setMinimumWidth(30)
        self.editor.verticalScrollBar().valueChanged.connect(self.update)
        self.editor.document().blockCountChanged.connect(self.update_width)

    def update_width(self):
        """Update widget width based on line number width."""
        line_count = self.editor.document().blockCount()
        digits = len(str(max(1, line_count)))
        width = self.fontMetrics().horizontalAdvance('9') * digits + 10
        self.setFixedWidth(width)

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
