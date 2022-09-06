from dcc.abstract import proxyfactory
from dcc import __application__
from . import abstracttask
from .. import tasks

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

            from ..tasks import maya
            return tasks, maya

        elif __application__ == '3dsmax':

            from ..tasks import max
            return tasks, max

        else:

            return tasks,
