# Python Script Editor

Interactive Python script editor with REPL capabilities, built on PySide6 and Jedi.

## Features

✅ **Interactive REPL** - Execute code with `Ctrl+Enter` with console feedback  
✅ **Multi-tab Support** - Multiple code tabs with independent contexts  
✅ **Syntax Highlighting** - Python code syntax highlighting with customizable colors  
✅ **Code Folding** - Indent-based fold regions, gutter markers, Fold All / Unfold All, fold state saved in sessions  
✅ **Code Completion** - Jedi-powered autocomplete resolved in a background QThread (non-blocking UI)  
✅ **Auto-indentation** - Automatic indentation when starting new blocks  
✅ **Line Numbers** - Line number gutter with fold markers  
✅ **Dynamic Font Size** - `Ctrl+MouseScroll` to resize fonts in all widgets  
✅ **Separated Architecture** - Clean separation between logic (tabs, code, execution) and UI  
✅ **Programmatic API** - Full API for working with the editor via code  

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
│   ├── folding.py              # FoldManager: fold ranges + block visibility
│   ├── line_number_widget.py   # Line number gutter + fold marker column
│   ├── completion_widget.py    # Autocomplete popup widget
│   └── tab_widget.py           # Multi-tab container widget
└── threads/
    └── completion_thread.py    # CompletionWorker(QThread) with request coalescing
```

## Usage

### Basic Usage

```python
from agio_dev_tools.lib.script_editor import ScriptEditorDialog
from PySide6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
editor = ScriptEditorDialog()
editor.show()
sys.exit(app.exec())
```

### Programmatic API

```python
from agio_dev_tools.lib.script_editor import ScriptEditorDialog

# Create editor
editor = ScriptEditorDialog()

# Add code to a new tab
tab = editor.add_tab("My Script", "print('Hello World')")

# Get current tab's code
code = editor.get_current_code()

# Set code in current tab
editor.set_current_code("x = 10\ny = 20\nprint(x + y)")

# Execute code programmatically
editor.execute_code()

# Folding
editor.fold_all()              # collapse all foldable regions in current tab
editor.unfold_all()            # expand everything
editor.toggle_fold_current()   # toggle region at cursor

# Get all tabs and their content
for i in range(editor.get_tab_count()):
    print(f"Tab {i}: {editor.get_tab_title(i)}")
    print(editor.get_tab_code(i))

# Get output
output = editor.get_output()
print(f"Console output:\n{output}")

# Clear output
editor.clear_output()

# Update execution namespace (add variables)
editor.update_namespace({'my_var': 42})

# Clear namespace
editor.clear_namespace()

# Work with specific tabs
editor.set_active_tab(0)
editor.set_tab_title(0, "New Title")
editor.close_tab(1)

# Get specific editor widget
editor_widget = editor.get_editor(0)
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Execute selected code or current line |
| `Ctrl+N` | New tab |
| `Tab` | Indent (or apply completion if visible) |
| `Shift+Tab` | Unindent |
| `Ctrl+D` | Duplicate line/selection |
| `Alt+Q` / `Ctrl+/` | Toggle comment |
| `Ctrl+Shift+-` | Fold all regions |
| `Ctrl+Shift+=` | Unfold all regions |
| `Ctrl+MouseScroll` | Increase/Decrease font size |
| `Enter` | Auto-indent (adds indentation after `:`) |

## Features Detail

### Code Execution
- Executes selected text or current line with `Ctrl+Enter`
- Captures stdout/stderr in real-time
- Maintains persistent namespace across executions
- Shows `>>>` prompt for executed code
- Handles exceptions with filtered tracebacks

### Code Folding
- Indent-based fold regions (Python), `elif/else/except/finally` continue a region
- Fold markers (▾/▸) in the gutter column; click to toggle the region at that line
- Click on a line number selects the line
- Nested folds: unfolding a parent keeps folded children collapsed
- `Ctrl+Shift+-` / `Ctrl+Shift+=` fold/unfold everything; context menu has Fold/Unfold entries
- Cursor never gets stuck inside hidden blocks
- Fold state is saved and restored with sessions

### Auto-completion
- Powered by Jedi, resolved in a dedicated `QThread` (UI never blocks)
- 150 ms debounce: jedi is not queried on every keystroke; only the latest
  request is evaluated when typing fast (coalescing)
- Triggers on identifiers and after `.`
- Navigate with arrow keys, apply with `Tab`/`Enter`/double-click, `Esc` closes
- Popup shows function signatures in tooltips, opens below the cursor line and
  flips above it when there is not enough room

### Syntax Highlighting
- Keywords, built-ins, strings, comments, numbers
- Function calls, class definitions
- Customizable color scheme
- Multi-line string and docstring support

### Tab Management
- Add, close, rename tabs
- Each tab has independent code context
- Move tabs with drag & drop
- Context menu for rename

### Sessions
- Tabs (title, code, font size) and window geometry persist between runs
- Fold state is saved per tab and restored on load

### Font Scaling
- `Ctrl+MouseScroll` in any editor widget
- Affects both input and output widgets
- Maintains readability at all sizes

## Dependencies

- **PySide6** (>= 6.11) - Qt6 bindings for Python
- **jedi** (>= 0.19.2; 0.20+ recommended for Python 3.14 hosts) - Python autocompletion engine

Install with:
```bash
pip install PySide6 jedi
```

## Testing

Run the test script:
```bash
python test_editor.py
```

This will open the editor and demonstrate the API.

## Design Principles

1. **Separation of Concerns**: Core logic (executor, completion_engine, session_manager) is independent of UI
2. **Thread Safety**: Completions run in a dedicated QThread to prevent UI blocking
3. **Signal-based Communication**: Real-time output via Qt signals
4. **Extensible API**: Easy to add new features or integrate with other systems
5. **Clean Architecture**: UI widgets are separate from business logic
