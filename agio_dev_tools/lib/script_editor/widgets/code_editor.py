"""Code editor widget based on QPlainTextEdit.

Replaces the old QTextEdit-based InputWidget. QPlainTextEdit together with
hidden text blocks (see folding.py) provides code folding, which QTextEdit
could not reliably support, and is generally faster for large documents.

The whole behavior of the previous InputWidget (indentation, Ctrl+Enter
execution, comment toggle, font zoom, completer hooks, ...) is preserved.
"""

import re

from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtGui import (
    QFont, QFontMetrics, QKeyEvent, QTextCursor
)
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMenu
from PySide6.QtWidgets import QPlainTextEdit

from .syntax.highlighter import PythonHighlighter
from .folding import FoldManager

INDENT_LEN = 4
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 30
DEFAULT_FONT_NAME = "Courier New"
COMPLETION_DEBOUNCE_MS = 150  # pause before sending a jedi request


class CodeEditor(QPlainTextEdit):
    execute_signal = Signal()
    save_signal = Signal()
    input_signal = Signal()
    font_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent

        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._setup_font()

        font_metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopDistance(INDENT_LEN * font_metrics.horizontalAdvance(' '))

        self.highlighter = PythonHighlighter(self.document())
        self.fold_manager = FoldManager(self)

        self.completer = None
        self.completion_thread = None
        self._request_id = 0

        # debounce timer: jedi requests are sent only after a short typing pause
        self._completion_timer = QTimer(self)
        self._completion_timer.setSingleShot(True)
        self._completion_timer.setInterval(COMPLETION_DEBOUNCE_MS)
        self._completion_timer.timeout.connect(self._send_completion_request)

        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.document().contentsChange.connect(self._on_contents_change)
        self.cursorPositionChanged.connect(self._on_cursor_moved)
        self.verticalScrollBar().valueChanged.connect(self._on_scrolled)

    def _on_scrolled(self):
        if self.completer and self.completer.isVisible():
            self.completer.hide()

    # ---------- folding ----------

    def fold_all(self):
        self.fold_manager.fold_all()

    def unfold_all(self):
        self.fold_manager.unfold_all()

    def toggle_fold_current(self):
        self.fold_manager.toggle_fold(self.textCursor().block())

    def fold_current(self):
        self.fold_manager.fold(self.textCursor().block())

    def unfold_current(self):
        self.fold_manager.unfold(self.textCursor().block())

    def update_gutter(self):
        """Called by FoldManager after visibility changes."""
        self.line_num_widget_updated()

    def line_num_widget_updated(self):
        # LineNumberWidget connects to editor signals; give it a poke
        gutter = getattr(self, '_gutter', None)
        if gutter is not None:
            gutter.update()

    def _on_contents_change(self, *args):
        self.fold_manager.on_contents_change(*args)

    def _on_cursor_moved(self):
        block = self.textCursor().block()
        if not block.isVisible():
            self.fold_manager.unfold_around(block)
        self._gutter_update_safe()

    def _gutter_update_safe(self):
        gutter = getattr(self, '_gutter', None)
        if gutter is not None:
            gutter.update()

    # ---------- font ----------

    def _setup_font(self):
        font = QFont(DEFAULT_FONT_NAME, 12)
        font.setFixedPitch(True)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.document().setDefaultFont(font)

    def get_font_size(self) -> int:
        return self.document().defaultFont().pointSize()

    def change_font_size_to(self, size: int):
        font = self.document().defaultFont()
        font.setPointSize(size)
        self.document().setDefaultFont(font)
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(INDENT_LEN * font_metrics.horizontalAdvance(' '))
        self.font_changed.emit()

    def change_font_size(self, increase: bool):
        current_size = self.get_font_size()
        new_size = min(MAX_FONT_SIZE, current_size + 1) if increase else max(MIN_FONT_SIZE, current_size - 1)
        font = self.document().defaultFont()
        font.setPointSize(new_size)
        self.document().setDefaultFont(font)
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(INDENT_LEN * font_metrics.horizontalAdvance(' '))
        self.font_changed.emit()

    # ---------- indentation ----------

    def get_current_indent(self) -> str:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        line = cursor.selectedText()
        indent = ''
        if line.strip():
            match = re.match(r'^(\s*)', line)
            if match:
                indent = match.group(0)
        if line.rstrip().endswith(':'):
            indent += ' ' * INDENT_LEN
        return indent

    def insert_tab(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            self._indent_selected(increase=True)
        else:
            self.insertPlainText(' ' * INDENT_LEN)

    def insert_backtab(self):
        self._indent_selected(increase=False)

    def _indent_selected(self, increase: bool):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        self._select_full_lines(cursor)
        start = cursor.selectionStart()
        text = cursor.selectedText()
        lines = text.split('\u2029')
        if increase:
            new_lines = [' ' * INDENT_LEN + line for line in lines]
        else:
            new_lines = []
            for line in lines:
                spaces_to_remove = min(INDENT_LEN, len(line) - len(line.lstrip(' ')))
                new_lines.append(line[spaces_to_remove:] if line.startswith(' ' * spaces_to_remove) else line)
        new_text = '\n'.join(new_lines)
        cursor.removeSelectedText()
        cursor.insertText(new_text)
        cursor.setPosition(start, QTextCursor.MoveMode.MoveAnchor)
        cursor.setPosition(start + len(new_text), QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)

    def _select_full_lines(self, cursor):
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
        self.setTextCursor(cursor)

    # ---------- events ----------

    def keyPressEvent(self, event: QKeyEvent):
        self.input_signal.emit()
        key = event.key()
        modifiers = event.modifiers()

        # folding shortcuts
        if modifiers == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
            if key == Qt.Key.Key_Minus:
                self.fold_all()
                event.accept()
                return
            if key in (Qt.Key.Key_Equal, Qt.Key.Key_Plus):
                self.unfold_all()
                event.accept()
                return

        if key == Qt.Key.Key_Tab:
            if self.completer and self.completer.isVisible():
                current_item = self.completer.currentItem()
                if current_item:
                    self.completer.apply_completion(current_item)
                event.accept()
                return
            self.insert_tab()
            event.accept()
            return

        if key == Qt.Key.Key_Backtab:
            if self.completer:
                self.completer.hide()
            self.insert_backtab()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.completer and self.completer.isVisible():
                if modifiers == Qt.KeyboardModifier.NoModifier:
                    self.completer.apply_completion(self.completer.currentItem())
                    event.accept()
                    return
            if modifiers == Qt.KeyboardModifier.NoModifier:
                indent = self.get_current_indent()
                super().keyPressEvent(event)
                if indent:
                    cursor = self.textCursor()
                    cursor.insertText(indent)
                    self.setTextCursor(cursor)
                event.accept()
                return
            if modifiers == Qt.KeyboardModifier.ShiftModifier:
                event.accept()
                return

        if modifiers == Qt.KeyboardModifier.ControlModifier and key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.completer:
                self.completer.hide()
            self.execute_signal.emit()
            return

        if key == Qt.Key.Key_Backspace:
            if self.completer:
                self.completer.hide()
            cursor = self.textCursor()
            if cursor.positionInBlock() >= INDENT_LEN:
                cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor, INDENT_LEN)
                selected = cursor.selectedText()
                if selected == ' ' * INDENT_LEN:
                    cursor.removeSelectedText()
                    event.accept()
                    return
            super().keyPressEvent(event)
            return

        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_D:
            if self.completer:
                self.completer.hide()
            self._duplicate_line_or_selection()
            return

        if modifiers == Qt.KeyboardModifier.AltModifier and key == Qt.Key.Key_Q:
            if self.completer:
                self.completer.hide()
            self._toggle_comment()
            return

        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Slash:
            if self.completer:
                self.completer.hide()
            self._toggle_comment()
            event.accept()
            return

        if key == Qt.Key.Key_Escape:
            if self.completer and self.completer.isVisible():
                self.completer.hide()
                event.accept()
                return

        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
            self._paste_plain_text()
            event.accept()
            return

        if modifiers == Qt.KeyboardModifier.ShiftModifier and key == Qt.Key.Key_Insert:
            self._paste_plain_text()
            event.accept()
            return

        if key in (Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_PageUp, Qt.Key.Key_PageDown):
            if self.completer and self.completer.isVisible():
                self.completer.navigate(key)
                event.accept()
                return

        super().keyPressEvent(event)

        if event.text() and modifiers in (Qt.KeyboardModifier.NoModifier, Qt.KeyboardModifier.ShiftModifier):
            self._trigger_completion()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if self.completer:
                self.completer.hide()
            if event.angleDelta().y() > 0:
                self.change_font_size(increase=True)
            else:
                self.change_font_size(increase=False)
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._gutter_update_safe()

    # ---------- editing helpers ----------

    def _duplicate_line_or_selection(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace('\u2029', '\n')
            end = cursor.selectionEnd()
            cursor.setPosition(end)
            cursor.insertText(text)
            cursor.setPosition(end, QTextCursor.MoveMode.MoveAnchor)
            cursor.setPosition(end + len(text), QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            line = cursor.selectedText()
            cursor.clearSelection()
            cursor.insertText('\n' + line)
            self.setTextCursor(cursor)

    def _toggle_comment(self):
        cursor = self.textCursor()
        self._select_full_lines(cursor)
        text = cursor.selectedText()
        lines = text.replace('\u2029', '\n').split('\n')
        all_commented = all(line.lstrip().startswith('#') for line in lines if line.strip())
        if all_commented:
            new_lines = []
            for line in lines:
                stripped = line.lstrip()
                if stripped.startswith('#'):
                    idx = line.index('#')
                    rest = line[idx+1:]
                    if rest.startswith(' '):
                        rest = rest[1:]
                    new_lines.append(line[:idx] + rest)
                else:
                    new_lines.append(line)
        else:
            new_lines = ['#' + line for line in lines]
        new_text = '\n'.join(new_lines)
        cursor.removeSelectedText()
        cursor.insertText(new_text)
        self.setTextCursor(cursor)

    def _paste_plain_text(self):
        text = QApplication.clipboard().text()
        self.insertPlainText(text)

    def paste(self):
        self._paste_plain_text()

    # ---------- context menu ----------

    def _show_context_menu(self, pos):
        menu = QMenu(self)

        fm = self.fold_manager
        cursor_block = self.textCursor().block()
        if fm.is_folded(cursor_block):
            fold_action = QAction("Unfold Current", self)
            fold_action.triggered.connect(self.unfold_current)
            menu.addAction(fold_action)
        elif fm.is_foldable(cursor_block):
            fold_action = QAction("Fold Current", self)
            fold_action.triggered.connect(self.fold_current)
            menu.addAction(fold_action)

        fold_all_action = QAction("Fold All", self)
        fold_all_action.setShortcut(QKeySequence("Ctrl+Shift+-"))
        fold_all_action.triggered.connect(self.fold_all)
        menu.addAction(fold_all_action)

        unfold_all_action = QAction("Unfold All", self)
        unfold_all_action.setShortcut(QKeySequence("Ctrl+Shift+="))
        unfold_all_action.triggered.connect(self.unfold_all)
        menu.addAction(unfold_all_action)

        menu.addSeparator()

        comment_action = QAction("Toggle Comment", self)
        comment_action.setShortcut(QKeySequence("Ctrl+/"))
        comment_action.triggered.connect(self._toggle_comment)
        menu.addAction(comment_action)

        menu.addSeparator()

        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)

        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self._paste_plain_text)

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.selectAll)

        menu.addAction(copy_action)
        menu.addAction(paste_action)
        menu.addAction(select_all_action)
        menu.exec(self.mapToGlobal(pos))

    # ---------- text access ----------

    def get_selected_text(self) -> str:
        cursor = self.textCursor()
        return cursor.selectedText().replace('\u2029', '\n')

    def append_text(self, text: str):
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.MoveOperation.End)

    # ---------- completion hooks (active once completer is wired by TabContainer) ----------

    def _trigger_completion(self):
        """Called after a printable keypress — decides whether a jedi request
        makes sense at the cursor position and (re)starts the debounce timer."""
        if not self.completion_thread or not self.completer:
            return

        cursor = self.textCursor()
        pos = cursor.position()
        text = self.toPlainText()

        if text and 0 < pos <= len(text):
            char_before = text[pos - 1]
            if char_before.isalnum() or char_before in '_.':
                self._completion_timer.start()  # restart debounce on each keystroke
                return
        if self.completer:
            self.completer.hide()

    def _send_completion_request(self):
        """Debounce timeout fired — actually send the request to the worker thread."""
        if not self.completion_thread or not self.completer:
            return
        if self.isReadOnly() or not self.hasFocus():
            return

        text = self.toPlainText()
        cursor = self.textCursor()
        pos = cursor.position()
        if not text or not (0 < pos <= len(text)):
            self.completer.hide()
            return

        self._request_id += 1
        self.completion_thread.request_completions(
            text, cursor.blockNumber() + 1, cursor.columnNumber(), self._request_id
        )

    def on_completions_ready(self, completions, request_id):
        if not self.completer:
            return
        if request_id != self._request_id:
            return  # stale result — newer request already pending/served
        if not self.hasFocus():
            self.completer.hide()
            return
        if completions:
            self.completer.update_completions(completions)
            self._move_completer()
        else:
            self.completer.hide()

    def _move_completer(self):
        if not self.completer:
            return
        self.completer.show_at(self.cursorRect())

    def apply_completion(self, completion):
        cursor = self.textCursor()
        pos = cursor.position()

        # Get text of the current block (line)
        block = cursor.block()
        line_text = block.text()
        col = cursor.columnNumber()

        # Find start of word before cursor (scan backwards in this line)
        start = col
        while start > 0:
            ch = line_text[start - 1]
            if not (ch.isalnum() or ch == '_'):
                break
            start -= 1

        # Select only the partial word and replace it
        cursor.setPosition(block.position() + start)
        cursor.setPosition(pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()

        insert_text = completion.name
        is_import_line = line_text.lstrip().startswith(('import ', 'from '))
        if hasattr(completion, 'type') and completion.type in ('function', 'method') and not is_import_line:
            insert_text = completion.name + '()'

        cursor.insertText(insert_text)

        if hasattr(completion, 'type') and completion.type in ('function', 'method') and not is_import_line:
            cursor.movePosition(QTextCursor.MoveOperation.Left)

        self.setTextCursor(cursor)
        self.setFocus()

    def focusOutEvent(self, event):
        if self.completer:
            self.completer.hide()
        super().focusOutEvent(event)
