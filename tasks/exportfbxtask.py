import os

from dcc.fbx.libs import fbxio
from dcc.perforce import cmds
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ExportFbxTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that exports animation from the scene file.
    """

    # region Dunderscores
    __slots__ = ('_fbxIO', '_animationOnly', '_checkout')
    __title__ = 'Export Fbx'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._fbxIO = fbxio.FbxIO().weakReference()
        self._animationOnly = kwargs.get('animationOnly', True)
        self._checkout = kwargs.get('checkout', False)

        # Call parent method
        #
        super(ExportFbxTask, self).__init__(*args, **kwargs)
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

    def exportSets(self):
        """
        Executes all the export sets inside the current scene file.

        :rtype: None
        """

        # Iterate through export sets
        #
        asset = self.fbxIO.loadAsset()

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

    def exportSequences(self):
        """
        Executes all the sequences inside the current scene file.

        :rtype: None
        """

        # Iterate through sequencers
        #
        sequencers = self.fbxIO.loadSequencers()

        for sequencer in sequencers:

            # Iterate through sequences
            #
            for sequence in sequencer.sequences:

                # Check if sequence should be checked out
                #
                exportPath = sequence.exportPath()
                requiresAdding = self.checkout and not os.path.exists(exportPath)

                if self.checkout and not requiresAdding:

                    cmds.edit(exportPath)

                # Export sequence
                #
                sequence.export()

                # Check if sequence should be added
                #
                if requiresAdding:

                    cmds.add(exportPath)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        if self.animationOnly:

            self.exportSequences()

        else:

            self.exportSets()
    # endregion
