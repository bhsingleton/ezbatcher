import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils
from ezposer.libs import poseutils
from ezposer.ui import qezposer
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ImportAnimationTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that imports animation data.
    """

    # region Dunderscores
    __slots__ = ('_namespace', '_rigConfiguration')
    __title__ = 'Import Animation'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(ImportAnimationTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._namespace = kwargs.get('namespace', 'X')
        self._rigConfiguration = kwargs.get('rigConfiguration', "Rig o'tron")
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
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if file exists
        #
        filePath = os.path.join(self.taskManager.currentDirectory, f'{self.taskManager.currentName}.anim')

        if not os.path.isfile(filePath):

            log.warning(f'Cannot locate animation file: {filePath}')
            return

        # Update namespace and configuration
        #
        qezposer.QEzPoser.setCurrentConfiguration(self.rigConfiguration)
        qezposer.QEzPoser.setCurrentNamespace(self.namespace)

        # Apply animation to controls
        #
        nodes = list(qezposer.QEzPoser.iterControls(visible=False))

        pose = poseutils.importPose(filePath)
        pose.applyAnimationTo(*nodes, namespace=self.namespace)
    # endregion
