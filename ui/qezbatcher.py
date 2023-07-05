import os
import sys
import json
import webbrowser

from Qt import QtCore, QtWidgets, QtGui
from dcc import fnscene
from dcc.json import jsonutils
from dcc.ui import quicwindow
from dcc.ui.models import qfileitemmodel, qfileexploreritemmodel, qfileitemfiltermodel
from dcc.ui.models import qpsonitemmodel, qpsonstyleditemdelegate
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

    # region Signals
    cwdChanged = QtCore.Signal(str)
    checkoutChanged = QtCore.Signal(bool)
    # endregion

    # region Dunderscores
    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance has been created.

        :key parent: QtWidgets.QWidget
        :key flags: QtCore.Qt.WindowFlags
        :rtype: None
        """

        # Call parent method
        #
        super(QEzBatcher, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._taskManager = taskmanager.TaskManager()
        self._taskFactory = taskfactory.TaskFactory.getInstance(asWeakReference=True)
        self._taskConstructor = None
        self._scene = fnscene.FnScene()
        self._cwd = ''
        self._checkout = False
        self._currentFilePath = ''
        self._currentFilename = ''

        # Declare public variables
        #
        self.fileMenu = None
        self.newAction = None
        self.openAction = None
        self.saveAction = None
        self.saveAsAction = None

        self.helpMenu = None
        self.usingEzBatcherAction = None

        self.mainSplitter = None
        self.fileWidget = None
        self.cwdLineEdit = None
        self.fileSplitter = None
        self.explorerGroupBox = None
        self.explorerFilterLineEdit = None
        self.explorerTreeView = None
        self.explorerItemModel = None
        self.explorerItemFilterModel = None
        self.queueGroupBox = None
        self.queueTableView = None
        self.queueItemModel = None

        self.taskGroupBox = None
        self.taskTreeView = None
        self.taskItemModel = None
        self.taskStyledItemDelegate = None
        self.buttonsWidget = None
        self.addTaskDropDownButton = None
        self.removeTaskPushButton = None
        self.checkoutCheckBox = None
        self.batchPushButton = None
        self.progressBar = None

        self.taskMenu = None
        self.assumeSceneDirectoryAction = None
        self.taskActionGroup = None
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

    @property
    def cwd(self):
        """
        Getter method that returns the current working directory.

        :rtype: str
        """

        return self._cwd

    @cwd.setter
    def cwd(self, cwd):
        """
        Setter method that updates the current working directory.

        :type cwd: str
        :rtype: None
        """

        if os.path.isdir(cwd) and not self.isSameFile(cwd, self._cwd):

            self._cwd = os.path.normpath(os.path.expandvars(cwd))
            self.cwdChanged.emit(self.cwd)

    @property
    def checkout(self):
        """
        Getter method that returns the "checkout" flag.

        :rtype: bool
        """

        return self._checkout

    @checkout.setter
    def checkout(self, checkout):
        """
        Setter method that updates the "checkout" flag.

        :type checkout: bool
        :rtype: None
        """

        if checkout != self._checkout:

            self._checkout = checkout
            self.checkoutChanged.emit(self._checkout)
    # endregion

    # region Methods
    def postLoad(self, *args, **kwargs):
        """
        Called after the user interface has been loaded.

        :rtype: None
        """

        # Call parent method
        #
        super(QEzBatcher, self).postLoad(*args, **kwargs)

        # Initialize file explorer item model
        #
        self.explorerItemModel = qfileexploreritemmodel.QFileExplorerItemModel(parent=self)
        self.explorerItemModel.setObjectName('explorerItemModel')

        self.explorerItemFilterModel = qfileitemfiltermodel.QFileItemFilterModel(parent=self)
        self.explorerItemFilterModel.setObjectName('explorerItemFilterModel')
        self.explorerItemFilterModel.setSourceModel(self.explorerItemModel)
        self.explorerItemFilterModel.setRecursiveFilteringEnabled(True)

        self.explorerFilterLineEdit.textChanged.connect(self.explorerItemFilterModel.setFilterWildcard)
        self.explorerTreeView.setModel(self.explorerItemFilterModel)

        # Initialize file queue item model
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
        self.taskStyledItemDelegate.setObjectName('taskStyledItemDelegate')

        self.taskTreeView.setModel(self.taskItemModel)
        self.taskTreeView.setItemDelegate(self.taskStyledItemDelegate)
        self.taskTreeView.installEventFilter(self)

        # Initialize task action group
        #
        self.taskActionGroup = QtWidgets.QActionGroup(self.taskMenu)
        self.taskActionGroup.setObjectName('taskActionGroup')
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
        self.taskMenu.setObjectName('taskMenu')

        actions = self.taskActionGroup.actions()
        numActions = len(actions)

        if numActions > 0:

            self.taskMenu.addActions(actions)
            actions[0].trigger()

        self.addTaskDropDownButton.setMenu(self.taskMenu)

        # Initialize CWD line edit
        #
        fileIconProvider = QtWidgets.QFileIconProvider()
        icon = fileIconProvider.icon(os.path.normpath(sys.executable))

        self.assumeSceneDirectoryAction = QtWidgets.QAction(icon, '', parent=self)
        self.assumeSceneDirectoryAction.setToolTip('Set directory to current scene.')
        self.assumeSceneDirectoryAction.triggered.connect(self.on_assumeSceneDirectoryAction_triggered)

        self.cwdLineEdit.addAction(self.assumeSceneDirectoryAction, QtWidgets.QLineEdit.LeadingPosition)

        # Connect property signals
        #
        self.cwdChanged.connect(self.cwdLineEdit.setText)
        self.cwdChanged.connect(self.explorerItemModel.setCwd)
        self.cwd = self.scene.currentProjectDirectory()

        self.checkoutChanged.connect(self.checkoutCheckBox.setChecked)

    def loadSettings(self, settings):
        """
        Loads the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QEzBatcher, self).loadSettings(settings)

        # Load user preferences
        #
        self.cwd = settings.value('editor/cwd', defaultValue=self.scene.currentProjectDirectory())
        self.checkout = bool(settings.value('editor/checkout', defaultValue=0))

    def saveSettings(self, settings):
        """
        Saves the user settings.

        :type settings: QtCore.QSettings
        :rtype: None
        """

        # Call parent method
        #
        super(QEzBatcher, self).saveSettings(settings)

        # Save user preferences
        #
        settings.setValue('editor/cwd', self.cwd)
        settings.setValue('editor/checkout', int(self.checkout))

    def newFile(self):
        """
        Clears all the active tasks.

        :rtype: None
        """

        # Clear tasks
        #
        self.clearTasks()

        # Reset window title
        #
        self._currentFilePath = ''
        self._currentFilename = ''

        self.setWindowTitle('EzBatcher')

    def openFile(self, filePath):
        """
        Loads a task manager from the supplied file path.

        :type filePath: str
        :rtype: None
        """

        # Load task queue from file
        #
        self.taskManager = jsonutils.load(filePath)

        # Update window title
        #
        self._currentFilePath = os.path.abspath(filePath)
        self._currentFilename = os.path.basename(self._currentFilePath)

        self.setWindowTitle(f'{self._currentFilename} - EzBatcher: {self._currentFilePath}')

    def saveFile(self, filePath, taskManager):
        """
        Serializes the current task manager to the specified path.

        :type filePath: str
        :type taskManager: taskmanager.TaskManager
        :rtype: None
        """

        # Dump task queue to file
        #
        jsonutils.dump(filePath, taskManager, indent=4)

        # Update window title
        #
        self._currentFilePath = os.path.abspath(filePath)
        self._currentFilename = os.path.basename(self._currentFilePath)

        self.setWindowTitle(f'{self._currentFilename} - EzBatcher: {self._currentFilePath}')

    def isSameFile(self, path, otherPath):
        """
        Evaluates if the two supplied files are the same.

        :type path: str
        :type otherPath: str
        :rtype: bool
        """

        try:

            return os.path.samefile(path, otherPath)

        except FileNotFoundError:

            return False

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

    def updateProgressBar(self, filePath='', progress=0.0):
        """
        Updates the progressbar based on the supplied parameters.

        :type filePath: str
        :type progress: float
        :rtype: None
        """

        # Update progress bar format
        #
        if not self.scene.isNullOrEmpty(filePath):

            text = '{filename} - %p%'.format(filename=os.path.basename(filePath))
            self.progressBar.setFormat(text)

        else:

            self.progressBar.setFormat('%p%')

        # Update progress value
        #
        self.progressBar.setValue(progress)
    # endregion

    # region Events
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
    # endregion

    # region Slots
    @QtCore.Slot(bool)
    def on_newAction_triggered(self, checked=False):
        """
        Slot method for the newAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.newFile()

    @QtCore.Slot(bool)
    def on_openAction_triggered(self, checked=False):
        """
        Slot method for the openAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for save path
        #
        filePath, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(
            parent=self,
            caption='Open',
            dir=self.cwd,
            filter='JSON (*.json)'
        )

        # Check if path is valid
        #
        if os.path.isfile(filePath):

            self.openFile(filePath)

        else:

            log.info('Operation aborted...')

    @QtCore.Slot(bool)
    def on_saveAction_triggered(self, checked=False):
        """
        Slot method for the saveAction's `triggered` signal.

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
        Slot method for the saveAsAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        # Prompt user for save path
        #
        savePath, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption='Save As',
            dir=self.cwd,
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
        Slot method for the usingEzBatcherAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/ezbatcher')

    @QtCore.Slot(bool)
    def on_assumeSceneDirectoryAction_triggered(self, checked=False):
        """
        Slot method for the assumeSceneDirectoryAction's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        if not self.scene.isNewScene():

            self.cwd = self.scene.currentDirectory()

    @QtCore.Slot(str)
    def on_cwdLineEdit_textChanged(self, text):
        """
        Slot method for the cwdLineEdit's `textChanged` signal.

        :type text: str
        :rtype: None
        """

        if os.path.isdir(text):

            self.cwd = text

        else:

            pass  # Let the `editingFinished` signal clean this up!

    @QtCore.Slot()
    def on_cwdLineEdit_editingFinished(self):
        """
        Slot method for the cwdLineEdit's `editingFinished` signal.

        :rtype: None
        """

        sender = self.sender()
        text = sender.text()

        if os.path.isdir(text):

            self.cwd = text

        else:

            sender.setText(self.cwd)  # Revert changes

    @QtCore.Slot()
    def on_cwdLineEdit_returnPressed(self):
        """
        Slot method for the cwdLineEdit's `returnPressed` signal.

        :rtype: None
        """

        sender = self.sender()
        sender.clearFocus()

    @QtCore.Slot(bool)
    def on_checkoutCheckBox_clicked(self, checked=False):
        """
        Slot method for the checkoutCheckBox's `clicked` signal.

        :rtype: None
        """

        self.checkout = checked

    @QtCore.Slot(bool)
    def on_addTaskDropDownButton_clicked(self, checked=False):
        """
        Slot method for the addTaskDropDownButton's `clicked` signal.

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
        Slot method for the taskActionGroup's `triggered` signal.

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
        Slot method for the removeTaskPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        self.removeSelectedTasks()

    @QtCore.Slot(bool)
    def on_batchPushButton_clicked(self, checked=False):
        """
        Slot method for the batchPushButton's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        # Collect files to process
        #
        filePaths = list(map(str, self.queueItemModel.paths()))
        numFilePaths = len(filePaths)

        if numFilePaths == 0:

            QtWidgets.QMessageBox.warning()
            return

        # Execute tasks
        #
        self.taskManager.execute(
            *filePaths,
            checkout=self.checkoutCheckBox.isChecked(),
            preCallback=self.updateProgressBar,
            postCallback=self.updateProgressBar
        )
    # endregion
