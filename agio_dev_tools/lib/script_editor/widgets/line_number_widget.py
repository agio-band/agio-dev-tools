"""Gutter widget: line numbers + fold markers column.

Geometry notes (QPlainTextEdit specifics):
``QPlainTextDocumentLayout`` anchors every block's ``blockBoundingRect`` at
(0, 0) — the Y position is not stored per block. Therefore coordinates must
be ACCUMULATED from ``firstVisibleBlock()`` (as in the canonical Qt
line-number example), starting from
``blockBoundingGeometry(firstBlock).translated(contentOffset())``.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QFont, QFontMetrics, QPalette, QPen, QBrush, QColor,
    QMouseEvent, QPolygonF, QTextCursor
)

MARKER_ZONE = 16      # width of the fold marker column
MARKER_SIZE = 4       # half-size of the triangle


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
        # fold state changes repaint the gutter via editor.update_gutter()
        editor._gutter = self
        self.update_width()

    def _on_font_changed(self):
        self.update_width()
        self.update()

    # ---------- geometry ----------

    def update_width(self):
        line_count = self.editor.document().blockCount()
        digits = len(str(max(1, line_count)))
        font = QFont(self.editor.document().defaultFont())
        fm = QFontMetrics(font)
        char_width = fm.horizontalAdvance('9')
        width = MARKER_ZONE + char_width * digits + self._padding + 4
        width = max(width, 30 + MARKER_ZONE)
        self.setFixedWidth(width)

    # ---------- block iteration (QPlainTextEdit-safe) ----------

    def _iter_visible_blocks(self, bottom_limit=None):
        """Yield (block, top, height) in viewport coordinates.

        ``top`` is accumulated from the first visible block because
        QPlainTextEdit's layout anchors block rects at (0, 0).
        """
        editor = self.editor
        block = editor.firstVisibleBlock()
        if not block.isValid():
            return
        top = editor.blockBoundingGeometry(block).translated(editor.contentOffset()).top()
        while block.isValid():
            height = editor.blockBoundingRect(block).height()
            if block.isVisible():
                yield block, top, height
            top += height
            if bottom_limit is not None and top > bottom_limit:
                return
            block = block.next()

    # ---------- mouse ----------

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            y = event.position().y()
            x = event.position().x()
            for block, top, height in self._iter_visible_blocks(bottom_limit=self.height() + 1):
                if top <= y < top + height:
                    if x < MARKER_ZONE:
                        fm = self.editor.fold_manager
                        if fm.is_folded(block) or fm.is_foldable(block):
                            fm.toggle_fold(block)
                            return
                    self._select_line_at(block)
                    return
        super().mousePressEvent(event)

    def _select_line_at(self, block):
        cursor = self.editor.textCursor()
        cursor.setPosition(block.position())
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    # ---------- painting ----------

    def paintEvent(self, event):
        painter = QPainter(self)

        font = QFont(self.editor.document().defaultFont())
        font_metrics = QFontMetrics(font)
        painter.setFont(font)

        fold_manager = self.editor.fold_manager
        current_block = self.editor.textCursor().block()
        window_text = self.palette().color(QPalette.ColorRole.WindowText)

        for block, top, height in self._iter_visible_blocks(bottom_limit=self.height() + 1):
            if height <= 0:
                continue
            top = round(top)
            height = round(height)

            # highlight background for the line with the cursor
            if block == current_block:
                bg_color = self.palette().brush(QPalette.ColorRole.Window).color()
                hsv = bg_color.toHsv()
                v = int(hsv.value() * 0.8) if hsv.value() > 20 else int(hsv.value() * 1.1)
                bg = QColor.fromHsv(hsv.hue(), hsv.saturation(), v)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(bg))
                painter.drawRect(QRect(0, top, self.width(), height))
                painter.setPen(QPen(self.palette().color(QPalette.ColorRole.WindowText)))

            # line number = real document line (1-based), hidden lines are not drawn
            rect = QRect(MARKER_ZONE, top, self.width() - MARKER_ZONE - 5, height)
            painter.drawText(rect, int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
                             str(block.blockNumber() + 1))

            # fold marker
            folded = fold_manager.is_folded(block)
            if folded or fold_manager.is_foldable(block):
                cy = top + height / 2.0
                self._draw_fold_marker(painter, MARKER_ZONE / 2.0, cy,
                                       folded, window_text,
                                       highlighted=(block == current_block))

        painter.end()
        super().paintEvent(event)

    def _draw_fold_marker(self, painter: QPainter, cx: float, cy: float,
                          folded: bool, color: QColor, highlighted: bool = False):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if highlighted:
            # subtle frame around the marker of the current line
            painter.setPen(QPen(QColor(120, 120, 120, 160), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                QRectF(cx - MARKER_ZONE / 2.0 + 2, cy - MARKER_SIZE - 2,
                       MARKER_ZONE - 4, MARKER_SIZE * 2 + 4), 2, 2)

        pen_color = QColor(color)
        pen_color.setAlpha(190)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(pen_color))
        s = MARKER_SIZE
        if folded:
            # right-pointing triangle ▸
            pts = [QPointF(cx - s * 0.6, cy - s), QPointF(cx - s * 0.6, cy + s), QPointF(cx + s * 0.8, cy)]
        else:
            # down-pointing triangle ▾
            pts = [QPointF(cx - s, cy - s * 0.6), QPointF(cx + s, cy - s * 0.6), QPointF(cx, cy + s * 0.8)]
        painter.drawPolygon(QPolygonF(pts))
        painter.restore()
