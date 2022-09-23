import os
import weakref

from dcc import fnscene
from dcc.collections import notifylist
from dcc.json import psonobject
from . import taskfactory
from ..tasks.abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TaskManager(psonobject.PSONObject):
    """
    Overload of PSONObject that acts as a collection of executable tasks.
    The execution logic works as follows:
    The internal tasks are applied to each file in the queue.
    For each task executed the results of that task are passed onto the next task as arguments.
    The first task will receive the current file path being processed as an argument.
    Each task will also receive the manager instance in the form of a 'taskManager' keyword argument.
    """

    # region Dunderscores
    __slots__ = ('__weakref__', '_scene', '_tasks', '_factory', '_currentTask', '_currentFile')

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
        self._currentTask = None
        self._currentFile = None

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

    @property
    def currentTask(self):
        """
        Getter method that returns the current task.

        :rtype: abstracttask.AbstractTask
        """

        return self._currentTask

    @property
    def currentFile(self):
        """
        Getter method that returns the current file.

        :rtype: str
        """
        return self._currentFile
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
        results = None

        for filePath in filePaths:

            # Check if scene file exists
            #
            self._currentFile = filePath

            if not os.path.exists(self._currentFile):

                log.warning('Cannot locate file: %s' % self._currentFile)
                continue

            # Execute tasks
            #
            results = self._currentFile

            for task in self.tasks:

                self._currentTask = task
                results = self._currentTask.doIt(results, taskManager=self)
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
