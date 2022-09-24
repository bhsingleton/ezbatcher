from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class NewSceneTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that creates a new scene file.
    """

    # region Dunderscores
    __slots__ = ()
    __title__ = 'New Scene'
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        self.scene.new()
    # endregion
