from dcc.maya.libs import sceneutils
from ...libs import DCC, abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class UnloadTurtlePluginTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that unloads the turtle plugin from the open scene file.
    """

    __slots__ = ()
    __dcc__ = DCC.Maya
    __title__ = 'Unload Turtle Plugin'

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :key taskManager: ezbatcher.libs.taskmanager.TaskManager
        :rtype: None
        """

        sceneutils.unloadTurtlePlugin()
