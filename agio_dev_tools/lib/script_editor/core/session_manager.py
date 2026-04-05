import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_SESSION_NAME = "default"
DEFAULT_SESSIONS_DIR = Path.home() / ".cache" / "agio" / "py-editor" / "sessions"

TAB_FILE_PREFIX = "tab_"
TAB_FILE_EXT = ".py"
MANIFEST_NAME = "tabs.json"


def _get_sessions_dir() -> Path:
    env_path = os.environ.get("AGIO_PY_EDITOR_SESSIONS_DIR")
    if env_path:
        return Path(env_path)
    return DEFAULT_SESSIONS_DIR


def _get_session_name() -> str:
    return os.environ.get("AGIO_PY_EDITOR_SESSION", DEFAULT_SESSION_NAME)


class SessionManager:

    def __init__(self, session_name: Optional[str] = None, sessions_dir: Optional[Path] = None):
        self.session_name = session_name or _get_session_name()
        self.sessions_dir = sessions_dir or _get_sessions_dir()
        self.session_dir = self.sessions_dir / self.session_name

    @property
    def manifest_path(self) -> Path:
        return self.session_dir / MANIFEST_NAME

    def _ensure_dir(self) -> Path:
        self.session_dir.mkdir(parents=True, exist_ok=True)
        return self.session_dir

    def session_exists(self) -> bool:
        return self.manifest_path.exists()

    def load_session(self) -> Optional[list[dict]]:
        if not self.session_exists():
            return None

        try:
            with open(self.manifest_path) as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        tabs = []
        for entry in manifest:
            title = entry.get("title", "Untitled")
            font_size = entry.get("font_size", 12)
            filename = entry.get("file")
            code = ""
            if filename:
                tab_file = self.session_dir / filename
                if tab_file.exists():
                    try:
                        code = tab_file.read_text(encoding="utf-8")
                    except OSError:
                        pass
            tabs.append({"title": title, "code": code, "font_size": font_size})

        return tabs if tabs else None

    def save_session(self, tabs: list[tuple[str, str, int]]):
        self._ensure_dir()

        # Clean up old tab files
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path) as f:
                    old_manifest = json.load(f)
                for entry in old_manifest:
                    filename = entry.get("file")
                    if filename:
                        old_file = self.session_dir / filename
                        if old_file.exists():
                            old_file.unlink(missing_ok=True)
            except (json.JSONDecodeError, OSError):
                pass

        # Write new tab files and build manifest
        manifest = []
        for i, (title, code, font_size) in enumerate(tabs):
            filename = f"{TAB_FILE_PREFIX}{i}{TAB_FILE_EXT}"
            tab_file = self.session_dir / filename
            try:
                tab_file.write_text(code, encoding="utf-8")
            except OSError:
                pass
            manifest.append({"title": title, "file": filename, "font_size": font_size})

        try:
            with open(self.manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
        except OSError:
            pass

    def save_tab(self, index: int, title: str, code: str, font_size: int = 12):
        self._ensure_dir()
        filename = f"{TAB_FILE_PREFIX}{index}{TAB_FILE_EXT}"
        tab_file = self.session_dir / filename
        try:
            tab_file.write_text(code, encoding="utf-8")
        except OSError:
            pass
        manifest = []
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path) as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, OSError):
                manifest = []

        entry = {"title": title, "file": filename, "font_size": font_size}
        if index < len(manifest):
            manifest[index] = entry
        else:
            manifest.append(entry)

        try:
            with open(self.manifest_path, "w") as f:
                json.dump(manifest, f, indent=2)
        except OSError:
            pass
