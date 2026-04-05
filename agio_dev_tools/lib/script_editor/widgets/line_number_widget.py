from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import (
    QPainter, QFont, QFontMetrics, QPalette, QPen, QBrush, QColor,
    QTextBlock, QMouseEvent
)


class LineNumberWidget(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self._padding = 12
        self.editor.verticalScrollBar().valueChanged.connect(self.update)
        self.editor.document().blockCountChanged.connect(self.update_width)
        self.editor.cursorPositionChanged.connect(self.update)
        self.editor.selectionChanged.connect(self.update)
        self.editor.font_changed.connect(self._on_font_changed)
        self.update_width()

    def _on_font_changed(self):
        self.update_width()
        self.update()

    def update_width(self):
        line_count = self.editor.document().blockCount()
        digits = len(str(max(1, line_count)))
        font = QFont(self.editor.document().defaultFont())
        fm = QFontMetrics(font)
        char_width = fm.horizontalAdvance('9')
        width = char_width * digits + self._padding + 4
        width = max(width, 30)
        self.setFixedWidth(width)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._select_line_at(event.pos().y())
        super().mousePressEvent(event)

    def _select_line_at(self, y_pos: int):
        contents_y = self.editor.verticalScrollBar().value()
        font = QFont(self.editor.document().defaultFont())
        fm = QFontMetrics(font)
        # line_height = fm.height()
        abs_y = y_pos + contents_y
        block = self.editor.document().findBlockByLineNumber(0)
        line_number = 0

        while block.isValid():
            line_number += 1
            block_rect = self.editor.document().documentLayout().blockBoundingRect(block)
            block_top = block_rect.top()
            block_bottom = block_rect.bottom()

            if block_top <= abs_y <= block_bottom:
                cursor = self.editor.textCursor()
                cursor.setPosition(block.position())
                self.editor.setTextCursor(cursor)
                self.editor.setFocus()
                break

            block = block.next()

    def paintEvent(self, event):
        painter = QPainter(self)

        font = QFont(self.editor.document().defaultFont())
        font_metrics = QFontMetrics(font)
        painter.setFont(font)

        contents_y = self.editor.verticalScrollBar().value()
        page_bottom = contents_y + self.editor.viewport().height()

        current_block = self.editor.textCursor().block()
        line_number = 0

        block = self.editor.document().begin()
        while block.isValid():
            line_number += 1
            position = self.editor.document().documentLayout().blockBoundingRect(block).topLeft()
            if position.y() > page_bottom:
                break
            y_pos = round(position.y()) - contents_y
            line_height = font_metrics.height()
            rect = QRect(0, y_pos, self.width() - 5, line_height)

            if block == current_block:
                bg_color = self.palette().brush(QPalette.ColorRole.Window).color()
                hsv = bg_color.toHsv()
                v = int(hsv.value() * 0.8) if hsv.value() > 20 else int(hsv.value() * 1.1)
                bg = QColor.fromHsv(hsv.hue(), hsv.saturation(), v)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(bg))
                painter.drawRect(QRect(0, y_pos, self.width(), line_height))
                painter.setPen(QPen(self.palette().color(QPalette.ColorRole.WindowText)))

            # Draw line number
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignRight), str(line_number))

            block = block.next()

        painter.end()
        super().paintEvent(event)
