from dcc.maya.libs import sceneutils
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class UnloadMentalRayPluginTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that unloads the MentalRay plugin from the open scene file.
    """

    # region Dunderscores
    __slots__ = ()
    __title__ = 'Unload MentalRay Plugin'
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        sceneutils.unloadMentalRayPlugin()
    # endregion
