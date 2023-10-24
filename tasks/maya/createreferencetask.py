import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.ui import qfileedit
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CreateReferenceTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that creates a new scene reference.
    """

    # region Dunderscores
    __slots__ = ('_filePath', '_namespace')
    __title__ = 'Create Reference'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(CreateReferenceTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._filePath = kwargs.get('filePath', '')
        self._namespace = kwargs.get('namespace', '')
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
    def namespace(self):
        """
        Getter method that returns the namespace for the new reference.

        :rtype: str
        """

        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        """
        Setter method that updates the namespace for the new reference.

        :type namespace: str
        :rtype: None
        """

        self._namespace = namespace
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

            return qfileedit.QFileEdit(filter='Maya Files (*.mb *.ma)', parent=parent)

        else:

            return super(CreateReferenceTask, cls).createEditor(name, parent=parent)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if file exists
        #
        absolutePath = os.path.normpath(os.path.expandvars(self.filePath))

        if not os.path.exists(absolutePath):

            log.warning(f'Cannot locate scene file: {self.filePath}')
            return

        # Check if namespace is valid
        #
        if stringutils.isNullOrEmpty(self.namespace):

            log.warning('Cannot create reference from null namespace!')
            return

        # Check if reference already exists
        #
        if not om.MNamespace.namespaceExists(self.namespace):

            mc.file(self.filePath, reference=True, namespace=self.namespace)

        else:

            log.warning(f'Skipping reference since "{self.namespace}" namespace already exists.')
    # endregion
