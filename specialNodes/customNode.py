from __future__ import annotations

from typing import TYPE_CHECKING, Set, Type, Any, List, Tuple

from node import Node


if TYPE_CHECKING:
    from node import NodeScene
    from node.factory import ComfyFactory


class CustomNode:
    @classmethod
    def getCategory(cls) -> str | None:
        raise NotImplementedError()

    @classmethod
    def getClassName(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def getDisplayName(cls) -> str:
        raise NotImplementedError()

    @classmethod
    def createNode(cls, factory: ComfyFactory, nodeDef: Any) -> Node:
        raise NotImplementedError()

    @classmethod
    def searchableInputs(cls) -> List[Tuple[str, str]]:
        return []

    @classmethod
    def searchableOutputs(cls) -> List[Tuple[str, str]]:
        return []


_nodesToLoad: Set[Any] = set()


def registerCustomNode(slotCls: Type[CustomNode]) -> Type[CustomNode]:
    _nodesToLoad.add(slotCls)
    return slotCls


def loadCustomNodes() -> List[Type[CustomNode]]:
    return list(_nodesToLoad)
