import os
import sys
import json
import webbrowser

from Qt import QtCore, QtWidgets, QtGui
from dcc import fnscene
from dcc.json import jsonutils
from dcc.ui import qsingletonwindow, qdropdownbutton, qdirectoryedit
from dcc.ui.models import qfileitemmodel, qfileexploreritemmodel, qfileitemfiltermodel
from dcc.ui.models import qpsonitemmodel, qpsonstyleditemdelegate
from dcc.generators.consecutivepairs import consecutivePairs
from ..libs import taskmanager, taskfactory

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class QEzBatcher(qsingletonwindow.QSingletonWindow):
    """
    Overload of `QSingletonWindow` that interfaces with batchable tasks.
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

    def __setup_ui__(self, *args, **kwargs):
        """
        Private method that initializes the user interface.

        :rtype: None
        """

        # Call parent method
        #
        super(QEzBatcher, self).__setup_ui__(*args, **kwargs)

        # Initialize main window
        #
        self.setWindowTitle("|| Ez'Batcher")
        self.setMinimumSize(QtCore.QSize(500, 600))

        # Initialize main menu-bar
        #
        mainMenuBar = QtWidgets.QMenuBar()
        mainMenuBar.setObjectName('mainMenuBar')

        self.setMenuBar(mainMenuBar)

        # Initialize file menu
        #
        self.fileMenu = mainMenuBar.addMenu('&File')
        self.fileMenu.setObjectName('fileMenu')
        self.fileMenu.setTearOffEnabled(True)

        self.newAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/new_file.svg'), '&New', parent=self.fileMenu)
        self.newAction.setObjectName('newAction')
        self.newAction.triggered.connect(self.on_newAction_triggered)

        self.openAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/open_folder.svg'), '&Open', parent=self.fileMenu)
        self.openAction.setObjectName('openAction')
        self.openAction.triggered.connect(self.on_openAction_triggered)

        self.saveAction = QtWidgets.QAction(QtGui.QIcon(':/dcc/icons/open_folder.svg'), '&Save', parent=self.fileMenu)
        self.saveAction.setObjectName('saveAction')
        self.saveAction.triggered.connect(self.on_saveAction_triggered)

        self.saveAsAction = QtWidgets.QAction('Save As', parent=self.fileMenu)
        self.saveAsAction.setObjectName('saveAsAction')
        self.saveAsAction.triggered.connect(self.on_saveAsAction_triggered)

        self.fileMenu.addActions([self.newAction, self.openAction])
        self.fileMenu.addSeparator()
        self.fileMenu.addActions([self.saveAction, self.saveAsAction])

        # Initialize help menu
        #
        self.helpMenu = mainMenuBar.addMenu('&Help')
        self.helpMenu.setObjectName('helpMenu')
        self.helpMenu.setTearOffEnabled(True)

        self.usingEzBatcherAction = QtWidgets.QAction("Using Ez'Batcher", parent=self.helpMenu)
        self.usingEzBatcherAction.setObjectName('usingEzBatcherAction')
        self.usingEzBatcherAction.triggered.connect(self.on_usingEzBatcherAction_triggered)

        self.helpMenu.addAction(self.usingEzBatcherAction)

        # Initialize central widget
        #
        centralLayout = QtWidgets.QVBoxLayout()
        centralLayout.setObjectName('centralLayout')

        centralWidget = QtWidgets.QWidget()
        centralWidget.setObjectName('centralWidget')
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)

        # Initialize CWD line-edit
        #
        self.cwdLineEdit = qdirectoryedit.QDirectoryEdit()
        self.cwdLineEdit.setObjectName('cwdLineEdit')
        self.cwdLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.cwdLineEdit.setFixedHeight(24)
        self.cwdLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.cwdLineEdit.textChanged.connect(self.on_cwdLineEdit_textChanged)
        self.cwdLineEdit.returnPressed.connect(self.on_cwdLineEdit_returnPressed)
        self.cwdLineEdit.editingFinished.connect(self.on_cwdLineEdit_editingFinished)

        fileIconProvider = QtWidgets.QFileIconProvider()
        fileInfo = QtCore.QFileInfo(os.path.normpath(sys.executable))
        fileIcon = fileIconProvider.icon(fileInfo)

        self.assumeSceneDirectoryAction = QtWidgets.QAction(fileIcon, '', parent=self)
        self.assumeSceneDirectoryAction.setToolTip('Set directory to current scene.')
        self.assumeSceneDirectoryAction.triggered.connect(self.on_assumeSceneDirectoryAction_triggered)

        self.cwdLineEdit.addAction(self.assumeSceneDirectoryAction, QtWidgets.QLineEdit.LeadingPosition)

        centralLayout.addWidget(self.cwdLineEdit)

        # Initialize explorer group-box
        #
        self.explorerLayout = QtWidgets.QVBoxLayout()
        self.explorerLayout.setObjectName('explorerLayout')

        self.explorerGroupBox = QtWidgets.QGroupBox('Explorer')
        self.explorerGroupBox.setObjectName('explorerGroupBox')
        self.explorerGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.explorerGroupBox.setFlat(True)
        self.explorerGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.explorerGroupBox.setLayout(self.explorerLayout)

        self.explorerTableView = QtWidgets.QTableView()
        self.explorerTableView.setObjectName('explorerTableView')
        self.explorerTableView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.explorerTableView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.explorerTableView.setStyleSheet('QTableView::item { height: 24px; }')
        self.explorerTableView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.explorerTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.explorerTableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.explorerTableView.setDropIndicatorShown(True)
        self.explorerTableView.setDragEnabled(True)
        self.explorerTableView.setDragDropOverwriteMode(True)
        self.explorerTableView.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.explorerTableView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.explorerTableView.setAlternatingRowColors(True)
        self.explorerTableView.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.explorerTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.explorerTableView.setShowGrid(True)
        self.explorerTableView.setWordWrap(False)
        self.explorerTableView.doubleClicked.connect(self.on_explorerTableView_doubleClicked)

        self.explorerItemModel = qfileexploreritemmodel.QFileExplorerItemModel(parent=self)
        self.explorerItemModel.setObjectName('explorerItemModel')

        self.explorerItemFilterModel = qfileitemfiltermodel.QFileItemFilterModel(parent=self)
        self.explorerItemFilterModel.setObjectName('explorerItemFilterModel')
        self.explorerItemFilterModel.setSourceModel(self.explorerItemModel)
        self.explorerItemFilterModel.setRecursiveFilteringEnabled(True)

        self.explorerTableView.setModel(self.explorerItemFilterModel)

        horizontalHeader = self.explorerTableView.horizontalHeader()  # type: QtWidgets.QHeaderView
        horizontalHeader.setStretchLastSection(True)
        horizontalHeader.setVisible(False)

        verticalHeader = self.explorerTableView.verticalHeader()  # type: QtWidgets.QHeaderView
        verticalHeader.setStretchLastSection(False)
        verticalHeader.setVisible(False)

        self.explorerFilterLineEdit = QtWidgets.QLineEdit()
        self.explorerFilterLineEdit.setObjectName('explorerFilterLineEdit')
        self.explorerFilterLineEdit.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.explorerFilterLineEdit.setFixedHeight(24)
        self.explorerFilterLineEdit.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.explorerFilterLineEdit.setPlaceholderText('Filter Files (ex. *.txt)')
        self.explorerFilterLineEdit.setClearButtonEnabled(True)
        self.explorerFilterLineEdit.textChanged.connect(self.explorerItemFilterModel.setFilterWildcard)

        self.explorerLayout.addWidget(self.explorerFilterLineEdit)
        self.explorerLayout.addWidget(self.explorerTableView)

        # Initialize queue group-box
        #
        self.queueLayout = QtWidgets.QVBoxLayout()
        self.queueLayout.setObjectName('queueLayout')

        self.queueGroupBox = QtWidgets.QGroupBox('Queue')
        self.queueGroupBox.setObjectName('queueGroupBox')
        self.queueGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.queueGroupBox.setFlat(True)
        self.queueGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.queueGroupBox.setLayout(self.queueLayout)

        self.queueTableView = QtWidgets.QTableView()
        self.queueTableView.setObjectName('queueTableView')
        self.queueTableView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.queueTableView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.queueTableView.setStyleSheet('QTableView::item { height: 24px; }')
        self.queueTableView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.queueTableView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.queueTableView.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.queueTableView.setDropIndicatorShown(True)
        self.queueTableView.setDragEnabled(True)
        self.queueTableView.setDragDropOverwriteMode(False)
        self.queueTableView.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.queueTableView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.queueTableView.setAlternatingRowColors(True)
        self.queueTableView.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.queueTableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.queueTableView.setShowGrid(True)
        self.queueTableView.setWordWrap(False)

        self.queueItemModel = qfileitemmodel.QFileItemModel(parent=self)
        self.queueItemModel.setObjectName('queueItemModel')

        self.queueTableView.setModel(self.queueItemModel)
        self.queueTableView.installEventFilter(self)

        horizontalHeader = self.queueTableView.horizontalHeader()  # type: QtWidgets.QHeaderView
        horizontalHeader.setStretchLastSection(True)
        horizontalHeader.setVisible(False)

        verticalHeader = self.queueTableView.verticalHeader()  # type: QtWidgets.QHeaderView
        verticalHeader.setStretchLastSection(False)
        verticalHeader.setVisible(False)

        self.queueLayout.addWidget(self.queueTableView)

        # Initialize file splitter
        #
        self.fileSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.fileSplitter.setObjectName('fileSplitter')
        self.fileSplitter.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.fileSplitter.addWidget(self.explorerGroupBox)
        self.fileSplitter.addWidget(self.queueGroupBox)

        # Initialize task widget
        #
        self.taskLayout = QtWidgets.QVBoxLayout()
        self.taskLayout.setObjectName('taskLayout')

        self.taskGroupBox = QtWidgets.QGroupBox('Tasks')
        self.taskGroupBox.setObjectName('queueGroupBox')
        self.taskGroupBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.taskGroupBox.setFlat(True)
        self.taskGroupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.taskGroupBox.setLayout(self.taskLayout)

        self.taskTreeView = QtWidgets.QTreeView()
        self.taskTreeView.setObjectName('taskTreeView')
        self.taskTreeView.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.taskTreeView.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.taskTreeView.setStyleSheet('QTreeView::item { height: 24px; }')
        self.taskTreeView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.taskTreeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.taskTreeView.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.taskTreeView.setDropIndicatorShown(True)
        self.taskTreeView.setDragEnabled(True)
        self.taskTreeView.setDragDropOverwriteMode(False)
        self.taskTreeView.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.taskTreeView.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.taskTreeView.setAlternatingRowColors(True)
        self.taskTreeView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.taskTreeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.taskTreeView.setUniformRowHeights(True)
        self.taskTreeView.setAnimated(True)
        self.taskTreeView.setExpandsOnDoubleClick(False)

        self.taskItemModel = qpsonitemmodel.QPSONItemModel(parent=self)
        self.taskItemModel.setObjectName('taskItemModel')
        self.taskItemModel.invisibleRootItem = self.taskManager
        self.taskItemModel.invisibleRootProperty = 'tasks'

        self.taskStyledItemDelegate = qpsonstyleditemdelegate.QPSONStyledItemDelegate(parent=self)
        self.taskStyledItemDelegate.setObjectName('taskStyledItemDelegate')

        self.taskTreeView.setModel(self.taskItemModel)
        self.taskTreeView.setItemDelegate(self.taskStyledItemDelegate)
        self.taskTreeView.installEventFilter(self)

        horizontalHeader = self.taskTreeView.header()  # type: QtWidgets.QHeaderView
        horizontalHeader.setDefaultSectionSize(200)
        horizontalHeader.setMinimumSectionSize(100)
        horizontalHeader.setStretchLastSection(True)
        horizontalHeader.setVisible(True)

        self.addTaskDropDownButton = qdropdownbutton.QDropDownButton('Add')
        self.addTaskDropDownButton.setObjectName('addTaskDropDownButton')
        self.addTaskDropDownButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.addTaskDropDownButton.setFixedHeight(24)
        self.addTaskDropDownButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.addTaskDropDownButton.clicked.connect(self.on_addTaskDropDownButton_clicked)

        self.removeTaskPushButton = QtWidgets.QPushButton('Remove')
        self.removeTaskPushButton.setObjectName('removeTaskPushButton')
        self.removeTaskPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.removeTaskPushButton.setFixedHeight(24)
        self.removeTaskPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.removeTaskPushButton.clicked.connect(self.on_removeTaskPushButton_clicked)

        self.horizontalSpacer = QtWidgets.QSpacerItem(24, 24, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.checkoutCheckBox = QtWidgets.QCheckBox('Checkout')
        self.checkoutCheckBox.setObjectName('checkoutCheckBox')
        self.checkoutCheckBox.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.checkoutCheckBox.setFixedHeight(24)
        self.checkoutCheckBox.setFocusPolicy(QtCore.Qt.NoFocus)
        self.checkoutCheckBox.clicked.connect(self.on_checkoutCheckBox_clicked)

        self.batchPushButton = QtWidgets.QPushButton('Batch')
        self.batchPushButton.setObjectName('batchPushButton')
        self.batchPushButton.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.batchPushButton.setFixedHeight(24)
        self.batchPushButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.batchPushButton.clicked.connect(self.on_batchPushButton_clicked)

        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.buttonsLayout.setObjectName('buttonsLayout')
        self.buttonsLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonsLayout.addWidget(self.addTaskDropDownButton)
        self.buttonsLayout.addWidget(self.removeTaskPushButton)
        self.buttonsLayout.addItem(self.horizontalSpacer)
        self.buttonsLayout.addWidget(self.checkoutCheckBox)
        self.buttonsLayout.addWidget(self.batchPushButton)

        self.taskLayout.addWidget(self.taskTreeView)
        self.taskLayout.addLayout(self.buttonsLayout)

        # Initialize task action-group
        #
        self.taskMenu = QtWidgets.QMenu(parent=self.addTaskDropDownButton)
        self.taskMenu.setObjectName('taskMenu')

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
        actions = self.taskActionGroup.actions()
        numActions = len(actions)

        if numActions > 0:

            self.taskMenu.addActions(actions)
            actions[0].trigger()

        self.addTaskDropDownButton.setMenu(self.taskMenu)

        # Initialize main splitter
        #
        self.mainSplitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.mainSplitter.setObjectName('splitter')
        self.mainSplitter.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.mainSplitter.addWidget(self.fileSplitter)
        self.mainSplitter.addWidget(self.taskGroupBox)

        centralLayout.addWidget(self.mainSplitter)

        # Initialize progress-bar
        #
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setObjectName('progressBar')
        self.progressBar.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        self.progressBar.setFixedHeight(24)
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setFormat('%p%')

        centralLayout.addWidget(self.progressBar)

        # Connect window signals
        #
        self.cwdChanged.connect(self.cwdLineEdit.setText)
        self.cwdChanged.connect(self.explorerItemModel.setCwd)
        self.cwd = self.scene.currentProjectDirectory()

        self.checkoutChanged.connect(self.checkoutCheckBox.setChecked)
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

        isDirectory = os.path.isdir(cwd)
        isSameDirectory = self.isSameFile(cwd, self._cwd)

        if (isDirectory and not isSameDirectory) and isinstance(cwd, str):

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

        if checkout != self._checkout and isinstance(checkout, bool):

            self._checkout = checkout
            self.checkoutChanged.emit(self._checkout)
    # endregion

    # region Methods
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
        self.cwd = settings.value('editor/cwd', defaultValue=self.scene.currentProjectDirectory(), type=str)
        self.checkout = bool(settings.value('editor/checkout', defaultValue=0, type=int))

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

        self.setWindowTitle("|| Ez'Batcher")

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

        self.setWindowTitle(f"|| {self._currentFilename} - Ez'Batcher: {self._currentFilePath}")

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

        self.setWindowTitle(f"|| {self._currentFilename} - Ez'Batcher: {self._currentFilePath}")

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
        Slot method for the `newAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        self.newFile()

    @QtCore.Slot(bool)
    def on_openAction_triggered(self, checked=False):
        """
        Slot method for the `openAction` widget's `triggered` signal.

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
        Slot method for the `saveAction` widget's `triggered` signal.

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
        Slot method for the `saveAsAction` widget's `triggered` signal.

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
        Slot method for the `usingEzBatcherAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        webbrowser.open('https://github.com/bhsingleton/ezbatcher')

    @QtCore.Slot(bool)
    def on_assumeSceneDirectoryAction_triggered(self, checked=False):
        """
        Slot method for the `assumeSceneDirectoryAction` widget's `triggered` signal.

        :type checked: bool
        :rtype: None
        """

        if not self.scene.isNewScene():

            self.cwd = self.scene.currentDirectory()

    @QtCore.Slot(str)
    def on_cwdLineEdit_textChanged(self, text):
        """
        Slot method for the `cwdLineEdit` widget's `textChanged` signal.

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
        Slot method for the `cwdLineEdit` widget's `editingFinished` signal.

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
        Slot method for the `cwdLineEdit` widget's `returnPressed` signal.

        :rtype: None
        """

        sender = self.sender()
        sender.clearFocus()

    @QtCore.Slot(QtCore.QModelIndex)
    def on_explorerTableView_doubleClicked(self, index):
        """
        Slot method for the `explorerTableView` widget's `doubleClicked` signal.

        :type index: QtCore.QModelIndex
        :rtype: None
        """

        sourceIndex = self.explorerItemFilterModel.mapToSource(index)
        path = self.explorerItemModel.pathFromIndex(sourceIndex)

        if path.isDir():

            self.cwd = str(path)

    @QtCore.Slot(bool)
    def on_checkoutCheckBox_clicked(self, checked=False):
        """
        Slot method for the `checkoutCheckBox` widget's `clicked` signal.

        :type checked: bool
        :rtype: None
        """

        self.checkout = checked

    @QtCore.Slot()
    def on_addTaskDropDownButton_clicked(self):
        """
        Slot method for the `addTaskDropDownButton` widget's `clicked` signal.

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
        Slot method for the `taskActionGroup` widget's `triggered` signal.

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

    @QtCore.Slot()
    def on_removeTaskPushButton_clicked(self):
        """
        Slot method for the `removeTaskPushButton` widget's `clicked` signal.

        :rtype: None
        """

        self.removeSelectedTasks()

    @QtCore.Slot(bool)
    def on_batchPushButton_clicked(self):
        """
        Slot method for the `batchPushButton` widget's `clicked` signal.

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
