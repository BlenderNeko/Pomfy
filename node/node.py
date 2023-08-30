from __future__ import annotations
from typing import TYPE_CHECKING, List, Callable, Dict, Any, Tuple
from server import ComfyPromptManager, NodeAddress, NodeResult, PartialPrompt

from PySide6.QtCore import QPointF
import PySide6.QtWidgets as QWgt

from constants import SlotType

if TYPE_CHECKING:
    from nodeSlots.nodeSlot import NodeSlot
    from node import NodeSocket, NodeScene
from nodeGUI import GrNode, BaseGrNode
from nodeSlots.slots.namedSlot import NamedSlot


class Node:
    def __init__(
        self,
        nodeScene: NodeScene,
        nodeClass: str,
        isOutput: bool = False,
        description: str = "",
        title: str = "undefined",
    ) -> None:
        self.nodeScene = nodeScene

        self.title = title
        self.nodeClass = nodeClass
        self.nodeID = -1
        self.description = description

        self._inputs: List[NodeSlot] = []
        self._outputs: List[NodeSlot] = []

        self.isOutput = isOutput

        self._namedInputs = 0

        self.grNode = self.createGUI()

        self.nodeScene.addNode(self)
        self.clientOnly: bool = False

    @property
    def inputs(self) -> List[NodeSlot]:
        return self._inputs

    @property
    def outputs(self) -> List[NodeSlot]:
        return self._outputs

    def generateSettings(self) -> List[Tuple[str, QWgt.QWidget]]:
        titleEdit = QWgt.QLineEdit()
        titleEdit.setText(self.title)
        titleEdit.textEdited.connect(self.setTitle)
        return [("Title", titleEdit)]

    def setTitle(self, title: str) -> None:
        self.title = title
        self.grNode.changeTitle(title)

    def remove(self) -> None:
        for slot in self.inputs:
            slot.socket.remove()
        for slot in self.outputs:
            slot.socket.remove()
        self.nodeScene.removeNode(self)

    def createGUI(self) -> BaseGrNode:
        return GrNode(self)

    def travelFrom(self, slotType: SlotType) -> List[NodeSlot]:
        if slotType == SlotType.OUTPUT or slotType == SlotType.BI:
            return self.inputs
        elif slotType == SlotType.INPUT:
            return self.outputs
        return []

    def addInputSlot(self, slot: NodeSlot) -> None:
        if isinstance(slot, NamedSlot):
            self.inputs.insert(self._namedInputs, slot)
            self._namedInputs += 1
        else:
            self.inputs.append(slot)
        self.grNode.setSlots()

    def removeInputSlot(self, slot: NodeSlot) -> None:
        if isinstance(slot, NamedSlot):
            self._namedInputs -= 1
        self.inputs.remove(slot)
        slot.socket.remove()
        self.grNode.unsetSlot(slot)
        self.grNode.setSlots()

    def addOutputSlot(self, slot: NodeSlot) -> None:
        self.outputs.append(slot)
        self.grNode.setSlots()

    def removeOutputSlot(self, slot: NodeSlot) -> None:
        self.outputs.remove(slot)
        slot.socket.remove()
        self.grNode.unsetSlot(slot)
        self.grNode.setSlots()

    def activateSockets(
        self, socket: NodeSocket, check: Callable[[NodeSocket], bool]
    ) -> None:
        if (
            socket.nodeSlot.slotType == SlotType.OUTPUT
            or socket.nodeSlot.slotType == SlotType.BI
        ):
            for slot in self.inputs:
                slot.socket.activateSocket(check)
        if socket.nodeSlot.slotType == SlotType.INPUT:
            for slot in self.outputs:
                slot.socket.activateSocket(check)

    def deactivateSockets(self) -> None:
        for slot in self.inputs:
            slot.socket.deactivateSocket()
        for slot in self.outputs:
            slot.socket.deactivateSocket()

    def saveState(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        state["input"] = []
        state["output"] = []
        for slot in self.inputs:
            state["input"].append(
                {
                    "ind": slot.ind,
                    "name": slot._name,
                    "typeName": slot.socket.socketType,
                    "content": slot.saveState(),
                }
            )
        for slot in self.outputs:
            state["output"].append(
                {
                    "ind": slot.ind,
                    "name": slot._name,
                    "typeName": slot.socket.socketType,
                    "content": slot.saveState(),
                }
            )
        state["position"] = self.grNode.pos().toTuple()
        state["width"] = self.grNode.width
        state["nodeClass"] = self.nodeClass
        state["title"] = self.title
        return state

    # TODO: proper error stuff
    def loadState(self, state: Dict[str, Any]) -> None:
        self.grNode.resize(state["width"])
        self.grNode.setPos(QPointF(*state["position"]))
        if "title" in state:
            self.setTitle(state["title"])
        for slotState in state["input"]:
            for x in self.inputs:
                if (
                    x._name == slotState["name"]
                    and x.socket.socketType == slotState["typeName"]
                ):
                    x.loadState(slotState["content"])
                    continue
                print(f'error in inputs: {slotState["name"]} {slotState["typeName"]}')
        for slotState in state["output"]:
            for x in self.outputs:
                if (
                    x.ind == slotState["ind"]
                    and x.socket.socketType == slotState["typeName"]
                ):
                    x.loadState(slotState["content"])
                    continue
                print(f'error in outputs: {slotState["ind"]} {slotState["typeName"]}')

    def getNodeAddress(self, promptManager: ComfyPromptManager) -> str:
        return ".".join([self.nodeClass, str(self.nodeID)])

    def getCashedExecute(
        self, promptManager: ComfyPromptManager
    ) -> Tuple[PartialPrompt, Dict[int, NodeAddress | NodeResult]] | None:
        if self in promptManager.idMap:
            id = promptManager.idMap[self]
            return (promptManager.partialPrompts[id], promptManager.outputMap[id])
        promptManager.executeNode(self)
        return None

    def execute(
        self, promptManager: ComfyPromptManager
    ) -> Tuple[PartialPrompt, Dict[int, NodeAddress | NodeResult]] | None:
        cashed = self.getCashedExecute(promptManager)
        if cashed is not None:
            return cashed

        slotResults: Dict[str, NodeAddress | NodeResult | None] = {}
        optional = []
        for slot in self.inputs:
            slotResults[slot._name] = slot.execute(promptManager)
            optional.append(slot.optional)
        for s, o in zip(slotResults.values(), optional):
            if s is None and not o:
                return None
        slotOutputs: Dict[int, NodeAddress | NodeResult] = {}
        for slot in self.outputs:
            slotOutput = slot.execute(promptManager)
            assert slotOutput is not None
            slotOutputs[slot.ind] = slotOutput
        if self.clientOnly:
            return (PartialPrompt.empty(), slotOutputs)
        return (PartialPrompt(slotResults, self.nodeClass), slotOutputs)
