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
from constants import SlotType
from customWidgets.QNumSpinner import QNumSpinner

if TYPE_CHECKING:
    from node.factory import ComfyFactory
    from node.socket import NodeSocket
    from node.socket import ConnectionChangedEvent

from node import Node, NodeScene
from nodeSlots.slots.numSlot import FloatSlot, IntSlot, NumSlot
from nodeSlots import NodeSlot
from specialNodes.customNode import CustomNode, registerCustomNode
from decimal import Decimal

T = TypeVar("T", Decimal, int)


class NumPrimitive(Node, CustomNode, Generic[T]):
    def __init__(
        self,
        nodeScene: NodeScene,
        nodeClass: str,
        isOutput: bool = False,
        description: str = "",
        title: str = "",
    ) -> None:
        super().__init__(nodeScene, nodeClass, isOutput, description, title)
        self.clientOnly = True

    @classmethod
    def getCategory(cls) -> str | None:
        return "Input"

    def recalcSpinnerSettings(self, cce: ConnectionChangedEvent) -> None:
        slots = []
        slot: NumSlot[T] = cast(NumSlot[T], self.outputs[0])
        for socket in slot.socket.getConnected():
            slots.append(socket.nodeSlot)
        if len(slots) == 0:
            slot.grItem.min = None
            slot.grItem.max = None
            slot.grItem.step = (
                Decimal("0.1") if isinstance(slot.grItem.step, Decimal) else 1
            )
            slot.grItem.valid = None
            slot.grItem.validOffset = None

        minVals = list(self.collectValues(slots, lambda x: x.min))
        if len(minVals) > 0:
            slot.grItem.min = max(minVals)

        maxVals = list(self.collectValues(slots, lambda x: x.max))
        if len(maxVals) > 0:
            slot.grItem.max = min(maxVals)

        steps = list(self.collectValues(slots, lambda x: x.step))
        if len(steps) > 0:
            slot.grItem.step = min(steps)

    def collectValues(
        self, slots: List[NodeSlot], func: Callable[[QNumSpinner], T | None]
    ) -> Generator[T, None, None]:
        for slot in slots:
            if isinstance(slot.grContent, QNumSpinner):
                value = func(slot.grContent)
                if value is not None:
                    yield value


@registerCustomNode
class FloatPrimitive(NumPrimitive[Decimal]):
    @classmethod
    def getClassName(cls) -> str:
        return "FloatPrimitive"

    @classmethod
    def getDisplayName(cls) -> str:
        return "Float"

    @classmethod
    def createNode(cls, factory: ComfyFactory, nodeDef: Any) -> Node:
        assert factory.activeScene is not None
        node = cls(
            factory.activeScene,
            cls.getClassName(),
            description="Float primitive",
            title="Float",
        )
        painter = factory.socketStyles.getSocketPainter("FLOAT", "node", False)
        floatSlot: FloatSlot = FloatSlot(
            node, Decimal("0.0"), "value", 0, painter, SlotType.OUTPUT
        )
        floatSlot.socket.onConnectionChanged += node.recalcSpinnerSettings

        return node

    @classmethod
    def searchableOutputs(cls) -> List[Tuple[str, str]]:
        return [("value", "FLOAT")]


@registerCustomNode
class IntPrimitive(NumPrimitive[Decimal]):
    @classmethod
    def getClassName(cls) -> str:
        return "IntegerPrimitive"

    @classmethod
    def getDisplayName(cls) -> str:
        return "Integer"

    @classmethod
    def createNode(cls, factory: ComfyFactory, nodeDef: Any) -> Node:
        assert factory.activeScene is not None
        node = cls(
            factory.activeScene,
            cls.getClassName(),
            description="Integer primitive",
            title="Integer",
        )
        painter = factory.socketStyles.getSocketPainter("INT", "node", False)
        intSlot: IntSlot = IntSlot(node, 0, "value", 0, painter, SlotType.OUTPUT)
        intSlot.socket.onConnectionChanged += node.recalcSpinnerSettings

        return node

    @classmethod
    def searchableOutputs(cls) -> List[Tuple[str, str]]:
        return [("value", "INT")]
