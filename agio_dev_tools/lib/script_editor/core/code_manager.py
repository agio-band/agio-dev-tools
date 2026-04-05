from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class TabInfo:
    title: str
    code: str = ""
    modified: bool = False


class CodeManager:
    def __init__(self):
        self._tabs: List[TabInfo] = []
        self._active_tab_index: int = -1

    def add_tab(self, title: str = "Untitled", code: str = "") -> int:
        tab = TabInfo(title=title, code=code)
        self._tabs.append(tab)
        self._active_tab_index = len(self._tabs) - 1
        return self._active_tab_index

    def remove_tab(self, index: int) -> bool:
        if 0 <= index < len(self._tabs) and len(self._tabs) > 1:
            self._tabs.pop(index)
            if self._active_tab_index >= len(self._tabs):
                self._active_tab_index = len(self._tabs) - 1
            return True
        return False

    def get_tab_count(self) -> int:
        return len(self._tabs)

    def get_active_tab_index(self) -> int:
        return self._active_tab_index

    def set_active_tab(self, index: int) -> bool:
        if 0 <= index < len(self._tabs):
            self._active_tab_index = index
            return True
        return False

    def get_tab_title(self, index: int = None) -> Optional[str]:
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            return self._tabs[idx].title
        return None

    def set_tab_title(self, index: int, title: str) -> bool:
        if 0 <= index < len(self._tabs):
            self._tabs[index].title = title
            return True
        return False

    def get_tab_code(self, index: int = None) -> Optional[str]:
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            return self._tabs[idx].code
        return None

    def set_tab_code(self, code: str, index: int = None) -> bool:
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            self._tabs[idx].code = code
            self._tabs[idx].modified = True
            return True
        return False

    def get_all_tabs(self) -> Dict[int, TabInfo]:
        return {i: tab for i, tab in enumerate(self._tabs)}

    def mark_tab_clean(self, index: int = None) -> bool:
        idx = index if index is not None else self._active_tab_index
        if 0 <= idx < len(self._tabs):
            self._tabs[idx].modified = False
            return True
        return False
