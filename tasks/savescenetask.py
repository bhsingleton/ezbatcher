import os

from dcc import fnscene
from dcc.python import stringutils
from dcc.ui import qdirectoryedit
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class SaveSceneTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that commits any changes made to the open scene file.
    """

    # region Dunderscores
    __slots__ = ('_directory', '_search', '_replace', '_extension')
    __title__ = 'Save Scene'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
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

        # Check if task manager exists
        #
        taskManager = kwargs.get('taskManager', None)

        if taskManager is None:

            raise TypeError('doIt() expects a valid task manager!')

        # Get directory and filename
        #
        directory, filename = '', ''

        if self.scene.isNewScene():

            # Evaluate file from task manager
            #
            directory, filename = os.path.split(taskManager.currentFile)
            name, extension = os.path.splitext(filename)

            if not self.scene.isValidExtension(extension):

                filename = '{name}.{extension}'.format(name=name, extension=self.extension.name)

        else:

            # Evaluate open scene file
            #
            directory = self.scene.currentDirectory()
            filename = self.scene.currentFilename()

        # Check if a search and replace is required
        #
        if not stringutils.isNullOrEmpty(self.search):

            filename = filename.replace(self.search, self.replace)

        # Check if a directory was supplied
        #
        filePath = None

        if not stringutils.isNullOrEmpty(self.directory):

            filePath = os.path.join(self.directory, filename)

        else:

            filePath = os.path.join(directory, filename)

        # Save changes to file
        #
        log.info('Saving changes to: %s' % filePath)
        self.scene.ensureDirectory(filePath)
        self.scene.saveAs(filePath)
    # endregion
