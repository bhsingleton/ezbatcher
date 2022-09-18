import os
import webbrowser

from Qt import QtCore, QtWidgets, QtGui
from dcc import fnscene
from dcc.perforce import cmds
from dcc.json import jsonutils
from dcc.ui import quicwindow
from dcc.ui.models import qfileitemmodel, qfileexploreritemmodel, qpsonitemmodel, qpsonstyleditemdelegate
from dcc.generators.consecutivepairs import consecutivePairs
from ..libs import taskmanager, taskfactory

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QEzBatcher(quicwindow.QUicWindow):
    """
    Overload of QUicWindow that interfaces with the task manager framework.
    """

    cwdChanged = QtCore.Signal(str)

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Declare private variables
        #
        self._taskManager = taskmanager.TaskManager()
        self._taskFactory = taskfactory.TaskFactory.getInstance(asWeakReference=True)
        self._taskConstructor = None
        self._scene = fnscene.FnScene()
        self._currentFilePath = ''

        # Declare public variables
        #
        self.explorerItemModel = None
        self.queueItemModel = None
        self.taskItemModel = None
        self.taskStyledItemDelegate = None
        self.taskMenu = None
        self.taskActionGroup = None

        # Call parent method
        #
        super(QEzBatcher, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def scene(self):
        """
        Getter methods that returns the scene interface.

        :rtype: fnscene.FnScene
        """

        return self._scene

    @property
    def taskManager(self):
        """
        Getter methods that returns the task manager.

        :rtype: taskmanager.TaskManager
        """

        return self._taskManager

    @taskManager.setter
    def taskManager(self, taskManager):
        """
        Setter methods that updates the task manager.

        :type taskManager: taskmanager.TaskManager
        :rtype: None
        """

        self._taskManager = taskManager
        self.taskItemModel.invisibleRootItem = self._taskManager

    @property
    def taskFactory(self):
        """
        Getter methods that returns the task factory.

        :rtype: taskfactory.TaskFactory
        """

        return self._taskFactory()

    @property
    def taskConstructor(self):
        """
        Getter method that returns the current task constructor.

        :rtype: class
        """

        return self._taskConstructor

    @property
    def currentFilePath(self):
        """
        Returns the current task manager file path.

        :rtype: str
        """

        return self._currentFilePath
    # endregion

    # region Methods
    def postLoad(self):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QEzBatcher, self).postLoad()

        # Initialize explorer item model
        #
        self.explorerItemModel = qfileexploreritemmodel.QFileExplorerItemModel(parent=self)
        self.explorerItemModel.setObjectName('explorerItemModel')

        self.cwdLineEdit.textChanged.connect(self.explorerItemModel.setCwd)
        self.cwdLineEdit.setText(self.scene.currentProjectDirectory())

        self.explorerTreeView.setModel(self.explorerItemModel)

        # Initialize queue item model
        #
        self.queueItemModel = qfileitemmodel.QFileItemModel(parent=self)
        self.queueItemModel.setObjectName('queueItemModel')

        self.queueTableView.setModel(self.queueItemModel)
        self.queueTableView.installEventFilter(self)

        # Initialize task item model
        #
        self.taskItemModel = qpsonitemmodel.QPSONItemModel(parent=self)
        self.taskItemModel.setObjectName('taskItemModel')
        self.taskItemModel.invisibleRootItem = self.taskManager
        self.taskItemModel.invisibleRootProperty = 'tasks'

        self.taskStyledItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self)

        self.taskTreeView.setModel(self.taskItemModel)
        self.taskTreeView.setItemDelegate(self.taskStyledItemDelegate)
        self.taskTreeView.installEventFilter(self)

        # Initialize task action group
        #
        self.taskActionGroup = QtWidgets.QActionGroup(self.taskMenu)
        self.taskActionGroup.setExclusive(True)
        self.taskActionGroup.triggered.connect(self.on_taskActionGroup_triggered)

        for (name, cls) in self.taskFactory.classes().items():

            action = QtWidgets.QAction(cls.title, parent=self.taskActionGroup)
            action.setWhatsThis(name)
            action.setCheckable(True)

            self.taskActionGroup.addAction(action)

        # Add actions to menu
        #
        self.taskMenu = QtWidgets.QMenu(parent=self.addTaskDropDownButton)
        self.addTaskDropDownButton.setMenu(self.taskMenu)

        actions = self.taskActionGroup.actions()
        numActions = len(actions)

        if numActions > 0:

            self.taskMenu.addActions(actions)
            actions[0].trigger()

    def eventFilter(self, watched, event):
        """
        Filters events if this object has been installed as an event filter for the watched object.
        If you want to filter the event out, i.e. stop it being handled further, return true; otherwise return false.

        :type watched: QtWidgets.QWidget
        :type event: QtCore.QEvent
        :rtype: bool
        """

        # Inspect event type
        #
        if event.type() == QtCore.QEvent.KeyPress:

            # Check if delete key was pressed
            #
            if event.key() not in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete):

                return False

            # Check which widget triggered the event
            #
            if watched is self.queueTableView:

                self.removeSelectedFiles()

            elif watched is self.taskTreeView:

                self.removeSelectedTasks()

            else:

                pass

            return True

        else:

            return False

    def cwd(self):
        """
        Returns the current working directory.

        :rtype: str
        """

        return self.cwdLineEdit.text()

    def setCwd(self, cwd):
        """
        Updates the current working directory.

        :type cwd: str
        :rtype: None
        """

        self.cwdLineEdit.setText(cwd)

    def newFile(self):
        """
        Clears all the active tasks.

        :rtype: None
        """

        self.clearTasks()

    def openFile(self, filePath):
        """
        Loads a task manager from the supplied file path.

        :type filePath: str
        :rtype: None
        """

        self.taskManager = jsonutils.load(filePath)
        self._currentFilePath = filePath

    def saveFile(self, filePath, taskManager):
        """
        Serializes the current task manager to the specified path.

        :type filePath: str
        :type taskManager: taskmanager.TaskManager
        :rtype: None
        """

        jsonutils.dump(filePath, taskManager)
        self._currentFilePath = filePath

    def removeSelectedFiles(self):
        """
        Removes any selected files from the queue item model.

        :rtype: None
        """

        selectedRows = [index.row() for index in self.queueTableView.selectedIndexes() if index.column() == 0]

        for (start, end) in reversed(tuple(consecutivePairs(selectedRows))):

            numRows = (end - start) + 1
            self.queueItemModel.removeRows(start, numRows)

    def removeSelectedTasks(self):
        """
        Removes any selected tasks from the task item model.

        :rtype: None
        """

        selectedRows = [self.taskItemModel.topLevelIndex(index).row() for index in self.taskTreeView.selectedIndexes() if index.column() == 0]

        for (start, end) in reversed(tuple(consecutivePairs(selectedRows))):

            numRows = (end - start) + 1
            self.taskItemModel.removeRows(start, numRows)

    def clearTasks(self):
        """
        Removes all tasks from the task manager.

        :rtype: None
        """

        numTasks = len(self.taskManager.tasks)

        if numTasks > 0:

            self.taskItemModel.removeRows(0, numTasks)
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_newAction_triggered(self, checked=False):
        """
        Slot method for the newAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        self.newFile()

    @QtCore.Slot(bool)
    def on_openAction_triggered(self, checked=False):
        """
        Slot method for the openAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for save path
        #
        filePath = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open',
            dir=self.cwd(),
            filter='JSON (*.json)'
        )

        # Check if path is valid
        #
        if os.path.exists(filePath) and os.path.isfile(filePath):

            self.openFile(filePath)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_saveAction_triggered(self, checked=False):
        """
        Slot method for the saveAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Check if current file exists
        #
        if os.path.exists(self.currentFilePath):

            self.saveFile(self.currentFilePath, self.taskManager)

        else:

            self.saveAsAction.trigger()  # Prompt user for new save path!

    @QtCore.Slot(bool)
    def on_saveAsAction_triggered(self, checked=False):
        """
        Slot method for the saveAsAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for save path
        #
        savePath = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save As',
            dir=self.cwd(),
            filter='JSON files (*.json)'
        )

        # Check if path is valid
        #
        if savePath:

            self.saveFile(savePath, self.taskManager)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_usingEzBatcherAction_triggered(self, checked=False):
        """
        Slot method for the usingEzBatcherAction's triggered signal.

        :type checked: bool
        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/ezbatcher')

    @QtCore.Slot(bool)
    def on_cwdPushButton_clicked(self, checked=False):
        """
        Slot method for the cwdPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for current working directory
        #
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select Current Working Directory',
            dir=self.cwd(),
            options=QtWidgets.QFileDialog.ShowDirsOnly
        )

        # Check if path is valid
        # A null value will be returned if the user exited
        #
        if os.path.isdir(directory) and os.path.exists(directory):

            self.setCwd(directory)

        else:

            log.info('Operation aborted.')

    @QtCore.Slot(bool)
    def on_addTaskDropDownButton_clicked(self, checked=False):
        """
        Slot method for the addTaskDropDownButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Check if constructor is callable
        #
        if not callable(self.taskConstructor):

            return

        # Append task to model
        #
        task = self.taskConstructor()
        self.taskItemModel.appendRow(task)

    @QtCore.Slot(QtWidgets.QAction)
    def on_taskActionGroup_triggered(self, action):
        """
        Slot method for the taskActionGroup's triggered signal.

        :type action: QtWidgets.QAction
        :rtype: None
        """

        # Update button text
        #
        text = 'Add "{task}" Task'.format(task=action.text())
        self.addTaskDropDownButton.setText(text)

        # Store associated constructor
        #
        self._taskConstructor = self.taskFactory[action.whatsThis()]

    @QtCore.Slot(bool)
    def on_removeTaskPushButton_clicked(self, checked=False):
        """
        Slot method for the removeTaskPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        self.removeSelectedTasks()

    @QtCore.Slot(bool)
    def on_batchPushButton_clicked(self, checked=False):
        """
        Slot method for the batchPushButton's clicked signal.

        :type checked: bool
        :rtype: None
        """

        # Iterate through paths
        #
        paths = self.queueItemModel.paths()
        numPaths = len(paths)

        for (i, path) in enumerate(paths):

            # Check if file should be checked out
            #
            filePath = str(path)

            if self.checkoutCheckBox.isChecked():

                cmds.edit(filePath)

            # Execute tasks on file
            #
            self.taskManager.execute(filePath)

            # Update progress bar
            #
            progress = (float(i) / float(numPaths - 1)) * 100.0
            self.progressBar.setValue(progress)
    # endregion
