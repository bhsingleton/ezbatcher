from airship_syndicate.maxtomaya import exportutils
from ..abstract import abstracttask
from ...libs import DCC

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ExportMXSONTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that commits any changes made to the open scene file.
    """

    # region Dunderscores
    __slots__ = ('_animationOnly',)
    __dcc__ = DCC.Max
    __title__ = 'Export MXSON'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._animationOnly = kwargs.get('animationOnly', False)

        # Call parent method
        #
        super(ExportMXSONTask, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def animationOnly(self):
        """
        Getter method that returns the directory to save to.

        :rtype: str
        """

        return self._animationOnly

    @animationOnly.setter
    def animationOnly(self, animationOnly):
        """
        Setter method that updates the directory to save to.

        :type animationOnly: str
        :rtype: None
        """

        self._animationOnly = animationOnly
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :key taskManager: ezbatcher.libs.taskmanager.TaskManager
        :rtype: None
        """

        if self.animationOnly:

            exportutils.exportAnimation()

        else:

            exportutils.exportScene()
    # endregion
