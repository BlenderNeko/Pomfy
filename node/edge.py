from __future__ import annotations
from typing import TYPE_CHECKING, List, Any, Union, Dict

from constants import ConnectionChangedType, SlotType

if TYPE_CHECKING:
    from node import Node, NodeSocket, NodeScene

from nodeGUI import GrNodeEdge


class NodeEdge:
    """Class that manages and stores data pertaining the connections between NodeSockets"""

    @property
    def outputSocket(self) -> NodeSocket:
        """Connected output socket."""
        return self._outputSocket

    @property
    def inputSocket(self) -> NodeSocket:
        """Connected input socket."""
        return self._inputSocket

    @property
    def nodeScene(self) -> NodeScene:
        """Node scene the edge lives in."""
        return self._nodeScene

    @property
    def grEdge(self) -> GrNodeEdge:
        """Qt class representing the edge."""
        return self._grEdge

    def __init__(
        self,
        nodeScene: NodeScene,
        outputSocket: NodeSocket,
        inputSocket: NodeSocket,
    ) -> None:
        self._nodeScene = nodeScene
        self.ntm = self._nodeScene.sceneCollection.ntm
        self._outputSocket: NodeSocket = outputSocket
        self._inputSocket: NodeSocket = inputSocket
        self._grEdge: GrNodeEdge = GrNodeEdge(self)
        self._nodeScene.addEdge(self)
        outputSocket.addEdge(self)
        inputSocket.addEdge(self)
        self.ntm.doStep(
            lambda: self._triggerChange(ConnectionChangedType.ADDED),
            lambda: self._triggerChange(ConnectionChangedType.REMOVED),
        )
        self.updateConnections()

    def _triggerChange(self, cct: ConnectionChangedType) -> None:
        self._outputSocket.triggerConnectionChange(self, cct)
        self._inputSocket.triggerConnectionChange(self, cct)

    def remove(self) -> None:
        """Removes edge from the node scene."""
        self.ntm.doStep(
            lambda: self._triggerChange(ConnectionChangedType.REMOVED),
            lambda: self._triggerChange(ConnectionChangedType.ADDED),
        )
        self._inputSocket.removeEdge(self)
        self._outputSocket.removeEdge(self)
        input = self.inputSocket
        output = self.outputSocket
        self.ntm.doStep(
            lambda: self._setSockets(None, None),  # type: ignore
            lambda: self._setSockets(input, output),
        )
        self.nodeScene.removeEdge(self)

    def swap(self) -> None:
        """swap input and output sockets."""
        input = self.inputSocket
        output = self.outputSocket
        pos = self.grEdge.end
        self.grEdge.end = self.grEdge.start
        self.grEdge.start = pos
        self.ntm.doStep(
            lambda: self._setSockets(output, input),
            lambda: self._setSockets(input, output),
        )

    def travelFrom(self, target: NodeSocket) -> NodeSocket:
        """Returns the NodeSocket opposite to `target` or the input socket if `target` does not exist."""
        if self.inputSocket == target:
            return self.outputSocket
        return self.inputSocket

    def _setSockets(self, input: NodeSocket, output: NodeSocket) -> None:
        self._setInput(input)
        self._setOutput(output)

    def _setInput(self, input: NodeSocket) -> None:
        self._inputSocket = input
        self.grEdge.update_color()
        if input is not None:
            self.grEdge.end = input.grNodeSocket.centerPos()

    def _setOutput(self, output: NodeSocket) -> None:
        self._outputSocket = output
        self.grEdge.update_color()
        if output is not None:
            self.grEdge.start = output.grNodeSocket.centerPos()

    def updateConnections(self) -> None:
        self.grEdge.end = self.inputSocket.grNodeSocket.centerPos()
        self.grEdge.start = self.outputSocket.grNodeSocket.centerPos()

    # TODO: type checking on loading
    def saveState(self, nodeMapping: Dict[Node, int]) -> Dict[str, Any] | None:
        state: Dict[str, Any] = {}
        if (
            self.inputSocket.nodeSlot.node not in nodeMapping
            or self.outputSocket.nodeSlot.node not in nodeMapping
        ):
            return None
        state["inputSocket"] = {
            "node": nodeMapping[self.inputSocket.nodeSlot.node],
            "slotName": self.inputSocket.nodeSlot._name,
            "slotInd": self.inputSocket.nodeSlot.ind,
        }
        state["outputSocket"] = {
            "node": nodeMapping[self.outputSocket.nodeSlot.node],
            "slotName": self.outputSocket.nodeSlot._name,
            "slotInd": self.outputSocket.nodeSlot.ind,
        }
        # state["typeName"] = self.outputSocket.socketType
        return state

    @classmethod
    def loadState(
        self, nodeScene: NodeScene, state: Dict[str, Any], nodeMapping: List[Node]
    ) -> NodeEdge | None:
        inputNode = nodeMapping[state["inputSocket"]["node"]]
        outputNode = nodeMapping[state["outputSocket"]["node"]]
        inputSocket = None
        outputSocket = None
        for slot in inputNode.inputs:
            if (
                slot.name == state["inputSocket"]["slotName"]
                and slot.ind == state["inputSocket"]["slotInd"]
            ):
                inputSocket = slot.socket
                continue
        for slot in outputNode.outputs:
            if (
                slot.name == state["outputSocket"]["slotName"]
                and slot.ind == state["outputSocket"]["slotInd"]
            ):
                outputSocket = slot.socket
                continue
        if inputSocket is not None and outputSocket is not None:
            return NodeEdge(nodeScene, outputSocket, inputSocket)
        return None
