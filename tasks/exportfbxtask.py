import os

from dcc.ui import qdirectoryedit
from dcc.fbx.libs import fbxio
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ExportFbxTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that exports animation from the scene file.
    """

    # region Dunderscores
    __slots__ = (
        '_fbxIO',
        '_animationOnly',
        '_alternateDirectory',
        '_checkout'
    )

    __title__ = 'Export Fbx'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(ExportFbxTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._fbxIO = fbxio.FbxIO().weakReference()
        self._animationOnly = kwargs.get('animationOnly', True)
        self._alternateDirectory = kwargs.get('alternateDirectory', '')
        self._checkout = kwargs.get('checkout', False)
    # endregion

    # region Properties
    @property
    def fbxIO(self):
        """
        Getter method that returns the fbx IO interface.

        :rtype: fbxio.FbxIO
        """

        return self._fbxIO()

    @property
    def animationOnly(self):
        """
        Getter method that returns the "animationOnly" flag.

        :rtype: bool
        """

        return self._animationOnly

    @animationOnly.setter
    def animationOnly(self, animationOnly):
        """
        Setter method that updates the "animationOnly" flag.

        :type animationOnly: bool
        :rtype: None
        """

        self._animationOnly = animationOnly

    @property
    def alternateDirectory(self):
        """
        Getter method that returns the export directory override.

        :rtype: str
        """

        return self._alternateDirectory

    @alternateDirectory.setter
    def alternateDirectory(self, alternateDirectory):
        """
        Setter method that updates the export directory override.

        :type alternateDirectory: str
        :rtype: None
        """

        self._alternateDirectory = os.path.normpath(alternateDirectory)

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

        self._checkout = checkout
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

        if name == 'alternateDirectory':

            return qdirectoryedit.QDirectoryEdit(parent=parent)

        else:

            return super(ExportFbxTask, cls).createEditor(name, parent=parent)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        directory = kwargs.get('directory', '')
        checkout = kwargs.get('checkout', False)

        if self.animationOnly:

            self.fbxIO.exportSequencers(directory=directory, checkout=checkout)

        else:

            self.fbxIO.exportAsset(checkout=checkout)
    # endregion
