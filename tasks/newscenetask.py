from dcc import fnscene
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

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(NewSceneTask, self).__init__(*args, **kwargs)
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        scene = fnscene.FnScene()
        scene.new()
    # endregion
