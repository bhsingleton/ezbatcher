import os
import weakref

from dcc import fnscene
from dcc.collections import notifylist
from dcc.json import psonobject
from . import abstracttask, taskfactory

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TaskManager(psonobject.PSONObject):
    """
    Overload of PSONObject that acts as a collection of executable tasks.
    """

    # region Dunderscores
    __slots__ = ('__weakref__', '_scene', '_tasks', '_factory')

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._scene = fnscene.FnScene()
        self._tasks = notifylist.NotifyList()
        self._factory = taskfactory.TaskFactory.getInstance(asWeakReference=True)

        # Setup notifies
        #
        self._tasks.addCallback('itemAdded', self.taskAdded)
        self._tasks.addCallback('itemRemoved', self.taskRemoved)

        # Call parent method
        #
        super(TaskManager, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter method that returns the scene interface.

        :rtype: fnscene.FnScene
        """

        return self._scene

    @property
    def factory(self):
        """
        Getter method that returns the task factory interface.

        :rtype: taskfactory.TaskFactory
        """

        return self._factory()

    @property
    def tasks(self):
        """
        Getter method that returns the task queue.

        :rtype: List[abstracttask.AbstractTask]
        """

        return self._tasks

    @tasks.setter
    def tasks(self, tasks):
        """
        Setter method that updates the task queue.

        :type tasks: List[abstracttask.AbstractTask]
        :rtype: None
        """

        self._tasks.clear()
        self._tasks.extend(tasks)
    # endregion

    # region Methods
    def execute(self, *filePaths):
        """
        Executes the internal tasks on the supplied files.

        :type filePaths: Union[str, List[str]]
        :rtype: None
        """

        # Iterate through files
        #
        for filePath in filePaths:

            # Check if scene file exists
            #
            if not os.path.exists(filePath):

                log.warning('Cannot locate scene file: %s' % filePath)
                continue

            # Try and open scene file
            #
            success = self.scene.open(filePath)

            if not success:

                log.warning('Cannot open scene file: %s' % filePath)
                continue

            # Execute tasks
            #
            for task in self.tasks:

                task.doIt()
    # endregion

    # region Callbacks
    def taskAdded(self, index, task):
        """
        Adds a reference of this manager to the supplied task.

        :type index: int
        :type task: abstracttask.AbstractTask
        :rtype: None
        """

        task._manager = weakref.ref(self)

    def taskRemoved(self, task):
        """
        Removes the reference of this manager from the supplied task.

        :type task: abstracttask.AbstractTask
        :rtype: None
        """

        task._manager = self.nullWeakReference
    # endregion
