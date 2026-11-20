"""Code folding logic based on Python indentation levels.

FoldManager computes foldable ranges from leading indentation of blocks
(Python is indentation-structured, so this is reliable enough for an editor
without full AST parsing) and applies them to the QTextDocument by hiding
the inner blocks.

Hidden blocks are handled by Qt: ``QTextBlock.setVisible(False)`` followed
by ``QTextDocument.markContentsDirty()`` makes QPlainTextEdit's layout
collapse the block to zero height (verified for PySide6).
"""

from PySide6.QtGui import QTextCursor

TAB_SIZE = 4

# Block statements that continue a region at the same indent level
# (so that folding an `if` also covers its `else`, `try` covers `except`, ...)
CONTINUATION_PREFIXES = ("elif", "else", "except", "finally")


class FoldManager:
    """Manages fold ranges and folded state for a single editor."""

    def __init__(self, editor):
        self._editor = editor
        self._folded: set[int] = set()      # block numbers of folded region starts
        self._ranges: dict[int, int] = {}   # start block number -> end block number (inclusive)
        self._dirty = True
        self._last_block_count = editor.document().blockCount()

    # ---------- range computation ----------

    def invalidate(self):
        self._dirty = True

    def _ensure_ranges(self):
        if self._dirty:
            self._ranges = self._compute_ranges()
            self._dirty = False

    def _compute_ranges(self) -> dict[int, int]:
        doc = self._editor.document()
        ranges = {}
        block = doc.firstBlock()
        while block.isValid():
            line = block.text()
            if line.strip():
                indent = self._indent(line)
                end = None
                it = block.next()
                while it.isValid():
                    text = it.text()
                    if text.strip():
                        ind = self._indent(text)
                        if ind > indent:
                            end = it
                        elif ind == indent and self._is_continuation(text):
                            # elif/else/except/finally at the same indent:
                            # the region continues through them
                            end = it
                        else:
                            break
                    # blank lines in between are skipped (they don't end a region)
                    it = it.next()
                if end is not None:
                    ranges[block.blockNumber()] = end.blockNumber()
            block = block.next()
        return ranges

    @staticmethod
    def _is_continuation(line: str) -> bool:
        stripped = line.lstrip()
        for prefix in CONTINUATION_PREFIXES:
            if stripped.startswith(prefix):
                rest = stripped[len(prefix):]
                if rest == "" or rest[0] in ": \t":
                    return True
        return False

    @staticmethod
    def _indent(line: str) -> int:
        expanded = line.expandtabs(TAB_SIZE)
        return len(expanded) - len(expanded.lstrip())

    # ---------- state queries ----------

    def is_foldable(self, block) -> bool:
        """True if the block starts a collapsible region (unfolded)."""
        self._ensure_ranges()
        return block.blockNumber() in self._ranges and block.isVisible()

    def is_folded(self, block) -> bool:
        """True if the block is the top line of a folded region."""
        return block.blockNumber() in self._folded

    def has_folds(self) -> bool:
        return bool(self._folded)

    def fold_range(self, block):
        """(start_number, end_number) of the region starting at block, or None."""
        self._ensure_ranges()
        num = block.blockNumber()
        if num not in self._ranges:
            return None
        return num, self._ranges[num]

    # ---------- folding operations ----------

    def fold(self, block):
        self._ensure_ranges()
        num = block.blockNumber()
        end = self._ranges.get(num)
        if end is None or num in self._folded:
            return
        self._folded.add(num)
        self._apply_visibility(num + 1, end, visible=False)
        self._after_change(block)

    def unfold(self, block):
        num = block.blockNumber()
        if num not in self._folded:
            return
        self._ensure_ranges()
        end = self._ranges.get(num, num)
        self._folded.discard(num)
        self._apply_visibility(num + 1, end, visible=True)
        # re-collapse nested regions that were folded before
        for start in list(self._folded):
            if num < start <= end:
                sub_end = self._ranges.get(start)
                if sub_end is not None and sub_end <= end:
                    self._apply_visibility(start + 1, sub_end, visible=False)
        self._after_change(block)

    def toggle_fold(self, block):
        if block.blockNumber() in self._folded:
            self.unfold(block)
        else:
            self.fold(block)

    def fold_all(self):
        self._ensure_ranges()
        if not self._ranges:
            return
        for start, end in self._ranges.items():
            self._folded.add(start)
        for start, end in self._ranges.items():
            self._apply_visibility(start + 1, end, visible=False)
        self._after_change()

    def unfold_all(self):
        self._ensure_ranges()
        if not self._folded:
            return
        for start in list(self._folded):
            end = self._ranges.get(start, start)
            self._apply_visibility(start + 1, end, visible=True)
        self._folded.clear()
        self._after_change()

    def unfold_around(self, block):
        """Unfold all regions containing (or starting at) the given block."""
        changed = False
        for start in list(self._folded):
            self._ensure_ranges()
            end = self._ranges.get(start)
            if end is not None and start <= block.blockNumber() <= end:
                self.unfold(self._editor.document().findBlockByNumber(start))
                changed = True
        return changed

    # ---------- maintenance ----------

    def on_contents_change(self, from_pos: int = 0, chars_removed: int = 0, chars_added: int = 0):
        """Re-sync folding state after document edits."""
        doc = self._editor.document()
        new_count = doc.blockCount()
        delta = new_count - self._last_block_count
        self._last_block_count = new_count
        self._dirty = True
        if not self._folded:
            return
        # remap folded starts when lines were inserted/removed above them
        if delta != 0:
            edit_block = doc.findBlock(from_pos).blockNumber()
            remapped = set()
            for start in self._folded:
                if start > edit_block and delta != 0:
                    shifted = start + delta
                    if shifted > 0:
                        remapped.add(shifted)
                else:
                    remapped.add(start)
            self._folded = remapped
        self._ensure_ranges()
        # drop folded entries whose region is gone
        for start in list(self._folded):
            if start not in self._ranges:
                self._folded.discard(start)
        # safety: show blocks hidden but not covered by any folded region
        covered = set()
        for start, end in self._ranges.items():
            if start in self._folded:
                covered.update(range(start + 1, end + 1))
        doc = self._editor.document()
        block = doc.firstBlock()
        first, last = None, None
        changed = False
        while block.isValid():
            if not block.isVisible() and block.blockNumber() not in covered:
                block.setVisible(True)
                changed = True
                first = first if first is not None else block
                last = block
            block = block.next()
        if changed and first is not None and last is not None:
            self._mark_dirty(first, last)
            self._dirty = True

    def _apply_visibility(self, start_num: int, end_num: int, visible: bool):
        doc = self._editor.document()
        first = doc.findBlockByNumber(start_num)
        last = doc.findBlockByNumber(end_num)
        if not first.isValid() or not last.isValid():
            return
        it = first
        changed = False
        while it.isValid() and it.blockNumber() <= end_num:
            if it.isVisible() != visible:
                it.setVisible(visible)
                changed = True
            it = it.next()
        if changed:
            self._mark_dirty(first, last)

    def _mark_dirty(self, first, last):
        doc = self._editor.document()
        start_pos = first.position()
        length = last.position() + last.length() - start_pos
        doc.markContentsDirty(start_pos, max(1, length))

    def _after_change(self, anchor_block=None):
        self._ensure_cursor_on_visible(anchor_block)
        self._editor.update_gutter()
        self._editor.ensureCursorVisible()

    def _ensure_cursor_on_visible(self, anchor_block=None):
        cursor = self._editor.textCursor()
        block = cursor.block()
        if block.isVisible():
            return
        # prefer keeping the anchor: unfold regions containing the cursor
        if anchor_block is None and self.unfold_around(block):
            return
        target = None
        it = block.previous()
        while it.isValid() and not it.isVisible():
            it = it.previous()
        if it.isValid():
            target = it
        else:
            it = block.next()
            while it.isValid() and not it.isVisible():
                it = it.next()
            if it.isValid():
                target = it
        if target is not None:
            new_cursor = QTextCursor(target)
            new_cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            self._editor.setTextCursor(new_cursor)
