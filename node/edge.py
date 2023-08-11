from __future__ import annotations
from typing import TYPE_CHECKING, List, Any, Union, Dict

from constants import SlotType

if TYPE_CHECKING:
    from node import Node, NodeSocket, NodeScene

from nodeGUI import GrNodeEdge


class NodeEdge:
    """Class that manages and stores data pertaining the connections between NodeSockets"""

    @property
    def outputSocket(self) -> NodeSocket | None:
        """Connected output socket."""
        return self._outputSocket

    @property
    def inputSocket(self) -> NodeSocket | None:
        """Connected input socket."""
        return self._inputSocket

    @property
    def nonEmpty(self) -> NodeSocket | None:
        """Tries to return the first socket that is not None"""
        if self._outputSocket is not None:
            return self._outputSocket
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
        nodeScene: "NodeScene",
        outputSocket: Union["NodeSocket", None],
        inputSocket: Union["NodeSocket", None],
    ) -> None:
        self._nodeScene = nodeScene
        self.ntm = self._nodeScene.sceneCollection.ntm
        self._outputSocket = outputSocket
        self._inputSocket = inputSocket
        self._grEdge = GrNodeEdge(self)
        self._nodeScene.addEdge(self)
        if outputSocket is not None:
            outputSocket.addEdge(self)
        if inputSocket is not None:
            inputSocket.addEdge(self)

    @staticmethod
    def createPartial(scene: NodeScene, socket: NodeSocket) -> "NodeEdge":
        """Creates a partial edge in the node scene, connected only to one socket."""
        if (
            socket.nodeSlot.slotType == SlotType.OUTPUT
            or socket.nodeSlot.slotType == SlotType.BI
        ):
            return NodeEdge(scene, socket, None)
        return NodeEdge(scene, None, socket)

    def disconnect(self) -> None:
        """Disconnect edge from the connected input socket, and highlights new candidates for connection."""
        if self._inputSocket is not None:
            self._inputSocket.removeEdge(self)
            input = self.inputSocket
            self.ntm.doStep(lambda: self._setInput(None), lambda: self._setInput(input))
            assert self._outputSocket is not None
            # self.nodeScene.activateSockets(self._outputSocket, self.canConnect)

    def remove(self) -> None:
        """Removes edge from the node scene."""
        if self._inputSocket is not None:
            self._inputSocket.removeEdge(self)
        if self._outputSocket is not None:
            self._outputSocket.removeEdge(self)
        input = self.inputSocket
        output = self.outputSocket
        self.ntm.doStep(
            lambda: self._setSockets(None, None),
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

    def travelFrom(self, target: NodeSocket) -> NodeSocket | None:
        """Returns the NodeSocket opposite to `target` or the input socket if `target` does not exist."""
        if self.inputSocket == target:
            return self.outputSocket
        return self.inputSocket

    def _setSockets(self, input: NodeSocket | None, output: NodeSocket | None) -> None:
        self._setInput(input)
        self._setOutput(output)

    def _setInput(self, input: NodeSocket | None) -> None:
        self._inputSocket = input
        self.grEdge.update_color()
        if input is not None:
            self.grEdge.end = input.grNodeSocket.centerPos()

    def _setOutput(self, output: NodeSocket | None) -> None:
        self._outputSocket = output
        self.grEdge.update_color()
        if output is not None:
            self.grEdge.start = output.grNodeSocket.centerPos()

    def canConnect(self, socket: NodeSocket) -> bool:
        """Returns True if the given `socket` is compatible with the partial edge."""
        currentSocket = (
            self.inputSocket if self.inputSocket is not None else self.outputSocket
        )
        assert currentSocket is not None
        return socket.isCompatible(currentSocket)

    def connect(self, target: NodeSocket, removeOnFailure: bool = True) -> bool:
        """attempts to connects edge to `target` NodeSocket, if `removeOnFailure` is True the edge will be removed from the node scene on failure."""
        if not self.canConnect(target):
            if removeOnFailure:
                self.remove()
            return False
        if self.inputSocket is None:
            self.ntm.doStep(
                lambda: self._setInput(target), lambda: self._setInput(None)
            )
        elif self.outputSocket is None:
            self.ntm.doStep(
                lambda: self._setOutput(target), lambda: self._setOutput(None)
            )
        target.addEdge(self)

        opposite = self.travelFrom(target)
        if opposite is not None:
            opposite.finalizeConnection(self)
        return True

    def updateConnections(self) -> None:
        if self.inputSocket is not None:
            self.grEdge.end = self.inputSocket.grNodeSocket.centerPos()
        if self.outputSocket is not None:
            self.grEdge.start = self.outputSocket.grNodeSocket.centerPos()

    def saveState(self, nodeMapping: Dict[Node, int]) -> Dict[str, Any] | None:
        state: Dict[str, Any] = {}
        assert self.inputSocket is not None and self.outputSocket is not None
        if (
            self.inputSocket.nodeSlot.node not in nodeMapping
            or self.outputSocket.nodeSlot.node not in nodeMapping
        ):
            return None
        state["inputSocket"] = {
            "node": nodeMapping[self.inputSocket.nodeSlot.node],
            "slotName": self.inputSocket.nodeSlot.name,
            "slotInd": self.inputSocket.nodeSlot.ind,
        }
        state["outputSocket"] = {
            "node": nodeMapping[self.outputSocket.nodeSlot.node],
            "slotName": self.outputSocket.nodeSlot.name,
            "slotInd": self.outputSocket.nodeSlot.ind,
        }
        state["typeName"] = self.outputSocket.socketType
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
                and (
                    slot.socket.socketType == state["typeName"]
                    or slot.socket.socketType == ""
                )
            ):
                inputSocket = slot.socket
        for slot in outputNode.outputs:
            if (
                slot.name == state["outputSocket"]["slotName"]
                and slot.ind == state["outputSocket"]["slotInd"]
                and (
                    slot.socket.socketType == state["typeName"]
                    or slot.socket.socketType == ""
                )
            ):
                outputSocket = slot.socket
        if inputSocket is not None and outputSocket is not None:
            return NodeEdge(nodeScene, outputSocket, inputSocket)
        return None
