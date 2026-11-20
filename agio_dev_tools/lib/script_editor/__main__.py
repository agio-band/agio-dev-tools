import os
import sys

from PySide6.QtWidgets import QApplication

from agio_dev_tools.lib.script_editor import ScriptEditorDialog

app = QApplication(sys.argv)
dial = ScriptEditorDialog()
dial.show()
sys.exit(app.exec())