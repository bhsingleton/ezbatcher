from dcc.maya.libs import sceneutils
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class UnloadTurtlePluginTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that unloads the turtle plugin from the open scene file.
    """

    # region Dunderscores
    __slots__ = ()
    __title__ = 'Unload Turtle Plugin'
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :key taskManager: ezbatcher.libs.taskmanager.TaskManager
        :rtype: None
        """

        sceneutils.unloadTurtlePlugin()
    # endregion
