"""Code input editor widget with syntax highlighting and completions."""

import re
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QFont, QTextOption, QFontMetrics, QKeyEvent, QTextCursor
)

from ..widgets.syntax.highlighter import PythonHighlighter, DEFAULT_COLORS

INDENT_LEN = 4
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 30
DEFAULT_FONT_NAME = "Courier New"


class InputWidget(QTextEdit):
    """Code input editor with syntax highlighting and auto-completion support."""

    execute_signal = Signal()
    save_signal = Signal()
    input_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_editor = parent
        
        # Setup editor
        self.setWordWrapMode(QTextOption.NoWrap)
        
        # Setup font
        self.font_name = DEFAULT_FONT_NAME
        self._setup_font()
        
        # Setup tab stops
        font_metrics = QFontMetrics(self.document().defaultFont())
        self.setTabStopDistance(INDENT_LEN * font_metrics.horizontalAdvance(' '))
        
        # Setup syntax highlighter
        self.highlighter = PythonHighlighter(self.document())
        
        # Completion widget reference
        self.completer = None
        
        self.setAcceptDrops(True)

    def _setup_font(self):
        """Setup the default font."""
        font = QFont(self.font_name, 12)
        font.setFixedPitch(True)
        font.setStyleHint(QFont.Monospace)
        self.document().setDefaultFont(font)

    def get_font_size(self) -> int:
        """Get current font size."""
        return self.document().defaultFont().pointSize()

    def change_font_size(self, increase: bool):
        """Change font size up or down."""
        current_size = self.get_font_size()
        if increase:
            new_size = min(MAX_FONT_SIZE, current_size + 1)
        else:
            new_size = max(MIN_FONT_SIZE, current_size - 1)
        
        font = self.document().defaultFont()
        font.setPointSize(new_size)
        self.document().setDefaultFont(font)
        
        # Update tab stops for new font
        font_metrics = QFontMetrics(font)
        self.setTabStopDistance(INDENT_LEN * font_metrics.horizontalAdvance(' '))

    def get_current_indent(self) -> str:
        """Get the indentation of the current line, plus extra if line ends with ':'."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        line = cursor.selectedText()
        
        indent = ''
        if line.strip():
            match = re.match(r'^(\s*)', line)
            if match:
                indent = match.group(0)
        
        # Auto-indent if line ends with ':'
        if line.rstrip().endswith(':'):
            indent += ' ' * INDENT_LEN
        
        return indent

    def insert_tab(self):
        """Insert tab or indent selected text."""
        cursor = self.textCursor()
        if cursor.hasSelection():
            # Indent selected lines
            self._indent_selected(increase=True)
        else:
            self.insertPlainText(' ' * INDENT_LEN)

    def insert_backtab(self):
        """Decrease indent of selected text or current line."""
        cursor = self.textCursor()
        self._indent_selected(increase=False)

    def _indent_selected(self, increase: bool):
        """Increase or decrease indentation of selected lines."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        
        # Select full lines
        self._select_full_lines(cursor)
        
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        text = cursor.selectedText()
        
        lines = text.split('\u2029')  # Unicode paragraph separator
        if increase:
            new_lines = [' ' * INDENT_LEN + line for line in lines]
        else:
            new_lines = []
            for line in lines:
                # Remove up to INDENT_LEN spaces
                spaces_to_remove = min(INDENT_LEN, len(line) - len(line.lstrip(' ')))
                new_lines.append(line[spaces_to_remove:] if line.startswith(' ' * spaces_to_remove) else line)
        
        new_text = '\n'.join(new_lines)
        
        cursor.removeSelectedText()
        cursor.insertText(new_text)
        cursor.setPosition(start, QTextCursor.MoveAnchor)
        cursor.setPosition(start + len(new_text), QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

    def _select_full_lines(self, cursor):
        """Expand selection to full lines."""
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key presses."""
        self.input_signal.emit()
        
        # Tab key
        if event.key() == Qt.Key_Tab:
            if self.completer and self.completer.isVisible():
                self.completer.apply_current_completion()
                return
            self.insert_tab()
            event.accept()
            return
        
        # Backtab (Shift+Tab)
        if event.key() == Qt.Key_Backtab:
            self.insert_backtab()
            return
        
        # Enter/Return
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # If completer is visible, apply completion
            if self.completer and self.completer.isVisible():
                if event.modifiers() == Qt.NoModifier:
                    self.completer.apply_current_completion()
                    return
            
            # Auto-indent on new line
            if event.modifiers() == Qt.NoModifier:
                indent = self.get_current_indent()
                super().keyPressEvent(event)
                if indent:
                    cursor = self.textCursor()
                    cursor.insertText(indent)
                    self.setTextCursor(cursor)
                event.accept()
                return
            
            # Ignore Shift+Enter
            if event.modifiers() == Qt.ShiftModifier:
                event.accept()
                return
        
        # Ctrl+Enter - Execute code
        if event.modifiers() == Qt.ControlModifier and event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.completer:
                self.completer.hide()
            self.execute_signal.emit()
            return
        
        # Backspace - handle auto-indent removal
        if event.key() == Qt.Key_Backspace:
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
        
        # Ctrl+D - Duplicate line/selection
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_D:
            self._duplicate_line_or_selection()
            return
        
        # Alt+Q - Comment/uncomment
        if event.modifiers() == Qt.AltModifier and event.key() == Qt.Key_Q:
            self._toggle_comment()
            return
        
        # Escape or navigation keys - close completer
        if event.key() in (Qt.Key_Escape, Qt.Key_Left, Qt.Key_Right, Qt.Key_Home, Qt.Key_End):
            if self.completer:
                self.completer.hide()
        
        # Arrow keys for completer navigation
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            if self.completer and self.completer.isVisible():
                self.completer.navigate(event.key())
                return
        
        super().keyPressEvent(event)
        
        # Trigger completion on text input
        if event.text() and event.modifiers() in (Qt.NoModifier, Qt.ShiftModifier):
            self._trigger_completion()

    def _duplicate_line_or_selection(self):
        """Duplicate current line or selection."""
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
        """Toggle comment on selected lines."""
        cursor = self.textCursor()
        self._select_full_lines(cursor)
        
        text = cursor.selectedText()
        lines = text.replace('\u2029', '\n').split('\n')
        
        # Check if all lines are commented
        all_commented = all(line.lstrip().startswith('#') for line in lines if line.strip())
        
        if all_commented:
            # Remove comments
            new_lines = []
            for line in lines:
                stripped = line.lstrip()
                if stripped.startswith('#'):
                    # Remove the # and one space after it
                    idx = line.index('#')
                    rest = line[idx+1:]
                    if rest.startswith(' '):
                        rest = rest[1:]
                    new_lines.append(line[:idx] + rest)
                else:
                    new_lines.append(line)
        else:
            # Add comments
            new_lines = ['#' + line for line in lines]
        
        new_text = '\n'.join(new_lines)
        cursor.removeSelectedText()
        cursor.insertText(new_text)
        self.setTextCursor(cursor)

    def _trigger_completion(self):
        """Trigger completion if appropriate."""
        if self.completer:
            text = self.toPlainText()
            cursor = self.textCursor()
            pos = cursor.position()
            
            if text and pos > 0:
                # Check if character before cursor should trigger completion
                if text[pos-1].isalnum() or text[pos-1] == '_':
                    # Get line and column for Jedi
                    line_num = cursor.blockNumber() + 1
                    col_num = cursor.columnNumber()
                    self.completer.request_completions(text, line_num, col_num)

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

    def get_selected_text(self) -> str:
        """Get currently selected text."""
        cursor = self.textCursor()
        return cursor.selectedText().replace('\u2029', '\n')

    def append_text(self, text: str):
        """Append text to the editor."""
        self.moveCursor(QTextCursor.End)
        self.insertPlainText(text)
        self.moveCursor(QTextCursor.End)
