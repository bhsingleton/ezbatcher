import os

from dcc.ui import qfileedit
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class OpenSceneTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that opens a scene file.
    """

    # region Dunderscores
    __slots__ = ('_filePath', '_reopenCurrentFile')
    __title__ = 'Open Scene'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._filePath = kwargs.get('filePath', '')
        self._reopenCurrentFile = kwargs.get('reopenCurrentFile', False)

        # Call parent method
        #
        super(OpenSceneTask, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def filePath(self):
        """
        Getter method that returns the file path for the new reference.

        :rtype: str
        """

        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        """
        Setter method that updates the file path for the new reference.

        :type filePath: str
        :rtype: None
        """

        self._filePath = filePath

    @property
    def reopenCurrentFile(self):
        """
        Getter method that returns the "reopenCurrentFile" flag.

        :rtype: bool
        """

        return self._reopenCurrentFile

    @reopenCurrentFile.setter
    def reopenCurrentFile(self, reopenCurrentFile):
        """
        Setter method that updates the "reopenCurrentFile" flag.

        :type reopenCurrentFile: bool
        :rtype: None
        """

        self._reopenCurrentFile = reopenCurrentFile
    # endregion

    # region Methods
    @classmethod
    def createEditor(cls, name, parent=None):
        """
        Returns a Qt editor for the specified property.

        :type name: str
        :type parent: Union[QtWidgets.QWidget, None]
        :rtype: Union[QtWidgets.QWidget, None]
        """

        if name == 'filePath':

            return qfileedit.QFileEdit(parent=parent)

        else:

            return super(OpenSceneTask, cls).createEditor(name, parent=parent)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if current file should be reopened
        #
        taskManager = kwargs.get('taskManager', None)

        if self.reopenCurrentFile:

            self.scene.open(taskManager.currentFile)

        elif os.path.exists(self.filePath):

            self.scene.open(self.filePath)

        else:

            log.warning('Cannot locate scene file: %s' % self.filePath)
    # endregion
