from dcc import __application__
from dcc.abstract import proxyfactory
from .. import tasks
from ..tasks import maya, max
from ..tasks.abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TaskFactory(proxyfactory.ProxyFactory):
    """
    Overload of ProxyFactory that manages instantiable tasks.
    """

    __slots__ = ()

    def classFilter(self):
        """
        Returns the base class used to filter out objects when searching for classes.

        :rtype: class
        """

        return abstracttask.AbstractTask

    def packages(self):
        """
        Returns a list of packages to be inspected for classes.

        :rtype: List[module]
        """

        if __application__ == 'maya':

            return tasks, maya

        elif __application__ == '3dsmax':

            return tasks, max

        else:

            return tasks,
