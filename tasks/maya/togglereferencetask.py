import os

from maya import cmds as mc
from maya.api import OpenMaya as om
from dcc.python import stringutils
from dcc.ui import qfileedit
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class ToggleReferenceTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that toggles a scene reference's load state.
    """

    # region Dunderscores
    __slots__ = ('_name', '_load', '_unload')
    __title__ = 'Toggle Reference'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(ToggleReferenceTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._name = kwargs.get('name', '')
        self._load = kwargs.get('load', False)
        self._unload = kwargs.get('unload', False)
    # endregion

    # region Properties
    @property
    def name(self):
        """
        Getter method that returns the target reference node.

        :rtype: str
        """

        return self._name

    @name.setter
    def name(self, name):
        """
        Setter method that updates the target reference node.

        :type filePath: str
        :rtype: None
        """

        self._name = name

    @property
    def load(self):
        """
        Getter method that returns the load flag.

        :rtype: bool
        """

        return self._load

    @load.setter
    def load(self, load):
        """
        Setter method that updates the load flag.

        :type load: bool
        :rtype: None
        """

        self._load = load

    @property
    def unload(self):
        """
        Getter method that returns the unload flag.

        :rtype: bool
        """

        return self._unload

    @unload.setter
    def unload(self, unload):
        """
        Setter method that updates the unload flag.

        :type unload: bool
        :rtype: None
        """

        self._unload = unload
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if reference node exists
        #
        if not mc.objExists(self.name):

            log.warning(f'Cannot locate "{self.name}" reference node!')
            return

        # Evaluate requested load state
        #
        filePath = mc.referenceQuery(self.name, filename=True)

        if self.load:

            mc.file(filePath, loadReference=self.name)

        if self.unload:

            mc.file(filePath, unloadReference=self.name)
    # endregion
