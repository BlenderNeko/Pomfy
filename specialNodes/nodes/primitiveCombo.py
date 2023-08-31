from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Generic,
    cast,
    Callable,
    List,
    Generator,
    Tuple,
)
from constants import SlotType, ConnectionChangedType
from customWidgets.QNumSpinner import QNumSpinner
from node.socket import SocketTyping

if TYPE_CHECKING:
    from node.factory import ComfyFactory
    from node.socket import NodeSocket
    from node.socket import ConnectionChangedEvent

from node import Node, NodeScene
from nodeSlots.slots.comboSlot import ComboSLotTyping, ComboSlot
from nodeSlots import NodeSlot
from specialNodes.customNode import CustomNode, registerCustomNode
from decimal import Decimal


@registerCustomNode
class ComboPrimitive(Node, CustomNode):
    @classmethod
    def getClassName(cls) -> str:
        return "ComboPrimitive"

    @classmethod
    def getDisplayName(cls) -> str:
        return "Combo"

    @classmethod
    def getCategory(cls) -> str | None:
        return "Input"

    @classmethod
    def createNode(cls, factory: ComfyFactory, nodeDef: Any) -> Node:
        assert factory.activeScene is not None
        node = cls(
            factory.activeScene,
            cls.getClassName(),
            description="Combo primitive",
            title="Combo",
        )
        painter = factory.socketStyles.getSocketPainter("COMBO", "node", False)
        comboSlot: ComboSlot = ComboSlot(node, "value", 0, [], painter, SlotType.OUTPUT)
        comboSlot.socket.onConnectionChanged += node.onConnectionChanged

        return node

    def changeItems(self, comboSocket: NodeSocket, items: List[str]) -> None:
        cast(ComboSLotTyping, comboSocket.socketType).updateItems(items)
        cast(ComboSlot, comboSocket.nodeSlot).updateItems(items)

    def onConnectionChanged(self, cce: ConnectionChangedEvent) -> None:
        if (
            cce.changedType == ConnectionChangedType.ADDED
            and len(cce.socket.getConnected()) == 1
            and cce.edge is not None
        ):
            newItems = cast(
                ComboSLotTyping,
                cce.socket.getConnected()[0].socketType,
            ).comboItems
            self.changeItems(cce.socket, newItems)
        if (
            cce.changedType == ConnectionChangedType.REMOVED
            and len(cce.socket.getConnected()) == 1
        ):
            self.changeItems(cce.socket, [])

    @classmethod
    def searchableOutputs(cls) -> List[Tuple[str, SocketTyping]]:
        return [("value", ComboSLotTyping([]))]
