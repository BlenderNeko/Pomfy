from __future__ import annotations
from decimal import Decimal

from typing import TYPE_CHECKING, Any, List, Type, Set, Dict
from node.socket import SocketTyping
from server import ComfyPromptManager, NodeAddress, NodeResult
from customWidgets.QSlotContentGraphicsItem import QSlotContentGraphicsItem
from node import NodeSocket
from constants import SLOT_MIN_HEIGHT, SlotType
from nodeGUI import GrNodeSlot
from style.socketStyle import SocketPainter, SocketStyles

if TYPE_CHECKING:
    from node import Node


class NodeSlot:
    def __init__(
        self,
        node: Node,
        content: Any,
        name: str,
        ind: int,
        socketTyping: SocketTyping,
        socketPainter: SocketPainter,
        slotType: SlotType,
        isOptional: bool = False,
        height: int = SLOT_MIN_HEIGHT,
    ) -> None:
        self._name = name
        self.ind = ind
        self.node = node
        self.content = content
        self.slotType = slotType
        self._height = height
        self._padding = 10
        self.optional = isOptional
        self.grContent = self.initContent(self._height)
        self.socket = self.createSocket(socketTyping, socketPainter)
        self.grNodeSlot = self.createGUI()
        if slotType == SlotType.INPUT:
            self.node.addInputSlot(self)
        if slotType == SlotType.OUTPUT:
            self.node.addOutputSlot(self)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self.grNodeSlot.name = value

    def createGUI(self) -> GrNodeSlot:
        return GrNodeSlot(self, self.grContent, self._name, self.slotType, self._height)

    def createSocket(self, socketTyping: SocketTyping, socketPainter: SocketPainter) -> NodeSocket:
        return NodeSocket(self, socketTyping, socketPainter)

    def initContent(self, height: float) -> QSlotContentGraphicsItem | None:
        raise NotImplementedError()
    
    @property
    def isOutput(self) -> bool:
        return self.slotType == SlotType.OUTPUT


    @classmethod
    def constructableFromSpec(self, spec: Any) -> bool:
        raise NotImplementedError()

    @classmethod
    def socketTypeFromSpec(cls, spec: Any) -> SocketTyping | None:
        raise NotImplementedError()

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
        raise NotImplementedError()

    def saveState(self) -> Dict[str, Any]:
        raise NotImplementedError()

    def loadState(self, state: Dict[str, Any]) -> None:
        raise NotImplementedError()

    def toPrompt(self) -> Any:
        return self.content

    def execute(
        self, promptManager: ComfyPromptManager
    ) -> NodeAddress | NodeResult | None:
        if self.slotType == SlotType.OUTPUT:
            if self.content is not None:
                return NodeResult(self.toPrompt())
            else:
                return NodeAddress(self.ind, self.node.getNodeAddress(promptManager))
        else:
            if len(self.socket.edges) == 0:
                if self.content is None and not self.optional:
                    raise ValueError("slot content can not be None")
                return NodeResult(self.toPrompt())
            target = self.socket.edges[0].outputSocket
            assert target is not None
            if target.nodeSlot.node not in promptManager.idMap:
                promptManager.executeNode(target.nodeSlot.node)
                return None
            id = promptManager.idMap[target.nodeSlot.node]
            return promptManager.outputMap[id][target.nodeSlot.ind]


_slotsToLoad: Set[Any] = set()


def registerSlot(slotCls: Type[NodeSlot]) -> Type[NodeSlot]:
    _slotsToLoad.add(slotCls)
    return slotCls


def loadSlots() -> List[NodeSlot]:
    return list(_slotsToLoad)
