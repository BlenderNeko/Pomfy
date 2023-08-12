from __future__ import annotations
from typing import TYPE_CHECKING, Callable, List, Tuple
from nodeGUI.edge import PreviewEdge

from style.socketStyle import SocketPainter

if TYPE_CHECKING:
    from nodeSlots.nodeSlot import NodeSlot
    from node import Node

from node import NodeEdge
from constants import SlotType
from nodeGUI import GrNodeSocket
from PySide6.QtCore import QPointF


class NodeSocket:
    @property
    def nodeSlot(self) -> NodeSlot:
        return self._nodeSlot

    @property
    def socketType(self) -> str:
        return self._typeName

    @socketType.setter
    def socketType(self, value: str) -> None:
        self._typeName = value

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
        self, nodeSlot: NodeSlot, typeName: str, socketPainter: SocketPainter
    ) -> None:
        self._nodeSlot = nodeSlot
        self._typeName = typeName
        self._active = False
        self._edges: List[NodeEdge] = []
        self.ntm = self.nodeSlot.node.nodeScene.sceneCollection.ntm
        self.grNodeSocket = self.createGUI(socketPainter)

    def createGUI(self, socketPainter: SocketPainter) -> GrNodeSocket:
        return GrNodeSocket(self, socketPainter)

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
        if (
            socket.socketType != self.socketType
            and self.socketType != ""
            and socket.socketType != ""
        ):
            return False
        return True

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
