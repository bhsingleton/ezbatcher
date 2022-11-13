from abc import ABCMeta, abstractmethod
from six import with_metaclass
from dcc import fnscene
from dcc.json import psonobject
from dcc.decorators.classproperty import classproperty

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class AbstractTask(with_metaclass(ABCMeta, psonobject.PSONObject)):
    """
    Abstract base class for performing batch tasks.
    """

    # region Dunderscores
    __slots__ = ('_manager',)
    __title__ = ''
    __scene__ = fnscene.FnScene()

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private methods
        #
        self._manager = self.nullWeakReference

        # Call parent method
        #
        super(AbstractTask, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @classproperty
    def title(cls):
        """
        Getter method that returns the task's title.

        :rtype: str
        """

        return cls.__title__

    @classproperty
    def scene(cls):
        """
        Getter method that returns the scene function set.

        :rtype: fnscene.FnScene
        """

        return cls.__scene__

    @property
    def manager(self):
        """
        Getter method that returns the associated task manager.

        :rtype: ezbatcher.libs.taskmanager.TaskManager
        """

        return self._manager()
    # endregion

    # region Methods
    @abstractmethod
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        pass
    # endregion
