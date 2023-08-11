from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict

from customWidgets.QSlotContentGraphicsItem import (
    QSlotContentGraphicsItem,
)

from constants import SlotType
from style.socketStyle import SocketPainter, SocketStyles

if TYPE_CHECKING:
    from node import Node


from nodeSlots.nodeSlot import NodeSlot, registerSlot


@registerSlot
class NamedSlot(NodeSlot):
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
        return isinstance(spec, list) and len(spec) == 1 and isinstance(spec[0], str)

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

        return NamedSlot(
            node,
            name,
            ind,
            typeName,
            painter,
            slotType,
            isOptional=isOptional,
        )

    def saveState(self) -> Dict[str, Any]:
        return {"value": None}

    def loadState(self, state: Dict[str, Any]) -> None:
        pass
