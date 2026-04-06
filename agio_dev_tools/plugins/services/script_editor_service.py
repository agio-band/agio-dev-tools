import logging

from PySide6.QtGui import Qt

from agio.core.plugins.base_service import ServicePlugin, make_action
from agio_dev_tools.lib.script_editor import ScriptEditorDialog

logger = logging.getLogger(__name__)


class DecService(ServicePlugin):
    name = 'dev_tools'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dialog = None

    @make_action(label='Script Editor',
                 menu_name='tray.main_menu',
                 app_name='desk')
    def open_script_editor(self, *args, **kwargs):
        if not self.dialog:
            self.dialog = ScriptEditorDialog(
                parent=None,
                custom_namespace={},
                session_name='tray-app'
            )
            self.dialog.setWindowFlags(Qt.WindowType.Window)
        self.dialog.show()
