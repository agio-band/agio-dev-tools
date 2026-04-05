"""Python syntax highlighter for code editor."""

import re
from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QBrush, QColor, QFont

from .keywords import SYNTAX

# Default color scheme
DEFAULT_COLORS = dict(
    background=(40, 40, 40),
    keywords=(65, 255, 130),
    digits=(250, 255, 62),
    definition=(255, 160, 250),
    operator=(230, 220, 110),
    extra=(110, 180, 230),
    methods=(120, 190, 205),
    comment=(110, 100, 100),
    string=(245, 165, 18),
    docstring=(130, 160, 75),
    boolean=(160, 220, 120),
    brace=(235, 235, 195),
    default=(210, 210, 210),
)


class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Python code."""

    def __init__(self, document, colors=None):
        super().__init__(document)
        self.colors = colors or DEFAULT_COLORS.copy()

        # Multi-line string delimiters
        self.tri_single = (QRegularExpression("'''"), 1, self._get_style(self.colors['docstring']))
        self.tri_double = (QRegularExpression('"""'), 2, self._get_style(self.colors['docstring']))

        rules = []

        # Keywords
        rules += [(f'\\b{w}\\b', 0, self._get_style(self.colors['keywords'], bold=True))
                  for w in SYNTAX['keywords']]

        # Methods/function calls
        rules += [(r"\b[A-Za-z0-9_]+(?=\()", 0, self._get_style(self.colors['methods']))]

        # Operators
        rules += [(f'{op}', 0, self._get_style(self.colors['operator']))
                  for op in SYNTAX['operators']]

        # Braces
        rules += [(brace, 0, self._get_style(self.colors['brace']))
                  for brace in SYNTAX['braces']]

        # Definition keywords (class, def, etc.)
        rules += [(f'\\b{w}\\b', 0, self._get_style(self.colors['definition'], bold=True))
                  for w in SYNTAX['definition']]

        # Extra (built-in functions)
        rules += [(f'\\b{w}\\b', 0, self._get_style(self.colors['extra']))
                  for w in SYNTAX['extras']]

        # Digits
        rules += [(r"\b[\d]+\b", 0, self._get_style(self.colors['digits']))]

        # Double-quoted strings
        rules += [(r'[ru]?"[^"\\]*(\\.[^"\\]*)*"', 0, self._get_style(self.colors['string']))]

        # Single-quoted strings
        rules += [(r"[ru]?'[^'\\]*(\\.[^'\\]*)*'", 0, self._get_style(self.colors['string']))]

        # Compile rules
        self.rules = [(QRegularExpression(pat), index, fmt) for (pat, index, fmt) in rules]

    def _get_style(self, color, bold=False):
        """Create QTextCharFormat from color tuple."""
        fmt = QTextCharFormat()
        fmt.setForeground(QBrush(QColor(*color)))
        if bold:
            fmt.setFontWeight(QFont.Bold)
        return fmt

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
        # Apply default format
        default_fmt = self._get_style(self.colors['default'])
        self.setFormat(0, len(text), default_fmt)

        # Apply syntax rules
        for expression, nth, fmt in self.rules:
            match = expression.match(text)
            while match.hasMatch():
                self.setFormat(match.capturedStart(nth), len(match.captured(nth)), fmt)
                match = expression.match(text, match.capturedEnd())

        # Handle comments (but not inside strings)
        self._highlight_comments(text)

        # Handle multi-line strings
        self.setCurrentBlockState(0)
        in_multiline = self._match_multiline(text, *self.tri_single)
        if not in_multiline:
            self._match_multiline(text, *self.tri_double)

    def _highlight_comments(self, text):
        """Highlight comments that are not inside strings."""
        strings = re.findall(r'(".*?")|(\'.*?\')', text)
        if '#' not in text:
            return

        # Check if # is outside strings
        copy = text
        if strings:
            for match_group in strings:
                for match in match_group:
                    if match:
                        copy = copy.replace(match, '_' * len(match))

        if '#' in copy:
            index = copy.index('#')
            length = len(copy) - index
            comment_fmt = self._get_style(self.colors['comment'])
            self.setFormat(index, length, comment_fmt)

    def _match_multiline(self, text, delimiter, in_state, style):
        """Highlight multi-line strings."""
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            match = delimiter.match(text)
            if match.hasMatch():
                start = match.capturedStart()
                add = match.capturedLength()
            else:
                return False

        while start >= 0:
            match = delimiter.match(text, start + add)
            if match.hasMatch():
                end = match.capturedStart()
                length = end - start + match.capturedLength()
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add

            self.setFormat(start, length, style)
            match = delimiter.match(text, start + length)
            if match.hasMatch():
                start = match.capturedStart()
            else:
                start = -1

        return self.currentBlockState() == in_state
