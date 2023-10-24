import os

from fnmatch import fnmatch
from dcc.fbx.libs import fbxio
from dcc.python import stringutils
from .abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class EditExportRangesTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that edits any export-ranges from the scene file.
    """

    # region Dunderscores
    __slots__ = (
        '_fbxIO',
        '_search',
        '_replace',
        '_directory',
        '_resampleTimeRange',
        '_moveToOrigin',
        '_removeRedundancies',
        '_fileFilters',

    )
    __title__ = 'Edit FBX Export Ranges'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(EditExportRangesTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._fbxIO = fbxio.FbxIO().weakReference()
        self._search = kwargs.get('search', '')
        self._replace = kwargs.get('replace', '')
        self._directory = kwargs.get('directory', '')
        self._resampleTimeRange = kwargs.get('resampleTimeRange', False)
        self._moveToOrigin = kwargs.get('moveToOrigin', False)
        self._removeRedundancies = kwargs.get('removeRedundancies', False)
        self._fileFilters = kwargs.get('fileFilters', [])
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

    @property
    def resampleTimeRange(self):
        """
        Getter method that returns the `resampleTimeRange` flag.

        :rtype: bool
        """

        return self._resampleTimeRange

    @resampleTimeRange.setter
    def resampleTimeRange(self, resampleTimeRange):
        """
        Setter method that updates the `resampleTimeRange` flag.

        :type resampleTimeRange: bool
        :rtype: None
        """

        self._resampleTimeRange = resampleTimeRange

    @property
    def moveToOrigin(self):
        """
        Getter method that returns the `moveToOrigin` flag.

        :rtype: bool
        """

        return self._moveToOrigin

    @moveToOrigin.setter
    def moveToOrigin(self, moveToOrigin):
        """
        Setter method that updates the `moveToOrigin` flag.

        :type moveToOrigin: bool
        :rtype: None
        """

        self._moveToOrigin = moveToOrigin

    @property
    def removeRedundancies(self):
        """
        Getter method that returns the `removeRedundancies` flag.

        :rtype: bool
        """

        return self._removeRedundancies

    @removeRedundancies.setter
    def removeRedundancies(self, removeRedundancies):
        """
        Setter method that updates the `removeRedundancies` flag.

        :type removeRedundancies: bool
        :rtype: None
        """

        self._removeRedundancies = removeRedundancies

    @property
    def fileFilters(self):
        """
        Getter method that returns the file filters.

        :rtype: List[str]
        """

        return self._fileFilters

    @fileFilters.setter
    def fileFilters(self, fileFilters):
        """
        Setter method that updates the file filter.

        :type fileFilters: List[str]
        :rtype: None
        """

        self._fileFilters.clear()
        self._fileFilters.extend(fileFilters)
    # endregion

    # region Methods
    def filterAccepts(self, sequencer):
        """
        Evaluates if the supplied sequencer is accepted.

        :type sequencer: dcc.fbx.libs.fbxsequencer.FbxSequencer
        :rtype: bool
        """

        # Check if sequencer is valid
        #
        isValid = sequencer.isValid()

        if not isValid:

            return False

        # Check if there are any filters
        #
        numFilters = len(self.fileFilters)

        if numFilters > 0:

            filePath = sequencer.reference.filePath()
            filename = os.path.basename(filePath)

            return any([fnmatch(filename, pattern) for pattern in self.fileFilters])

        else:

            return True

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Check for redundant sequencers
        #
        sequencers = self.fbxIO.loadSequencers()
        numSequencers = len(sequencers)

        if self.removeRedundancies and numSequencers == 1:

            sequencer = sequencers[0]
            numSequences = len(sequencer.exportRanges)

            if not (numSequences >= 2):

                sequencers.clear()

        # Iterate through sequencers
        #
        for sequencer in sequencers:

            # Check if sequencer is accepted
            #
            isAccepted = self.filterAccepts(sequencer)

            if not isAccepted:

                continue

            # Iterate through sequences
            #
            for sequence in sequencer.exportRanges:

                # Check if name requires changing
                #
                if not stringutils.isNullOrEmpty(self.search):

                    sequence.name = sequence.name.replace(self.search, self.replace)

                # Check if directory requires changing
                #
                if not stringutils.isNullOrEmpty(self.directory):

                    sequence.directory = self.directory

                # Check if time-range requires resampling
                #
                if self.resampleTimeRange:

                    sequence.startTime = self.scene.getStartTime()
                    sequence.endTime = self.scene.getEndTime()

                # Check if move-to-origin should be enabled
                #
                if self.moveToOrigin:

                    sequence.moveToOrigin = True

        # Commit changes to sequencers
        #
        self.fbxIO.saveSequencers(sequencers)
    # endregion
