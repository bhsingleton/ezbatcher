import os

from dcc.fbx.libs import fbxio
from dcc.perforce import cmds
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ExportAssetTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that exports animation from the scene file.
    """

    # region Dunderscores
    __slots__ = ('_manager', '_checkout')
    __title__ = 'Export Assets'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._manager = fbxio.FbxIO()
        self._checkout = kwargs.get('checkout', False)

        # Call parent method
        #
        super(ExportAssetTask, self).__init__(*args, **kwargs)

    # endregion

    # region Properties
    @property
    def manager(self):
        """
        Getter method that returns the fbx IO interface.

        :rtype: fbxio.FbxIO
        """

        return self._manager

    @property
    def checkout(self):
        """
        Getter method that returns the checkout flag.

        :rtype: bool
        """

        return self._checkout

    @checkout.setter
    def checkout(self, checkout):
        """
        Setter method that updates the checkout flag.

        :type checkout: bool
        :rtype: None
        """

        self._checkout = checkout
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Iterate through export sets
        #
        asset = self.manager.loadAsset()

        for exportSet in asset.exportSets:

            # Check if sequence should be checked out
            #
            exportPath = exportSet.exportPath()

            requiresAdding = self.checkout and not os.path.exists(exportPath)

            if self.checkout and not requiresAdding:

                cmds.edit(exportPath)

            # Export asset
            #
            exportSet.export()

            # Check if sequence should be added
            #
            if requiresAdding:

                cmds.add(exportPath)
    # endregion
