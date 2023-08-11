from __future__ import annotations

from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from node import Node, NodeScene
import json


class ComfyPromptManager:
    def __init__(self) -> None:
        self.idMap: Dict[Node, str] = {}
        self.outputMap: Dict[str, Dict[int, NodeAddress | NodeResult]] = {}
        self.partialPrompts: Dict[str, PartialPrompt] = {}
        self.executionStack: List[Node] = []

    def executeNode(self, node: Node) -> None:
        self.executionStack.append(node)

    def execute(self, nodescenes: List[NodeScene]) -> Dict[str, Any]:
        # find output nodes
        outputNodes: List[Node] = []
        for scene in nodescenes:
            outputNodes.extend([s for s in scene.nodes if s.isOutput])

        # try construct prompt for each output node
        for outputNode in outputNodes:
            try:
                self.executeNode(outputNode)
                while len(self.executionStack) > 0:
                    node = self.executionStack.pop()
                    result = node.execute(self)
                    if result is not None:
                        nodeAddress = node.getNodeAddress(self)
                        self.idMap[node] = nodeAddress
                        self.partialPrompts[nodeAddress] = result[0]
                        self.outputMap[nodeAddress] = result[1]
            except:
                ...

        # convert to json
        prompt: Dict[str, Any] = {}
        for k, v in self.partialPrompts.items():
            if not v.isEmpty:
                prompt[k] = v.toPrompt()
        return prompt


class NodeAddress:
    def __init__(self, slotInd: int, nodeID: str) -> None:
        self.nodeID: str = nodeID
        self.slotInd: int = slotInd

    def toPrompt(self) -> Any:
        return [self.nodeID, self.slotInd]


class NodeResult:
    def __init__(self, value: Any) -> None:
        self.value: Any = value

    def toPrompt(self) -> Any:
        return self.value


class PartialPrompt:
    def __init__(
        self, inputs: Dict[str, NodeAddress | NodeResult | None], className: str
    ) -> None:
        self.className: str = className
        self.inputs: Dict[str, NodeAddress | NodeResult | None] = inputs
        self.isEmpty: bool = self.className == ""

    @classmethod
    def empty(cls) -> "PartialPrompt":
        return cls({}, "")

    def toPrompt(self) -> Dict[str, Any]:
        return {
            "class_type": self.className,
            "inputs": {
                k: v.toPrompt() for k, v in self.inputs.items() if v is not None
            },
        }
