"""Code input editor widget with syntax highlighting and completions."""

import re
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import (
    QFont, QTextOption, QFontMetrics, QKeyEvent, QTextCursor
)

from .syntax.highlighter import PythonHighlighter

INDENT_LEN = 4
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 30
DEFAULT_FONT_NAME = "Courier New"


class InputWidget(QTextEdit):
    """Code input editor with syntax highlighting and auto-completion support."""

    execute_signal = Signal()
    save_signal = Signal()
    input_signal = Signal()
    font_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent

        self.setWordWrapMode(QTextOption.NoWrap)
        self._setup_font()

        font_metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopDistance(INDENT_LEN * font_metrics.horizontalAdvance(' '))

        self.highlighter = PythonHighlighter(self.document())

        self.completer = None
        self.completion_thread = None
        self._request_id = 0

        self.setAcceptDrops(True)

    def _setup_font(self):
        font = QFont(DEFAULT_FONT_NAME, 12)
        font.setFixedPitch(True)
        font.setStyleHint(QFont.Monospace)
        self.document().setDefaultFont(font)

    def get_font_size(self) -> int:
        return self.document().defaultFont().pointSize()

    def change_font_size(self, increase: bool):
        current_size = self.get_font_size()
        new_size = min(MAX_FONT_SIZE, current_size + 1) if increase else max(MIN_FONT_SIZE, current_size - 1)
        font = self.document().defaultFont()
        font.setPointSize(new_size)
        self.document().setDefaultFont(font)
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(INDENT_LEN * font_metrics.horizontalAdvance(' '))
        self.font_changed.emit()

    def get_current_indent(self) -> str:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
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
        cursor.setPosition(start, QTextCursor.MoveAnchor)
        cursor.setPosition(start + len(new_text), QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

    def _select_full_lines(self, cursor):
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event: QKeyEvent):
        self.input_signal.emit()
        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Tab:
            if self.completer and self.completer.isVisible():
                current_item = self.completer.currentItem()
                if current_item:
                    self.completer._apply_completion(current_item)
                event.accept()
                return
            self.insert_tab()
            event.accept()
            return

        if key == Qt.Key_Backtab:
            if self.completer:
                self.completer.hide()
            self.insert_backtab()
            return

        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self.completer and self.completer.isVisible():
                if modifiers == Qt.NoModifier:
                    self.completer._apply_completion(self.completer.currentItem())
                    event.accept()
                    return
            if modifiers == Qt.NoModifier:
                indent = self.get_current_indent()
                super().keyPressEvent(event)
                if indent:
                    cursor = self.textCursor()
                    cursor.insertText(indent)
                    self.setTextCursor(cursor)
                event.accept()
                return
            if modifiers == Qt.ShiftModifier:
                event.accept()
                return

        if modifiers == Qt.ControlModifier and key in (Qt.Key_Return, Qt.Key_Enter):
            if self.completer:
                self.completer.hide()
            self.execute_signal.emit()
            return

        if key == Qt.Key_Backspace:
            if self.completer:
                self.completer.hide()
            cursor = self.textCursor()
            if cursor.positionInBlock() >= INDENT_LEN:
                cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, INDENT_LEN)
                selected = cursor.selectedText()
                if selected == ' ' * INDENT_LEN:
                    cursor.removeSelectedText()
                    event.accept()
                    return
            super().keyPressEvent(event)
            return

        if modifiers == Qt.ControlModifier and key == Qt.Key_D:
            if self.completer:
                self.completer.hide()
            self._duplicate_line_or_selection()
            return

        if modifiers == Qt.AltModifier and key == Qt.Key_Q:
            if self.completer:
                self.completer.hide()
            self._toggle_comment()
            return

        if key == Qt.Key_Escape:
            if self.completer and self.completer.isVisible():
                self.completer.hide()
                event.accept()
                return

        if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp, Qt.Key_PageDown):
            if self.completer and self.completer.isVisible():
                self.completer.navigate(key)
                event.accept()
                return

        super().keyPressEvent(event)

        if event.text() and modifiers in (Qt.NoModifier, Qt.ShiftModifier):
            self._trigger_completion()

    def _duplicate_line_or_selection(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace('\u2029', '\n')
            end = cursor.selectionEnd()
            cursor.setPosition(end)
            cursor.insertText(text)
            cursor.setPosition(end, QTextCursor.MoveAnchor)
            cursor.setPosition(end + len(text), QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            cursor.movePosition(QTextCursor.StartOfLine)
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
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

    def _trigger_completion(self):
        if not self.completion_thread or not self.completer:
            return

        text = self.toPlainText()
        cursor = self.textCursor()
        pos = cursor.position()

        if text and pos > 0 and pos <= len(text):
            char_before = text[pos - 1]
            if char_before.isalnum() or char_before == '_':
                self._request_id += 1
                line_num = cursor.blockNumber() + 1
                col_num = cursor.columnNumber()
                self.completion_thread.request_completions(
                    text, line_num, col_num, self._request_id
                )
            else:
                self.completer.hide()

    def on_completions_ready(self, completions, request_id):
        if not self.completer:
            return
        if request_id != self._request_id:
            return
        if completions:
            self.completer.update_completions(completions)
            self._move_completer()
        else:
            self.completer.hide()

    def _move_completer(self):
        if not self.completer:
            return
        cursor_rect = self.cursorRect()
        # Position is relative to editor (parent)
        pos = QPoint(cursor_rect.left(), cursor_rect.bottom() + 2)
        self.completer.show_at(pos)

    def apply_completion(self, completion):
        cursor = self.textCursor()
        pos = cursor.position()

        # Manually find the start of the partial word (stop at dot, space, or start of line)
        # Scan backwards character by character
        scan_pos = pos
        text = self.toPlainText()
        while scan_pos > 0:
            ch = text[scan_pos - 1]
            if ch in (' ', '.', '\t', '\n'):
                word_start = scan_pos  # Start after separator
                break
            scan_pos -= 1
        else:
            word_start = 0  # Start of document

        # Always use the full name for replacement
        insert_text = completion.name
        needs_cursor_move_back = False

        # For functions/methods, insert name + brackets with cursor between
        if hasattr(completion, 'type') and completion.type in ('function', 'method'):
            insert_text = completion.name + '()'
            needs_cursor_move_back = True

        # Select from word_start to pos and replace
        cursor.setPosition(word_start)
        cursor.setPosition(pos, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(insert_text)

        # Position cursor inside parentheses for functions
        if needs_cursor_move_back:
            cursor.movePosition(QTextCursor.Left)

        self.setTextCursor(cursor)
        self.setFocus()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if self.completer:
                self.completer.hide()
            if event.angleDelta().y() > 0:
                self.change_font_size(increase=True)
            else:
                self.change_font_size(increase=False)
            event.accept()
        else:
            super().wheelEvent(event)

    def get_selected_text(self) -> str:
        cursor = self.textCursor()
        return cursor.selectedText().replace('\u2029', '\n')

    def append_text(self, text: str):
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.End)

    def focusOutEvent(self, event):
        if self.completer:
            self.completer.hide()
        super().focusOutEvent(event)
