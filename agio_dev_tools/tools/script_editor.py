from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import QWidget


def attach_script_editor(widget: QWidget, shortcut='Ctrl+P', session_name=None, extra_namespace=None):
    from agio_dev_tools.lib.script_editor import ScriptEditorDialog

    parent = widget if isinstance(widget, QWidget) else None

    dialog = ScriptEditorDialog(
        parent=parent,
        custom_namespace=extra_namespace,
        session_name=session_name or widget.objectName() or ''
    )
    widget.__script_editor__ = ScriptEditorDialog(dialog)
    if shortcut:
        QShortcut(QKeySequence(shortcut), widget, activated=dialog.show)
