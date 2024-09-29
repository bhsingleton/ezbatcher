import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.json import jsonutils
from dcc.python import pathutils
from ezposer.libs import poseutils
from ezposer.ui import qezposer
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ExportAnimationTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that exports animation data.
    """

    # region Dunderscores
    __slots__ = ('_namespace', '_rigConfiguration', '_renameNodeMap', '_renameAttributeMap', '_normalizeCustomAttributes')
    __title__ = 'Export Animation'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(ExportAnimationTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._namespace = kwargs.get('namespace', 'X')
        self._rigConfiguration = kwargs.get('rigConfiguration', "Frame44")
        self._renameNodeMap = kwargs.get('renameNodeMap', '')
        self._renameAttributeMap = kwargs.get('renameAttributeMap', '')
        self._normalizeCustomAttributes = kwargs.get('normalizeCustomAttributes', True)
    # endregion

    # region Properties
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

    @property
    def rigConfiguration(self):
        """
        Getter method that returns the rigConfiguration.

        :rtype: str
        """

        return self._rigConfiguration

    @rigConfiguration.setter
    def rigConfiguration(self, rigConfiguration):
        """
        Getter method that returns the rigConfiguration.

        :type rigConfiguration: str
        :rtype: None
        """

        self._rigConfiguration = rigConfiguration
    
    @property
    def renameNodeMap(self):
        """
        Getter method that returns the rename node map.

        :rtype: str
        """

        return self._renameNodeMap

    @renameNodeMap.setter
    def renameNodeMap(self, renameNodeMap):
        """
        Setter method that updates the rename node map.

        :type renameNodeMap: str
        :rtype: None
        """

        self._renameNodeMap = renameNodeMap

    @property
    def renameAttributeMap(self):
        """
        Getter method that returns the rename attribute map.

        :rtype: str
        """

        return self._renameAttributeMap

    @renameAttributeMap.setter
    def renameAttributeMap(self, renameAttributeMap):
        """
        Setter method that updates the rename attribute map.

        :type renameAttributeMap: str
        :rtype: None
        """

        self._renameAttributeMap = renameAttributeMap

    @property
    def normalizeCustomAttributes(self):
        """
        Getter method that returns the normalize custom-attributes flags.

        :rtype: bool
        """

        return self._renameAttributeMap

    @normalizeCustomAttributes.setter
    def normalizeCustomAttributes(self, normalizeCustomAttributes):
        """
        Setter method that updates the normalize custom-attributes flags.

        :type normalizeCustomAttributes: bool
        :rtype: None
        """

        self._normalizeCustomAttributes = normalizeCustomAttributes
    # endregion

    # region Methods
    def loadRenameNodeMap(self):
        """
        Returns a deserialized rename node map.

        :rtype: Dict[str, str]
        """

        if pathutils.isFileLike(self.renameNodeMap):

            return jsonutils.load(self.renameNodeMap)

        else:

            return jsonutils.loads(self.renameNodeMap, default={})

    def loadRenameAttributeMap(self):
        """
        Returns a deserialized rename attribute map.

        :rtype: Dict[str, str]
        """

        if pathutils.isFileLike(self.renameAttributeMap):

            return jsonutils.load(self.renameAttributeMap)

        else:

            return jsonutils.loads(self.renameAttributeMap, default={})

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Update namespace and configuration
        #
        qezposer.QEzPoser.setCurrentConfiguration(self.rigConfiguration)
        qezposer.QEzPoser.setCurrentNamespace(self.namespace)

        # Create pose from controls
        #
        nodes = list(qezposer.QEzPoser.iterControls(visible=False))

        pose = poseutils.createPose(
            *nodes,
            name=self.taskManager.currentName,
            skipKeys=False,
            skipLayers=True
        )

        # Update pose node names
        #
        renameNodeMap = self.loadRenameNodeMap()
        renameAttributeMap = self.loadRenameAttributeMap()

        for node in pose.nodes:

            node.name = renameNodeMap.get(node.name, node.name)

            for attribute in node.attributes:

                attribute.name = renameAttributeMap(attribute.name, attribute.name)

                if attribute.isCustom and self.normalizeCustomAttributes:

                    attribute.value /= 100.0

                    for keyframe in attribute.keyframes:

                        keyframe.value /= 100.0

                else:

                    continue

        # Export pose using current scene name
        #
        filePath = os.path.join(self.taskManager.currentDirectory, f'{self.taskManager.currentName}.anim')
        poseutils.exportPose(filePath, pose)
    # endregion
