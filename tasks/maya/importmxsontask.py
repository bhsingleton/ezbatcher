import os.path
from collections import defaultdict
from maxtomaya.mxs import mxsscene
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ImportMXSONTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that imports animation from a MXSON file.
    """

    # region Dunderscores
    __slots__ = ('_filePath', '_useCurrentFile')
    __title__ = 'Import MXSON Scene'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._filePath = kwargs.get('filePath', '')
        self._useCurrentFile = kwargs.get('useCurrentFile', False)

        # Call parent method
        #
        super(ImportMXSONTask, self).__init__(*args, **kwargs)
    # endregion

    # region Properties
    @property
    def filePath(self):
        """
        Getter method that returns the MXSON source file.

        :rtype: str
        """

        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        """
        Setter method that updates the MXSON source file.

        :type filePath: str
        :rtype: None
        """

        self._filePath = filePath

    @property
    def useCurrentFile(self):
        """
        Getter method that returns the "useCurrentFile" flag.

        :rtype: bool
        """

        return self._useCurrentFile

    @useCurrentFile.setter
    def useCurrentFile(self, useCurrentFile):
        """
        Setter method that updates the "useCurrentFile" flag.

        :type useCurrentFile: bool
        :rtype: None
        """

        self._useCurrentFile = useCurrentFile
    # endregion

    # region Methods
    def getNamespaces(self, scene):
        """
        Returns a list of namespaces from the supplied MXS scene.

        :type scene: mxsscene.MXSScene
        :rtype: Dict[str, mxswrapper.MXSWrapper]
        """

        # Iterate through layers
        #
        namespaces = defaultdict(list)

        for layer in scene.layers:

            # Inspect layer name for namespace
            #
            strings = layer.name.split(':')
            numStrings = len(strings)

            if numStrings != 2:

                continue

            # Collect nodes from layer
            #
            namespace, name = strings
            namespaces[namespace].extend(layer.nodes)

        return namespaces

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if current file should be used
        #
        scene = None

        if self.useCurrentFile:

            taskManager = kwargs.get('taskManager', None)
            scene = mxsscene.MXSScene.loadScene(taskManager.currentFile)

        elif os.path.exists(self.filePath) and self.filePath.endswith('.json'):

            scene = mxsscene.MXSScene.loadScene(self.filePath)

        else:

            log.warning('Cannot locate MXSON file: %s' % self.filePath)
            return

        # Iterate through namespaces
        #
        namespaces = self.getNamespaces(scene)

        for (namespace, nodes) in namespaces.items():

            scene.reconstructKeys(*nodes, namespace=namespace)
    # endregion
