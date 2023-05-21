import os

from dcc.fbx.libs import fbxio
from dcc.python import stringutils
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class EditSequencesTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that edits any sequences from the scene file.
    """

    # region Dunderscores
    __slots__ = ('_fbxIO', '_search', '_replace', '_directory')
    __title__ = 'Edit FBX Sequences'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Declare private variables
        #
        self._fbxIO = fbxio.FbxIO().weakReference()
        self._search = kwargs.get('search', '')
        self._replace = kwargs.get('replace', '')
        self._directory = kwargs.get('directory', '')

        # Call parent method
        #
        super(EditSequencesTask, self).__init__(*args, **kwargs)
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
    def search(self):
        """
        Getter method that returns the search string for name changes.

        :rtype: str
        """

        return self._search

    @search.setter
    def search(self, search):
        """
        Setter method that updates the search string for name changes.

        :type search: str
        :rtype: None
        """

        self._search = search

    @property
    def replace(self):
        """
        Getter method that returns the replace string for name changes.

        :rtype: str
        """

        return self._replace

    @replace.setter
    def replace(self, replace):
        """
        Setter method that updates the replace string for name changes.

        :type replace: str
        :rtype: None
        """

        self._replace = replace

    @property
    def directory(self):
        """
        Getter method that returns the replacement directory path.

        :rtype: str
        """

        return self._directory

    @directory.setter
    def directory(self, directory):
        """
        Setter method that updates the replacement directory path.

        :type directory: str
        :rtype: None
        """

        self._directory = os.path.normpath(directory)
    # endregion

    # region Methods
    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Iterate through sequencers
        #
        sequencers = self.fbxIO.loadSequencers()

        for sequencer in sequencers:

            # Iterate through sequences
            #
            for sequence in sequencer.sequences:

                # Check if name requires changing
                #
                if not stringutils.isNullOrEmpty(self.search):

                    sequence.name = sequence.name.replace(self.search, self.replace)

                # Check if directory requires changing
                #
                if not stringutils.isNullOrEmpty(self.directory):

                    sequence.directory = self.directory

        # Commit changes to sequencers
        #
        self.fbxIO.saveSequencers(sequencers)
    # endregion
