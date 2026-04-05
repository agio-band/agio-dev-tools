## Simple Python Script Editor

Interactive REPL editor

How to use standalone

```python

import sys
import os
from PySide6.QtWidgets import QApplication

from agio_dev_tools.lib.script_editor import ScriptEditorDialog


def main():
    app = QApplication(sys.argv)
    editor = ScriptEditorDialog(session_name='example')
    editor.show()
    sys.exit(app.exec())

    
if __name__ == "__main__":
    main()
```
