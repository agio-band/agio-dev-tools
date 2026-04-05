"""Code manager for handling tabs and code storage."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TabInfo:
    """Information about a single code tab."""
    title: str
    code: str = ""
    modified: bool = False


class CodeManager:
    """Manages multiple code tabs and their content."""

    def __init__(self):
        self._tabs: List[TabInfo] = []
        self._active_tab_index: int = -1

    def add_tab(self, title: str = "Untitled", code: str = "") -> int:
        """Add a new tab and return its index."""
        tab = TabInfo(title=title, code=code)
        self._tabs.append(tab)
        self._active_tab_index = len(self._tabs) - 1
        return self._active_tab_index

    def remove_tab(self, index: int) -> bool:
        """Remove tab at given index. Returns True if successful."""
        if 0 <= index < len(self._tabs) and len(self._tabs) > 1:
            self._tabs.pop(index)
            if self._active_tab_index >= len(self._tabs):
                self._active_tab_index = len(self._tabs) - 1
            return True
        return False

    def get_tab_count(self) -> int:
        """Return number of tabs."""
        return len(self._tabs)

    def get_active_tab_index(self) -> int:
        """Return index of active tab."""
        return self._active_tab_index

    def set_active_tab(self, index: int) -> bool:
        """Set active tab by index. Returns True if successful."""
        if 0 <= index < len(self._tabs):
            self._active_tab_index = index
            return True
        return False

    def get_tab_title(self, index: int = None) -> Optional[str]:
        """Get title of tab at index (or active tab if None)."""
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            return self._tabs[idx].title
        return None

    def set_tab_title(self, index: int, title: str) -> bool:
        """Set title of tab at index. Returns True if successful."""
        if 0 <= index < len(self._tabs):
            self._tabs[index].title = title
            return True
        return False

    def get_tab_code(self, index: int = None) -> Optional[str]:
        """Get code from tab at index (or active tab if None)."""
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            return self._tabs[idx].code
        return None

    def set_tab_code(self, code: str, index: int = None) -> bool:
        """Set code for tab at index (or active tab if None)."""
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            self._tabs[idx].code = code
            self._tabs[idx].modified = True
            return True
        return False

    def get_all_tabs(self) -> Dict[int, TabInfo]:
        """Get all tabs as {index: TabInfo} dict."""
        return {i: tab for i, tab in enumerate(self._tabs)}

    def mark_tab_clean(self, index: int = None) -> bool:
        """Mark tab as unmodified. Returns True if successful."""
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            self._tabs[idx].modified = False
            return True
        return False
