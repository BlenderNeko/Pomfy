from __future__ import annotations

from typing import (
    TYPE_CHECKING,
)
from constants import SlotType
from node.socket import SocketTyping

if TYPE_CHECKING:
    from node.socket import NodeSocket, ConnectionChangedEvent
    from style.socketStyle import SocketPainter

from node import Node
from nodeSlots.slots.namedSlot import NamedSlot
from nodeSlots import NodeSlot


class ExpandableNode(Node):
    def addExpandableInput(self) -> NodeSlot:
        factory = self.nodeScene.sceneCollection.nodeFactory
        painter = factory.socketStyles.getSocketPainter("", "node", False)
        namedSlot = NamedSlot(self, "", 0, "", painter, SlotType.INPUT, False)
        namedSlot.socket.onConnectionChanged += self._expand
        return namedSlot

    def addExpandableOutput(self) -> NodeSlot:
        factory = self.nodeScene.sceneCollection.nodeFactory
        painter = factory.socketStyles.getSocketPainter("", "node", False)
        namedSlot = NamedSlot(self, "", 0, "", painter, SlotType.OUTPUT, False)
        namedSlot.socket.onConnectionChanged += self._expand
        return namedSlot

    def _expand(self, cce: ConnectionChangedEvent) -> None:
        connections = cce.socket.getConnected()
        if len(connections) < 1:
            return
        target = connections[0]
        ntm = self.nodeScene.sceneCollection.ntm
        factory = self.nodeScene.sceneCollection.nodeFactory
        painter = factory.socketStyles.getSocketPainter("", "node", False)
        slotType = cce.socket.nodeSlot.slotType
        namedSlot = NamedSlot(self, "", 0, "", painter, slotType, False)
        if slotType == SlotType.OUTPUT:
            self.removeOutputSlot(namedSlot)
        else:
            self.removeInputSlot(namedSlot)
        ntm.doStep(
            lambda: self._addNewSlot(cce.socket, target, namedSlot),
            lambda: self._removeSlot(cce.socket, namedSlot, painter),
        )

    def _addNewSlot(
        self, socket: NodeSocket, target: NodeSocket, newSlot: NodeSlot
    ) -> None:
        socket.onConnectionChanged -= self._expand
        newSlot.socket.onConnectionChanged += self._expand
        socket.nodeSlot.name = target.nodeSlot.name
        socket.socketType = target.socketType
        socket.grNodeSocket.socketPainter = target.grNodeSocket.socketPainter
        if newSlot.slotType == SlotType.OUTPUT:
            self.addOutputSlot(newSlot)
        else:
            self.addInputSlot(newSlot)

    def _removeSlot(
        self,
        socket: NodeSocket,
        newSlot: NodeSlot,
        painter: SocketPainter,
    ) -> None:
        socket.onConnectionChanged += self._expand
        newSlot.socket.onConnectionChanged -= self._expand
        socket.nodeSlot.name = ""
        socket.socketType = SocketTyping()
        socket.grNodeSocket.socketPainter = painter
        if newSlot.slotType == SlotType.OUTPUT:
            self.removeOutputSlot(newSlot)
        else:
            self.removeInputSlot(newSlot)
