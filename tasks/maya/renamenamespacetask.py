from maya import cmds as mc
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RenameNamespaceTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that renames a namespace from the scene file.
    """

    # region Dunderscores
    __slots__ = ('_search', '_replace')
    __title__ = 'Rename Namespace'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(RenameNamespaceTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._search = kwargs.get('search', '')
        self._replace = kwargs.get('replace', '')
    # endregion

    # region Properties
    @property
    def search(self):
        """
        Getter method that returns the search string.

        :rtype: str
        """

        return self._search

    @search.setter
    def search(self, search):
        """
        Setter method that updates the search string.

        :type search: str
        :rtype: None
        """

        self._search = search

    @property
    def replace(self):
        """
        Getter method that returns the replacement string.

        :rtype: str
        """

        return self._replace

    @replace.setter
    def replace(self, replace):
        """
        Setter method that updates the replacement string.

        :type replace: str
        :rtype: None
        """

        self._replace = replace

    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check if namespace exists
        #
        searchExists = mc.namespace(exists=self.search)

        if not searchExists:

            log.warning(f'Cannot locate namespace: {self.search}')
            return

        # Check for name collision
        #
        replaceExists = mc.namespace(exists=self.replace)

        if replaceExists:

            log.warning(f'Namespace already exists: {self.replace}')
            return

        # Update namespace and associated reference
        #
        log.info(f'Renaming namespace: "{self.search}" > "{self.replace}"')
        mc.namespace(rename=(self.search, self.replace))

        oldName = f'{self.search}RN'
        newName = f'{self.replace}RN'

        if mc.objExists(oldName):

            mc.lockNode(oldName, lock=False)
            mc.rename(oldName, newName)
            mc.lockNode(newName, lock=True)
    # endregion
