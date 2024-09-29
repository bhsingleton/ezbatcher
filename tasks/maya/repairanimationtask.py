from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils, pathutils
from dcc.json import jsonutils
from dcc.maya.libs import dagutils, plugutils, animutils
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RepairAnimationTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that repairs broken animation curves.
    """

    # region Dunderscores
    __slots__ = ('_renameNodeMap', '_renamePlugMap')
    __title__ = 'Repair Animation'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(RepairAnimationTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._renameNodeMap = kwargs.get('renameNodeMap', '')
        self._renamePlugMap = kwargs.get('renamePlugMap', '')
    # endregion

    # region Properties
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
    def renamePlugMap(self):
        """
        Getter method that returns the rename plug map.

        :rtype: str
        """

        return self._renamePlugMap

    @renamePlugMap.setter
    def renamePlugMap(self, renamePlugMap):
        """
        Setter method that updates the rename plug map.

        :type renamePlugMap: str
        :rtype: None
        """

        self._renamePlugMap = renamePlugMap
    # endregion

    # region Methods
    def loadRenameNodeMap(self):
        """
        Returns a deserialized rename node map.

        :rtype: Dict[str, str]
        """

        if pathutils.isFileLike(self.renameNodeMap):

            return jsonutils.load(self.renameNodeMap, default={})

        else:

            return jsonutils.loads(self.renameNodeMap, default={})

    def loadRenamePlugMap(self):
        """
        Returns a deserialized rename plug map.

        :rtype: Dict[str, str]
        """

        if pathutils.isFileLike(self.renamePlugMap):

            return jsonutils.load(self.renamePlugMap, default={})

        else:

            return jsonutils.loads(self.renamePlugMap, default={})

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if any reference nodes exist
        #
        referenceNodes = mc.ls(type='reference')

        if stringutils.isNullOrEmpty(referenceNodes):

            return

        # Iterate through reference nodes
        #
        renameNodeMap = self.loadRenameNodeMap()
        renamePlugMap = self.loadRenamePlugMap()

        for referenceNode in referenceNodes:

            # Check if this is a shared reference node
            #
            if referenceNode == 'sharedReferenceNode':

                continue

            # Check if reference is loaded
            #
            isLoaded = mc.referenceQuery(referenceNode, isLoaded=True)

            if not isLoaded:

                continue

            # Check if any reference edits exists
            #
            editCommands = mc.referenceQuery(referenceNode, editStrings=True, failedEdits=True)

            if stringutils.isNullOrEmpty(editCommands):

                continue

            # Check if `connectAttr` edits exist
            #
            connectAttrCommands = [editCommand for editCommand in editCommands if editCommand.startswith('connectAttr')]
            numConnectAttrCommands = len(connectAttrCommands)

            if numConnectAttrCommands == 0:

                continue

            # Iterate through edits
            #
            for connectAttrCommand in connectAttrCommands:

                # Decompose `connectAttr` arguments
                #
                log.debug(f'Inspecting edit: {connectAttrCommand}')

                args = connectAttrCommand.split(' ')
                sourcePlugPath, destinationPlugPath = args[1].replace('"', ''), args[2].replace('"', '')

                # Evaluate source node
                #
                sourceNodeName, sourcePlugName = sourcePlugPath.split('.')
                sourceNode = dagutils.getMObjectByName(sourceNodeName)

                sourceNodeExists = not sourceNode.isNull()

                if not sourceNodeExists:

                    log.warning(f'Unable to locate source node: "{sourceNodeName}"!')
                    continue

                # Evaluate source node type
                #
                isAnimCurve = animutils.isAnimCurve(sourceNode)

                if not isAnimCurve:

                    log.info(f'Skipping non-anim curve: "{sourceNodeName}"!')
                    continue

                # Check if anim-curve has been remapped
                #
                cleanDestinationPlugPath = dagutils.stripAll(destinationPlugPath)
                destinationNodeName, destinationPlugName = cleanDestinationPlugPath.split('.')

                newNodeName = renameNodeMap.get(destinationNodeName, None)
                newPlugPath = renamePlugMap.get(cleanDestinationPlugPath, None)

                sourcePlug = plugutils.findPlug(sourceNode, sourcePlugName)

                if not stringutils.isNullOrEmpty(newPlugPath):
                    
                    # Check if remapped node exists
                    #
                    newNodeName, newPlugName = newPlugPath.split('.')
                    newNode = dagutils.getMObjectByName(newNodeName)

                    newNodeExists = not newNode.isNull()

                    if not newNodeExists:

                        log.warning(f'Unable to locate node: {newNodeName}')
                        continue

                    # Reconnect anim-curve to new node
                    #
                    newPlug = plugutils.findPlug(newNode, newPlugName)
                    newPlugExists = not newPlug.isNull

                    if newPlugExists:

                        # Remove edit command
                        #
                        log.info(f'Removing reference edit: {connectAttrCommand}')
                        mc.referenceEdit(destinationPlugPath, editCommand='connectAttr', failedEdits=True, removeEdits=True)

                        # Update anim-curve connection
                        #
                        log.info(f'Connecting: {sourcePlug.info} > {newPlug.info}')

                        plugutils.connectPlugs(sourcePlug, newPlug, force=True)
                        dagutils.renameNode(sourceNode, f'{newNodeName}_{newPlugName}')

                    else:

                        log.warning(f'Unable to find plug: "{newNodeName}.{newPlugName}"!')

                elif not stringutils.isNullOrEmpty(newNodeName):

                    # Check if new node name exists
                    #
                    newNode = dagutils.getMObjectByName(newNodeName)
                    newNodeExists = not newNode.isNull()

                    if not newNodeExists:

                        log.warning(f'Unable to locate node: {newNodeName}')
                        continue

                    # Reconnect anim-curve to new node
                    #
                    newPlug = plugutils.findPlug(newNode, destinationPlugName)
                    newPlugExists = not newPlug.isNull

                    if newPlugExists:

                        # Remove edit command
                        #
                        log.info(f'Removing reference edit: {connectAttrCommand}')
                        mc.referenceEdit(destinationPlugPath, editCommand='connectAttr', failedEdits=True, removeEdits=True)

                        # Update anim-curve connection
                        #
                        log.info(f'Connecting: {sourcePlug.info} > {newPlug.info}')

                        plugutils.connectPlugs(sourcePlug, newPlug, force=True)
                        dagutils.renameNode(sourceNode, f'{newNodeName}_{destinationPlugName}')

                    else:

                        log.warning(f'Unable to find plug: "{newNodeName}.{destinationPlugName}"!')

                else:

                    log.info(f'No remaps found for anim-curve: {sourcePlugPath}')
                    continue

            # Finally, remove all `setAttr` edits
            #
            mc.referenceEdit(referenceNode, editCommand='setAttr', failedEdits=True, removeEdits=True)
    # endregion
