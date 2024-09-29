from maya.api import OpenMaya as om, OpenMayaAnim as oma
from dcc.maya.libs import plugutils, animutils
from ..abstract import abstracttask

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class EditAnimationTask(abstracttask.AbstractTask):
    """
    Overload of `AbstractTask` that edits animation keys.
    """

    # region Dunderscores
    __slots__ = ('_namespace', '_invertPlugs', '_normalizePlugs')
    __title__ = 'Edit Animation'

    def __init__(self, *args, **kwargs):
        """
        Private method called after a new instance is created.

        :rtype: None
        """

        # Call parent method
        #
        super(EditAnimationTask, self).__init__(*args, **kwargs)

        # Declare private variables
        #
        self._namespace = kwargs.get('namespace', 'X')
        self._invertPlugs = kwargs.get('invertPlugs', [])
        self._normalizePlugs = kwargs.get('normalizePlugs', [])
    # endregion

    # region Properties
    @property
    def namespace(self):
        """
        Getter method that returns the target namespace.

        :rtype: str
        """

        return self._namespace

    @namespace.setter
    def namespace(self, namespace):
        """
        Setter method that updates the target namespace.

        :type namespace: str
        :rtype: None
        """

        self._namespace = namespace

    @property
    def invertPlugs(self):
        """
        Getter method that returns the plugs to invert.

        :rtype: List[str]
        """

        return self._invertPlugs

    @invertPlugs.setter
    def invertPlugs(self, invertPlugs):
        """
        Setter method that updates the plugs to invert.

        :type invertPlugs: List[str]
        :rtype: None
        """

        self._invertPlugs.clear()
        self._invertPlugs.extend(invertPlugs)

    @property
    def normalizePlugs(self):
        """
        Getter method that returns the plugs to normalize.

        :rtype: List[str]
        """

        return self._normalizePlugs

    @normalizePlugs.setter
    def normalizePlugs(self, normalizePlugs):
        """
        Setter method that updates the plugs to normalize.

        :type normalizePlugs: List[str]
        :rtype: None
        """

        self._normalizePlugs.clear()
        self._normalizePlugs.extend(normalizePlugs)
    # endregion

    # region Methods
    def iterPlugFromNames(self, *plugNames):
        """
        Returns a generator that yields plugs from the supplied names.

        :type plugNames: Union[str, List[str]]
        :rtype: Iterator[om.MPlug]
        """

        selectionList = om.MSelectionList()

        for plugName in plugNames:

            fullPlugName = f'{self.namespace}:{plugName}'

            try:

                selectionList.add(fullPlugName)
                plug = selectionList.getPlug(0)

                yield plug

            except RuntimeError as exception:

                log.warning(f'Unable to locate plug: {fullPlugName}')

            finally:

                selectionList.clear()

    def inverseKeyframes(self, plug):
        """
        Inverses the anim-curve values on the supplied plug.

        :type plug: om.MPlug
        :rtype: None
        """

        # Check if plug is animated
        #
        if not plugutils.isAnimated(plug):
            
            return

        # Inverse anim-curve values
        #
        animCurve = animutils.findAnimCurve(plug, create=False)
        fnAnimCurve = oma.MFnAnimCurve(animCurve)

        numKeys = fnAnimCurve.numKeys

        for i in range(numKeys):

            # Unlock tangents
            #
            tangentsLocked = fnAnimCurve.tangentsLocked(i)

            fnAnimCurve.setWeightsLocked(i, False)
            fnAnimCurve.setTangentsLocked(i, False)

            # Check if in-tangent requires editing
            #
            inTangentType = fnAnimCurve.inTangentType(i)

            if inTangentType in (oma.MFnAnimCurve.kTangentAutoCustom, oma.MFnAnimCurve.kTangentFixed):

                inTangentX, inTangentY = fnAnimCurve.getTangentXY(i, True)
                fnAnimCurve.setTangent(i, inTangentX, -inTangentY, True, convertUnits=False)

            # Inverse value
            #
            value = fnAnimCurve.value(i) * -1.0
            fnAnimCurve.setValue(i, value)

            # Check if out-tangent requires editing
            #
            outTangentType = fnAnimCurve.outTangentType(i)

            if outTangentType in (oma.MFnAnimCurve.kTangentAutoCustom, oma.MFnAnimCurve.kTangentFixed):

                outTangentX, outTangentY = fnAnimCurve.getTangentXY(i, False)
                fnAnimCurve.setTangent(i, outTangentX, -outTangentY, False, convertUnits=False)

            # Re-lock tangents
            #
            fnAnimCurve.setTangentsLocked(i, tangentsLocked)

    def normalizeKeyframes(self, plug):
        """
        Normalizes the anim-curve values on the supplied plug.

        :type plug: om.MPlug
        :rtype: None
        """

        # Check if plug is animated
        #
        if not plugutils.isAnimated(plug):

            return

        # Inverse anim-curve values
        #
        animCurve = animutils.findAnimCurve(plug, create=False)
        fnAnimCurve = oma.MFnAnimCurve(animCurve)

        numKeys = fnAnimCurve.numKeys

        for i in range(numKeys):

            value = fnAnimCurve.value(i) / 100.0
            fnAnimCurve.setValue(i, value)

    def doIt(self, *args, **kwargs):
        """
        Executes this task.

        :rtype: None
        """

        # Iterate through plugs that require inverting
        #
        for plug in self.iterPlugFromNames(*self.invertPlugs):

            self.inverseKeyframes(plug)

        # Iterate through plugs that require normalizing
        #
        for plug in self.iterPlugFromNames(*self.normalizePlugs):

            self.normalizeKeyframes(plug)
    # endregion
