from __future__ import annotations
from typing import TYPE_CHECKING, Callable, List, Tuple
from nodeGUI.edge import PreviewEdge

from style.socketStyle import SocketPainter

if TYPE_CHECKING:
    from nodeSlots.nodeSlot import NodeSlot
    from node import Node

from node import NodeEdge
from constants import ConnectionChangedType, SlotType
from nodeGUI import GrNodeSocket
from PySide6.QtCore import QPointF
from events import Event
from enum import Enum

class SocketTyping:
    def __init__(self, *types:str) -> None:
        self.types = types
    
    def checkCompat(self, outputTarget:'SocketTyping') -> bool:
        '''check if target sockettyping is compatible'''
        if len(self.types) == 0:
            return True
        for t in outputTarget.types:
            if t not in self.types:
                return False
        return True
    
    def checkEqual(self, socketTyping: 'SocketTyping') -> bool:
        return set(self.types) == set(socketTyping.types)
    
    #TODO: better printing
    def toString(self) -> str:
        return "\n".join(self.types[:5])
    


class ConnectionChangedEvent:
    def __init__(
        self,
        socket: "NodeSocket",
        edge: NodeEdge | None,
        changedType: ConnectionChangedType,
    ) -> None:
        self.socket = socket
        self.edge = edge
        self.changedType = changedType


class NodeSocket:
    @property
    def nodeSlot(self) -> NodeSlot:
        return self._nodeSlot

    @property
    def socketType(self) -> SocketTyping:
        return self._socketType

    @socketType.setter
    def socketType(self, value: SocketTyping) -> None:
        self._socketType = value

    @property
    def active(self) -> bool:
        return self._active

    @property
    def scenePosition(self) -> QPointF:
        return self.grNodeSocket.centerPos()

    @property
    def edges(self) -> List[NodeEdge]:
        return self._edges

    def __init__(
        self, nodeSlot: NodeSlot, socketType: SocketTyping, socketPainter: SocketPainter
    ) -> None:
        self._nodeSlot = nodeSlot
        self._socketType = socketType
        self._active = False
        self._edges: List[NodeEdge] = []
        self.ntm = self.nodeSlot.node.nodeScene.sceneCollection.ntm
        self.grNodeSocket: GrNodeSocket = self.createGUI(socketPainter)
        self.onConnectionChanged: Event[
            Callable[[ConnectionChangedEvent], None]
        ] = Event()

    def createGUI(self, socketPainter: SocketPainter) -> GrNodeSocket:
        return GrNodeSocket(self, socketPainter)

    def triggerConnectionChange(
        self, edge: NodeEdge | None, cType: ConnectionChangedType
    ) -> None:
        self.onConnectionChanged(ConnectionChangedEvent(self, edge, cType))

    def getConnected(self) -> List[NodeSocket]:
        sockets: List[NodeSocket] = []
        for edge in self.edges:
            socket = edge.travelFrom(self)
            sockets.extend(socket.resolveConnected(self.nodeSlot.slotType))
        return sockets

    def resolveConnected(self, origin: SlotType) -> List[NodeSocket]:
        return [self]

    def getConnectedForDeactivation(self) -> List[Node]:
        nodes = []
        for e in self._edges:
            if self.nodeSlot.slotType == SlotType.INPUT:
                nodes.append(e.outputSocket.nodeSlot.node)
            elif self.nodeSlot.slotType == SlotType.OUTPUT:
                nodes.append(e.inputSocket.nodeSlot.node)
        return nodes

    def activateSocket(self, check: Callable[["NodeSocket"], bool]) -> None:
        if check(self):
            self._active = True

    def deactivateSocket(self) -> None:
        self._active = False

    def getEdge(self) -> Tuple[PreviewEdge, NodeEdge | None]:
        if self._nodeSlot.slotType == SlotType.OUTPUT or len(self._edges) == 0:
            previewEdge = PreviewEdge(self.grNodeSocket)
            return (previewEdge, None)
        else:
            previewEdge = PreviewEdge(self._edges[0].outputSocket.grNodeSocket)
            return (previewEdge, self._edges[0])

    def isCompatible(self, socket: "NodeSocket") -> bool:
        if (
            self.nodeSlot.slotType == socket.nodeSlot.slotType
            and self.nodeSlot.slotType != SlotType.BI
            and socket.nodeSlot.slotType != SlotType.BI
        ):
            return False
        if self.nodeSlot.node == socket.nodeSlot.node:
            return False
        outputTarget = self if self.nodeSlot.isOutput else socket
        inputTarget = self if self != outputTarget else socket
        return inputTarget.socketType.checkCompat(outputTarget.socketType)

    def addEdge(self, edge: NodeEdge) -> None:
        # can only have a single edge connected to an input slot
        if self.nodeSlot.slotType == SlotType.INPUT and len(self._edges) > 0:
            self._edges[0].remove()
        # can not have duplicate edges
        elif self.nodeSlot.slotType == SlotType.OUTPUT:
            for e in self._edges:
                if e.inputSocket == edge.inputSocket:
                    e.remove()
                    break
        self.ntm.doStep(
            lambda: self._edges.append(edge),
            lambda: None if self._edges.pop() else None,
        )
        # hide content if input connection
        if self.nodeSlot.slotType == SlotType.INPUT:
            showContent = self.nodeSlot.grNodeSlot.showContent
            self.ntm.doStep(
                lambda: self.nodeSlot.grNodeSlot.setShowContent(False),
                lambda: self.nodeSlot.grNodeSlot.setShowContent(showContent),
            )

    def removeEdge(self, edge: NodeEdge) -> None:
        ind = self._edges.index(edge)
        self.ntm.doStep(
            lambda: self._edges.remove(edge), lambda: self._edges.insert(ind, edge)
        )
        if self.nodeSlot.slotType == SlotType.INPUT:
            showContent = self.nodeSlot.grNodeSlot.showContent
            self.ntm.doStep(
                lambda: self.nodeSlot.grNodeSlot.setShowContent(True),
                lambda: self.nodeSlot.grNodeSlot.setShowContent(showContent),
            )

    def remove(self) -> None:
        edges = self._edges.copy()
        for e in edges:
            e.remove()

    def updateEdges(self) -> None:
        if self.nodeSlot.slotType == SlotType.OUTPUT:
            for edge in self._edges:
                edge.grEdge.start = self.grNodeSocket.centerPos()
        if self.nodeSlot.slotType == SlotType.INPUT:
            for edge in self._edges:
                edge.grEdge.end = self.grNodeSocket.centerPos()
