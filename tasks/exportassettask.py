from dcc.fbx.libs import fbxio
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
    __slots__ = ('_manager',)
    __title__ = 'Export Assets'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._manager = fbxio.FbxIO()

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

            exportSet.export()
    # endregion
