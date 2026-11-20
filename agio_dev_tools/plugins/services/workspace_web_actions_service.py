import logging

from agio.core.actions import make_action
from agio.core.entities.project import AProject
from agio.core.plugins.base_service import ServicePlugin
from agio.tools import paths

logger = logging.getLogger(__name__)


class WorkspaceService(ServicePlugin):
    name = 'workspace_service'

    @make_action(
        label='Open Workspace Dir',
        menu_name='workspace_tools_menu',
        app_name='web'
    )
    def open_dir(self, *args: str, **kwargs):
        project_id = kwargs.get('project_id')
        if not project_id:
            raise Exception('No project_id provided')
        workspace = AProject(project_id).get_workspace()
        ws_path = workspace.get_manager().install_root
        paths.open_path(ws_path)

    # TODO: reinstall workspace
    # TODO: delete workspace

