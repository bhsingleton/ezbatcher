import os

from dcc import fnscene
from dcc.ui import qdirectoryedit
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class NewSceneTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that creates a new scene file.
    """

    # region Dunderscores
    __slots__ = ('_filename', '_directory', '_extension', '_useCurrentFilename')
    __title__ = 'New Scene'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._filename = kwargs.get('filename', '')
        self._directory = kwargs.get('directory', '')
        self._extension = kwargs.get('extension', self.scene.FileExtensions(0))
        self._useCurrentFilename = kwargs.get('useCurrentFilename', '')

        # Call parent method
        #
        super(NewSceneTask, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def filename(self):
        """
        Getter method that returns the file name to save as.

        :rtype: str
        """

        return self._filename

    @filename.setter
    def filename(self, filename):
        """
        Setter method that updates the file name to save as.

        :type filename: str
        :rtype: None
        """

        self._filename = filename

    @property
    def directory(self):
        """
        Getter method that returns the directory to save to.

        :rtype: str
        """

        return self._directory

    @directory.setter
    def directory(self, directory):
        """
        Setter method that updates the directory to save to.

        :type directory: str
        :rtype: None
        """

        self._directory = directory

    @property
    def extension(self):
        """
        Getter method that returns the file extension to save with.

        :rtype: fnscene.FnScene.FileExtensions
        """

        return self._extension

    @extension.setter
    def extension(self, extension):
        """
        Setter method that updates the file extension to save with.

        :type extension: fnscene.FnScene.FileExtensions
        :rtype: None
        """

        self._extension = self.scene.FileExtensions(extension)

    @property
    def useCurrentFilename(self):
        """
        Getter method that returns the `useCurrentFilename` flag.

        :rtype: bool
        """

        return self._useCurrentFilename

    @useCurrentFilename.setter
    def useCurrentFilename(self, useCurrentFilename):
        """
        Setter method that updates the `useCurrentFilename` flag.

        :type useCurrentFilename: bool
        :rtype: None
        """

        self._useCurrentFilename = useCurrentFilename
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

        if name == 'directory':

            return qdirectoryedit.QDirectoryEdit(parent=parent)

        else:

            return super(NewSceneTask, cls).createEditor(name, parent=parent)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Create new scene file
        #
        self.scene.new()

        # Check if scene should be saved
        #
        taskManager = kwargs.get('taskManager', None)
        filename = os.path.basename(taskManager.currentFile) if self.useCurrentFilename else self.filename

        if not self.scene.isNullOrEmpty(filename) and not self.scene.isNullOrEmpty(self.directory):

            name, extension = os.path.splitext(filename)
            filePath = os.path.join(self.directory, f'{name}.{self.extension.name}')

            self.scene.ensureDirectory(self.directory)
            self.scene.saveAs(filePath)
    # endregion
