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
from specialNodes.nodes.expandableNode import ExpandableNode


if TYPE_CHECKING:
    from node.factory import ComfyFactory

from node import Node, NodeScene
from specialNodes.customNode import CustomNode, registerCustomNode


@registerCustomNode
class GroupIn(ExpandableNode, CustomNode):
    def __init__(
        self,
        nodeScene: NodeScene,
        nodeClass: str,
        isOutput: bool = False,
        description: str = "",
        title: str = "undefined",
    ) -> None:
        super().__init__(nodeScene, nodeClass, isOutput, description, title)

    @classmethod
    def getClassName(cls) -> str:
        return "GroupIn"

    @classmethod
    def getDisplayName(cls) -> str:
        return "Group Input"

    @classmethod
    def getCategory(cls) -> str | None:
        return "Layout"

    @classmethod
    def createNode(cls, factory: ComfyFactory, nodeDef: Any) -> Node:
        assert factory.activeScene is not None
        node = cls(
            factory.activeScene,
            cls.getClassName(),
            description="group node input",
            title=cls.getDisplayName(),
        )
        node.addExpandableOutput()
        return node
