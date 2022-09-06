from maya import cmds
from ezbatcher.libs import DCC, abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class RenameNamespaceTask(abstracttask.AbstractTask):
    """
    Overload of AbstractTask that renames a namespace from the scene file.
    """

    # region Dunderscores
    __slots__ = ()
    __dcc__ = DCC.Maya
    __title__ = 'Rename Namespace'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._search = kwargs.get('search', '')
        self._replace = kwargs.get('replace', '')

        # Call parent method
        #
        super(RenameNamespaceTask, self).__init__(*args, **kwargs)
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

        searchExists = cmds.namespace(self.search, query=True, exists=True)
        replaceExists = cmds.namespace(self.replace, query=True, exists=True)

        if searchExists and not replaceExists:

            log.info('Renaming "%s" namespace to "%s".' % (self.search, self.replace))
            cmds.namespace(rename=(self.search, self.replace))
    # endregion
