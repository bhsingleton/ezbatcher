import os
import stat

from dcc.python import stringutils
from dcc.ui import qdirectoryedit
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SaveSceneTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that commits any changes made to the open scene file.
    """

    # region Dunderscores
    __slots__ = ('_filename', '_directory', '_search', '_replace', '_extension')
    __title__ = 'Save Scene'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._filename = kwargs.get('filename', '')
        self._directory = kwargs.get('directory', '')
        self._search = kwargs.get('search', '')
        self._replace = kwargs.get('replace', '')
        self._extension = kwargs.get('extension', self.scene.FileExtensions(0))

        # Call parent method
        #
        super(SaveSceneTask, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def filename(self):
        """
        Getter method that returns the name to save as.

        :rtype: str
        """

        return self._filename

    @filename.setter
    def filename(self, filename):
        """
        Setter method that updates the name to save as.

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
    def search(self):
        """
        Getter method that returns the string pattern to search for.

        :rtype: str
        """

        return self._search

    @search.setter
    def search(self, search):
        """
        Setter method that updates the string pattern to search for.

        :type search: str
        :rtype: None
        """

        self._search = search

    @property
    def replace(self):
        """
        Getter method that returns the string to replace the search pattern with.

        :rtype: str
        """

        return self._replace

    @replace.setter
    def replace(self, replace):
        """
        Setter method that updates the string to replace the search pattern with.

        :type replace: str
        :rtype: None
        """

        self._replace = replace

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

            return super(SaveSceneTask, cls).createEditor(name, parent=parent)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if a directory was supplied
        # If not, then use the current file's directory
        #
        directory = None

        if not stringutils.isNullOrEmpty(self.directory):

            directory = os.path.abspath(self.directory)

        else:

            directory = self.taskManager.currentDirectory

        # Check if a filename was supplied
        # Again, if not, the use the current file's name
        #
        filename = None

        if not stringutils.isNullOrEmpty(self.filename):

            name = self.filename.format(name=self.taskManager.currentName, index=(self.taskManager.currentIndex + 1))
            filename = f'{name}.{self.extension.name}'

        elif self.scene.isValidExtension(self.taskManager.currentExtension):

            filename = self.taskManager.currentFilename

        else:

            filename = f'{self.taskManager.currentName}.{self.extension.name}'

        # Check if a search and replace is required
        #
        if not stringutils.isNullOrEmpty(self.search):

            filename = filename.replace(self.search, self.replace)

        # Save scene to specified path
        #
        filePath = os.path.join(directory, filename)
        log.info(f'Saving changes to: {filePath}')

        if os.path.exists(filePath):

            # Check if file is read-only
            #
            isWritable = os.access(filePath, os.W_OK)

            if not isWritable:

                os.chmod(filePath, stat.S_IWRITE)

            self.scene.saveAs(filePath)

        else:

            # Ensure directories exist and save file
            #
            self.scene.ensureDirectory(filePath)
            self.scene.saveAs(filePath)
    # endregion
