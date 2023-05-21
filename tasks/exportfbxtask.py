import os

from dcc import fnreference
from dcc.ui import qdirectoryedit
from dcc.python import stringutils
from dcc.perforce import cmds, p4utils
from dcc.fbx.libs import fbxio, fbxsequencer, fbxsequence
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

        # Declare private variables
        #
        self._fbxIO = fbxio.FbxIO().weakReference()
        self._animationOnly = kwargs.get('animationOnly', True)
        self._alternateDirectory = kwargs.get('alternateDirectory', '')
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

    def exportSets(self):
        """
        Exports all the export sets inside the current scene file.

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

    def exportReferencedAssets(self):
        """
        Tries to export any animation from referenced assets inside the current scene file.
        This is done by checking if any of the reference nodes contains any export set data.
        If no export set data is found then the referenced asset is ignored!

        :rtype: None
        """

        # Check if scene contains any references
        #
        references = list(fnreference.FnReference.iterSceneReferences())
        numReferences = len(references)

        if numReferences == 0:

            log.warning('Scene contains no referenced assets!')
            return

        # Collect references from scene
        #
        reference = fnreference.FnReference()
        reference.setQueue(references)

        while not reference.isDone():

            # Initialize sequencer
            #
            name = self.scene.currentName()
            directory = self.alternateDirectory if not stringutils.isNullOrEmpty(self.alternateDirectory) else 'Export'
            sequence = fbxsequence.FbxSequence(name=name, directory=directory, useTimeline=True)

            guid = reference.guid()
            sequencer = fbxsequencer.FbxSequencer(guid=guid, sequences=[sequence])

            if not sequencer.isValid():

                log.warning(f'Cannot locate valid asset from reference: {guid}')
                reference.next()

                continue

            # Export sequence
            #
            exportPath = sequence.export(checkout=self.checkout)

            # Go to next reference
            #
            reference.next()

    def exportSequences(self):
        """
        Exports all the sequences inside the current scene file.

        :rtype: None
        """

        # Check if file contains any sequencers
        #
        sequencers = self.fbxIO.loadSequencers()
        numSequencers = len(sequencers)

        if numSequencers == 0:

            self.exportReferencedAssets()

        # Iterate through sequencers
        #
        for sequencer in sequencers:

            # Iterate through sequences
            #
            for sequence in sequencer.sequences:

                # Check if directory has been overriden
                #
                if not stringutils.isNullOrEmpty(self.alternateDirectory):

                    sequence.directory = self.alternateDirectory

                # Export sequence
                #
                exportPath = sequence.export(checkout=self.checkout)

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
