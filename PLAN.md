# Python Script Editor for Agio Debug

Interactive Python script editor with REPL capabilities, built on PySide6.

## Status: ✅ COMPLETE

All planned features have been implemented.

## Features Implemented

### Phase 1: Core Infrastructure ✅
1. **Executor** (`core/executor.py`) - Code execution with stdout/stderr capture, namespace management
2. **Session Manager** (`core/session_manager.py`) - Tab/code/window persistence between runs
3. **Completion Engine** (`core/completion_engine.py`) - Jedi-based completion logic (runs in worker thread)

### Phase 2: UI Widgets ✅
4. **Syntax Highlighter** (`widgets/syntax/highlighter.py`) - Python syntax highlighting with themes
5. **Code Editor** (`widgets/code_editor.py`) - QPlainTextEdit-based editor (indent, tab handling, font scaling)
6. **Fold Manager** (`widgets/folding.py`) - Indent-based fold ranges, fold/unfold/fold_all/unfold_all,
   fold state remap on edits
7. **Line Number Widget** (`widgets/line_number_widget.py`) - Line number gutter + fold marker column
8. **Completion Widget** (`widgets/completion_widget.py`) - Autocomplete popup (viewport-based positioning)
9. **Tab Widget** (`widgets/tab_widget.py`) - Multi-tab container with close/rename/add

### Phase 3: Integration ✅
10. **Completion Worker** (`threads/completion_thread.py`) - QThread with request queue and coalescing
11. **Editor Dialog** (`editor_dialog.py`) - Main dialog integrating all components
12. **API Layer** - Clean public API for external usage (all methods in ScriptEditorDialog)

### Phase 4: Polish ✅
13. **Event Handling** - Keyboard shortcuts, mouse events
14. **Documentation** - README.md with usage examples and API docs
15. **Test Script** - `test_editor.py` for demonstration

### Phase 5: Code Folding ✅
16. **Folding** - Indent-based fold regions (with elif/else/except/finally continuation),
    fold markers in gutter with click toggling, nested folds, Fold All / Unfold All
    (`Ctrl+Shift+-` / `Ctrl+Shift+=`), fold state remap on edits above regions,
    fold state saved in sessions

### Phase 6: Autocompletion Rework ✅
17. **Threaded completions** - `CompletionWorker(QThread)` with request coalescing,
    150ms debounce, popup positioned relative to viewport with flip/clamp

## Architecture

```
script_editor/
├── __init__.py                 # Public API exports
├── editor_dialog.py            # Main entry point - ScriptEditorDialog
├── core/                       # Core logic (no UI dependencies)
│   ├── executor.py             # Python code execution engine
│   ├── session_manager.py      # Session persistence (tabs, folds, window geometry)
│   └── completion_engine.py    # Jedi completion logic (worker-thread only)
├── widgets/                    # UI components
│   ├── syntax/                 # Syntax highlighting
│   │   ├── keywords.py         # Python keywords/syntax definitions
│   │   └── highlighter.py      # QSyntaxHighlighter implementation
│   ├── code_editor.py          # QPlainTextEdit-based code editor (CodeEditor)
│   ├── input_widget.py         # Backward-compatible InputWidget alias
│   ├── folding.py              # FoldManager: fold ranges + visibility
│   ├── line_number_widget.py   # Line number gutter + fold markers
│   ├── completion_widget.py    # Autocomplete popup widget
│   └── tab_widget.py           # Multi-tab container widget
└── threads/
    └── completion_thread.py    # CompletionWorker(QThread) with coalescing
```

## All Features

- ✅ Interactive REPL on Qt widget with Ctrl+Enter execution
- ✅ Feedback in output console
- ✅ Support for multiple code tabs
- ✅ Python syntax highlighting
- ✅ Autocomplete with jedi resolved in QThread (non-blocking UI)
- ✅ Auto-indent on new block start
- ✅ Line numbers in editors (document numbering, hidden lines skipped)
- ✅ Code folding (marker column, click toggling, fold all / unfold all)
- ✅ Font size change with Ctrl+MouseScroll
- ✅ Separated logic (tabs, code, execution) from interface
- ✅ API for working with editor via code

## Usage

```python
from agio_dev_tools.lib.script_editor import ScriptEditorDialog

# Create editor
editor = ScriptEditorDialog()

# Add code to a new tab
editor.add_tab("My Script", "print('Hello World')")

# Get current tab's code
code = editor.get_current_code()

# Execute code programmatically
editor.execute_code()

# Folding API
editor.fold_all()             # collapse all regions in current tab
editor.unfold_all()
editor.toggle_fold_current()

# Get all tabs and their content
for i in range(editor.get_tab_count()):
    print(f"Tab {i}: {editor.get_tab_title(i)}")
    print(editor.get_tab_code(i))
```

## Dependencies

- PySide6 >= 6.11
- jedi >= 0.19.2 (0.20+ required for Python 3.14 hosts)
