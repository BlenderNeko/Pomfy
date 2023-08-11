from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict

from customWidgets.QSlotContentGraphicsItem import (
    QSlotContentGraphicsItem,
)

from style.socketStyle import SocketPainter, SocketStyles
from constants import SlotType

if TYPE_CHECKING:
    from node import Node


from nodeSlots.nodeSlot import NodeSlot, registerSlot


# @registerSlot
class BooleanSlot(NodeSlot):
    def __init__(
        self,
        node: Node,
        name: str,
        ind: int,
        typeName: str,
        socketPainter: SocketPainter,
        slotType: SlotType,
        isOptional: bool,
    ) -> None:
        super().__init__(
            node, None, name, ind, typeName, socketPainter, slotType, isOptional
        )

    def initContent(self, height: float) -> QSlotContentGraphicsItem | None:
        return None

    @classmethod
    def constructableFromSpec(self, spec: Any) -> bool:
        return (
            isinstance(spec, list)
            and len(spec) == 2
            and spec[0] == "BOOLEAN"
            and isinstance(spec[1], dict)
        )

    @classmethod
    def fromSpec(
        self,
        socketStyles: SocketStyles,
        node: Node,
        name: str,
        ind: int,
        spec: Any,
        slotType: SlotType,
        visualHint: str,
        isOptional: bool,
    ) -> NodeSlot | None:
        if not self.constructableFromSpec(spec):
            return None
        typeName = spec[0]
        painter = socketStyles.getSocketPainter(typeName, visualHint, isOptional)

        return BooleanSlot(
            node,
            name,
            ind,
            typeName,
            painter,
            slotType,
            isOptional=isOptional,
        )

    def saveState(self) -> Dict[str, Any]:
        return {"value": self.content}

    def loadState(self, state: Dict[str, Any]) -> None:
        pass
