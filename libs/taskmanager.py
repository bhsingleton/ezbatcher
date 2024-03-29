import os
import time
import weakref

from dcc import fnscene
from dcc.collections import notifylist
from dcc.json import psonobject
from dcc.perforce import p4utils
from . import taskfactory
from ..tasks.abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def nullCallback(*args, **kwargs):
    """
    Placeholder for the execution callbacks.

    :rtype: None
    """

    pass


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
    __slots__ = (
        '__weakref__',
        '_scene',
        '_tasks',
        '_factory',
        '_currentTask',
        '_currentFilePath',
        '_currentDirectory',
        '_currentFilename',
        '_currentName',
        '_currentExtension',
        '_currentIndex'
    )

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
        self._currentFilePath = None
        self._currentDirectory = None
        self._currentFilename = None
        self._currentName = None
        self._currentExtension = None
        self._currentIndex = None

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
    def currentFilePath(self):
        """
        Getter method that returns the current file path.

        :rtype: str
        """

        return self._currentFilePath

    @property
    def currentDirectory(self):
        """
        Getter method that returns the current directory.

        :rtype: str
        """

        return self._currentDirectory

    @property
    def currentFilename(self):
        """
        Getter method that returns the current file name with extension.

        :rtype: str
        """

        return self._currentFilename

    @property
    def currentName(self):
        """
        Getter method that returns the current file name.

        :rtype: str
        """

        return self._currentName

    @property
    def currentExtension(self):
        """
        Getter method that returns the current file extension.

        :rtype: str
        """

        return self._currentExtension

    @property
    def currentIndex(self):
        """
        Getter method that returns the current position in the queue.

        :rtype: int
        """

        return self._currentIndex
    # endregion

    # region Methods
    def execute(self, *filePaths, checkout=False, preCallback=nullCallback, postCallback=nullCallback):
        """
        Executes the internal tasks on the supplied files.
        An additional callback can be supplied if an external class requires progress updates.
        This callback should accept a 'filePath' and 'progress' keyword arguments.

        :type filePaths: Union[str, List[str]]
        :type checkout: bool
        :type preCallback: Callable
        :type postCallback: Callable
        :rtype: None
        """

        # Iterate through files
        #
        fileCount = len(filePaths)

        progress = 0.0
        startTime = time.time()

        for (i, filePath) in enumerate(filePaths):

            # Check if scene file exists
            #
            self._currentFilePath = os.path.abspath(filePath)
            self._currentDirectory = os.path.dirname(self._currentFilePath)
            self._currentFilename = os.path.basename(self._currentFilePath)
            self._currentName, self._currentExtension = os.path.splitext(self._currentFilename)
            self._currentIndex = i

            if not os.path.exists(filePath):

                log.warning(f'Cannot locate file: {filePath}')
                continue

            # Check if scene can be opened
            #
            preCallback(filePath=filePath, progress=progress)

            if self.scene.isValidExtension(filePath):

                log.info(f'Opening scene file: {filePath}')
                self.scene.open(filePath)

            # Check if file should be checked out
            #
            if checkout:

                p4utils.tryCheckout(filePath)

            # Execute tasks on current file
            #
            results = filePath

            for task in self.tasks:

                self._currentTask = task
                results = task.doIt(results, taskManager=self)

            # Update progress
            #
            progress = (float(i + 1) / float(fileCount)) * 100.0
            postCallback(filePath=filePath, progress=progress)

        # Notify user of time taken
        #
        endTime = time.time()
        timeDelta = endTime - startTime

        log.info('%s file(s) batched in %s!' % (fileCount, time.strftime('%H hours %M minutes and %S seconds', time.gmtime(timeDelta))))
    # endregion

    # region Callbacks
    def taskAdded(self, index, task):
        """
        Adds a reference of this manager to the supplied task.

        :type index: int
        :type task: abstracttask.AbstractTask
        :rtype: None
        """

        task._taskManager = weakref.ref(self)

    def taskRemoved(self, task):
        """
        Removes the reference of this manager from the supplied task.

        :type task: abstracttask.AbstractTask
        :rtype: None
        """

        task._taskManager = self.nullWeakReference
    # endregion
