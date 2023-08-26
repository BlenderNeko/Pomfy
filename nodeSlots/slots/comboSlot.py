from __future__ import annotations
from typing import TYPE_CHECKING, List, Any, Dict
from customWidgets.QComboSpinner import QComboSpinner
from customWidgets.QSlotContentGraphicsItem import (
    QSlotContentGraphicsItem,
)

from PySide6.QtGui import QUndoCommand

from style.socketStyle import SocketPainter, SocketStyles
from constants import SlotType

if TYPE_CHECKING:
    from node import Node

from nodeSlots.nodeSlot import NodeSlot, registerSlot


@registerSlot
class ComboSlot(NodeSlot):
    def __init__(
        self,
        node: Node,
        name: str,
        ind: int,
        items: List[str],
        socketPainter: SocketPainter,
        slotType: SlotType,
        isOptional: bool = False,
    ):
        self.items = items
        self.name = name
        self.default = items[0] if len(items) > 0 else ""
        super().__init__(
            node, self.default, name, ind, "COMBO", socketPainter, slotType, isOptional
        )

    def initContent(self, height: float) -> QSlotContentGraphicsItem | None:
        self.grItem = QComboSpinner(
            self.name, 100, height, self._value_changed, self.items, self.default
        )
        return self.grItem

    def _value_changed(self, command: QUndoCommand) -> None:
        self.node.nodeScene.sceneCollection.undoStack.push(command)
        self.content = self.grItem.value

    @classmethod
    def constructableFromSpec(self, spec: Any) -> bool:
        return (
            isinstance(spec, list)
            and isinstance(spec[0], list)
            and (len(spec) == 1 or isinstance(spec[1], dict))
        )

    @classmethod
    def socketTypeFromSpec(cls, spec: Any) -> str | None:
        if cls.constructableFromSpec(spec):
            return "COMBO"
        return None

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
        items = spec[0]
        painter = socketStyles.getSocketPainter("COMBO", visualHint, isOptional)
        return ComboSlot(node, name, ind, items, painter, slotType, isOptional)

    def saveState(self) -> Dict[str, Any]:
        ind = self.items.index(self.content)
        return {"value": (ind, self.content)}

    def loadState(self, state: Dict[str, Any]) -> None:
        if "value" in state:
            ind: int
            text: str
            ind, text = state["value"]
            if text in self.items:
                self.grItem.value = text
            elif ind < len(self.items):
                self.grItem.value = self.items[ind]
