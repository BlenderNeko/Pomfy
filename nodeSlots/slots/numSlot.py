from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, TypedDict, Dict, cast, TypeVar, Generic

from decimal import Decimal

from customWidgets.QComboSpinner import QComboSpinner
from customWidgets.QNumSpinner import QNumSpinner
from customWidgets.QSlotContentGraphicsItem import (
    QSlotContentGraphicsItem,
)

from PySide6.QtGui import QUndoCommand

from style.socketStyle import SocketPainter, SocketStyles
from constants import SlotType

if TYPE_CHECKING:
    from node import Node

from nodeSlots.nodeSlot import NodeSlot, registerSlot

T = TypeVar("T", Decimal, int)


class NumSlot(NodeSlot, Generic[T]):
    def __init__(
        self,
        node: Node,
        default: T,
        name: str,
        ind: int,
        typeName: str,
        socketPainter: SocketPainter,
        slotType: SlotType,
        min: T | None = None,
        max: T | None = None,
        step: T | None = None,
        valid: T | None = None,
        validOffset: T | None = None,
        isOptional: bool = False,
    ) -> None:
        self.default: T = default
        self.min: T | None = min
        self.max: T | None = max
        self.step: T | None = step
        self.valid: T | None = valid
        self.validOffset: T | None = validOffset
        super().__init__(
            node, default, name, ind, typeName, socketPainter, slotType, isOptional
        )

    def initContent(self, height: float) -> QSlotContentGraphicsItem | None:
        self.grItem: QNumSpinner[T] = QNumSpinner[T](
            self.name,
            100,
            height,
            self._value_changed,
            self.default,
            self.min,
            self.max,
            self.step,
            self.valid,
            self.validOffset,
        )

        return self.grItem

    def _value_changed(self, command: QUndoCommand) -> None:
        self.node.nodeScene.sceneCollection.undoStack.push(command)
        self.content = self.grItem.value


@registerSlot
class IntSlot(NumSlot[int]):
    def __init__(
        self,
        node: Node,
        default: int,
        name: str,
        ind: int,
        socketPainter: SocketPainter,
        slotType: SlotType,
        min: int | None = None,
        max: int | None = None,
        step: int | None = None,
        valid: int | None = None,
        validOffset: int | None = None,
        isOptional: bool = False,
    ) -> None:
        super().__init__(
            node,
            default,
            name,
            ind,
            "INT",
            socketPainter,
            slotType,
            min,
            max,
            step,
            valid,
            validOffset,
            isOptional,
        )

    @classmethod
    def constructableFromSpec(self, spec: Any) -> bool:
        return (
            isinstance(spec, list)
            and len(spec) == 2
            and spec[0] == "INT"
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
        default = spec[1]["default"] if "default" in spec[1] else 0.0
        min = spec[1]["min"] if "min" in spec[1] else None
        max = spec[1]["max"] if "max" in spec[1] else None
        step = spec[1]["step"] if "step" in spec[1] else None

        painter = socketStyles.getSocketPainter("INT", visualHint, isOptional)

        return IntSlot(
            node,
            default,
            name,
            ind,
            painter,
            slotType,
            min,
            max,
            step,
            isOptional=isOptional,
        )

    def saveState(self) -> Dict[str, Any]:
        return {"value": self.content}

    def loadState(self, state: Dict[str, Any]) -> None:
        if "value" in state:
            self.grItem.value = state["value"]


@registerSlot
class FloatSlot(NumSlot[Decimal]):
    def __init__(
        self,
        node: Node,
        default: Decimal,
        name: str,
        ind: int,
        socketPainter: SocketPainter,
        slotType: SlotType,
        min: Decimal | None = None,
        max: Decimal | None = None,
        step: Decimal | None = None,
        valid: Decimal | None = None,
        validOffset: Decimal | None = None,
        isOptional: bool = False,
    ) -> None:
        super().__init__(
            node,
            default,
            name,
            ind,
            "FLOAT",
            socketPainter,
            slotType,
            min,
            max,
            step,
            valid,
            validOffset,
            isOptional,
        )

    @classmethod
    def constructableFromSpec(self, spec: Any) -> bool:
        return (
            isinstance(spec, list)
            and len(spec) == 2
            and spec[0] == "FLOAT"
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
        default = spec[1]["default"] if "default" in spec[1] else 0.0
        min = spec[1]["min"] if "min" in spec[1] else None
        max = spec[1]["max"] if "max" in spec[1] else None
        step = spec[1]["step"] if "step" in spec[1] else None

        painter = socketStyles.getSocketPainter("FLOAT", visualHint, isOptional)

        return FloatSlot(
            node,
            default,
            name,
            ind,
            painter,
            slotType,
            min,
            max,
            step,
            isOptional=isOptional,
        )

    def saveState(self) -> Dict[str, Any]:
        return {"value": cast(Decimal, self.content).as_tuple()}

    def loadState(self, state: Dict[str, Any]) -> None:
        if "value" in state:
            self.grItem.value = Decimal(state["value"])

    def toPrompt(self) -> Any:
        return float(self.content)
