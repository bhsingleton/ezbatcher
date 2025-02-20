import os

from mpy import mpyscene
from ezposer.libs import poseutils
from dcc.ui import qfileedit, qdirectoryedit
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class TransferAnimationTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that transfers animation into a new scene file.
    """

    # region Dunderscores
    __slots__ = (
        '_sourceNamespace',
        '_controllerPattern',
        '_targetNamespace',
        '_targetRig',
        '_targetDirectory'
    )
    __title__ = 'Transfer Animation'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(TransferAnimationTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._sourceNamespace = kwargs.get('sourceNamespace', 'X')
        self._controllerPattern = kwargs.get('controllerPattern', '*_CTRL')
        self._targetNamespace = kwargs.get('targetNamespace', 'X')
        self._targetRig = kwargs.get('targetRig', '')
        self._targetDirectory = kwargs.get('targetDirectory', '')
    # endregion

    # region Properties
    @property
    def sourceNamespace(self):
        """
        Getter method that returns the source namespace.

        :rtype: str
        """

        return self._sourceNamespace

    @sourceNamespace.setter
    def sourceNamespace(self, sourceNamespace):
        """
        Setter method that updates the source namespace.

        :type sourceNamespace: str
        :rtype: None
        """

        self._sourceNamespace = sourceNamespace

    @property
    def controllerPattern(self):
        """
        Getter method that returns the controller pattern.

        :rtype: str
        """

        return self._controllerPattern

    @controllerPattern.setter
    def controllerPattern(self, controllerPattern):
        """
        Setter method that updates the controller pattern.

        :type controllerPattern: str
        :rtype: None
        """

        self._controllerPattern = controllerPattern

    @property
    def targetNamespace(self):
        """
        Getter method that returns the target namespace.

        :rtype: str
        """

        return self._targetNamespace

    @targetNamespace.setter
    def targetNamespace(self, targetNamespace):
        """
        Setter method that updates the target namespace.

        :type targetNamespace: str
        :rtype: None
        """

        self._targetNamespace = targetNamespace

    @property
    def targetRig(self):
        """
        Getter method that returns the target rig.

        :rtype: str
        """

        return self._targetRig

    @targetRig.setter
    def targetRig(self, targetRig):
        """
        Setter method that updates the target rig.

        :type targetRig: str
        :rtype: None
        """

        self._targetRig = targetRig

    @property
    def targetDirectory(self):
        """
        Getter method that returns the target directory.

        :rtype: str
        """

        return self._targetDirectory

    @targetDirectory.setter
    def targetDirectory(self, targetDirectory):
        """
        Setter method that updates the target directory.

        :type targetDirectory: str
        :rtype: None
        """

        self._targetDirectory = targetDirectory
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

        if name == 'targetRig':

            return qfileedit.QFileEdit(filter='Maya Files (*.mb *.ma)', parent=parent)

        elif name == 'targetDirectory':

            return qdirectoryedit.QDirectoryEdit(parent=parent)

        else:

            return super(TransferAnimationTask, cls).createEditor(name, parent=parent)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Save animation from controls
        #
        scene = mpyscene.MPyScene()
        sourcePattern = f'{self.sourceNamespace}:{self.controllerPattern}'
        controls = list(scene.iterNodesByPattern(sourcePattern, apiType=om.MFn.kTransform))

        pose = poseutils.createPose(*controls, skipKeys=False)

        # Copy sequencer data
        #
        fbxSequencers = scene.properties.get('fbxSequencers', '')

        sourceReference = scene.getNodeByName(f'{self.sourceNamespace}RN')
        sourceUUID = sourceReference.uuid(asString=True)

        # Create reference and apply animation to rig
        #
        scene.new()
        targetReference = scene.createReference(self.targetRig, namespace=self.targetNamespace)

        targetPattern = f'{self.targetNamespace}:{self.controllerPattern}'
        controls = list(scene.iterNodesByPattern(targetPattern, apiType=om.MFn.kTransform))

        pose.applyAnimationTo(*controls)

        # Remap the reference UUID associated with the sequencer data
        #
        targetUUID = targetReference.uuid(asString=True)
        fbxSequencers.replace(sourceUUID, targetUUID)

        scene.properties['fbxSequencers'] = fbxSequencers

        # Save scene to target directory
        #
        savePath = os.path.join(self.targetDirectory, self.taskManager.currentFilename)
        self.scene.saveAs(savePath)
    # endregion
