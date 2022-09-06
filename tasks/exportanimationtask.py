from ..libs import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ExportAnimationTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that exports animation from the scene file.
    """

    __slots__ = ()
    __title__ = 'Export Animation'

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :key taskManager: ezbatcher.libs.taskmanager.TaskManager
        :rtype: None
        """

        pass