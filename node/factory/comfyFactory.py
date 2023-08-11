import collections
from functools import partial
from decimal import Decimal
import json
from typing import Dict, Callable, Any, Tuple, List, TypedDict, Literal, cast
from constants import SlotType, SocketShape
from node import Node, NodeScene
from nodeSlots import NodeSlot, loadSlots
from nodeSlots.slots.namedSlot import NamedSlot
from style.socketStyle import SocketStyles
from specialNodes.nodes import *
from specialNodes.customNode import loadCustomNodes

import PySide6.QtWidgets as QWgt

# input type of comfy nodes json file


class ComfyFloat(TypedDict):
    default: Decimal
    min: Decimal
    max: Decimal
    step: Decimal


class ComfyInt(TypedDict):
    default: int
    min: int
    max: int
    step: int


class ComfyString(TypedDict, total=False):
    multiline: bool
    default: str


ComfyComplexType = Tuple[str]
ComfyComboType = Tuple[List[str]]
ComfyPrimitive = (
    Tuple[Literal["FLOAT"], ComfyFloat]
    | Tuple[Literal["INT"], ComfyInt]
    | Tuple[Literal["STRING"], ComfyString]
)
ComfyNodeInputSpec = ComfyPrimitive | ComfyComboType | ComfyComplexType


class ComfyNodeInputsSpec(TypedDict):
    required: Dict[str, ComfyNodeInputSpec]
    optional: Dict[str, ComfyNodeInputSpec] | None
    # using this since only since 3.11 do we have optional keys
    # leaving out hidden inputs


class ComfyNodeSpec(TypedDict):
    name: str
    display_name: str
    description: str
    category: str
    output_node: bool
    input: ComfyNodeInputsSpec
    output: List[str]
    output_is_list: List[bool]
    output_name: List[str]


ComfySpec = Dict[str, ComfyNodeSpec]


class MenuData:
    def __init__(self, name: str) -> None:
        self.subMenus: Dict[str, "MenuData"] = dict()
        self.items: Dict[str, "MenuItem"] = dict()
        self.name = name

    def addItem(
        self,
        categories: List[str],
        displayName: str,
        className: str,
        constructor: Callable[[], Node],
    ) -> None:
        if len(categories) == 0:
            self.items[className] = MenuItem(className, displayName, constructor)
            return
        cat = categories.pop(0)
        if cat not in self.subMenus:
            self.subMenus[cat] = MenuData(cat)
        self.subMenus[cat].addItem(categories, displayName, className, constructor)


class MenuItem:
    def __init__(
        self,
        name: str,
        displayName: str,
        constructor: Callable[[], Node],
    ) -> None:
        self.name = name
        self.displayName = displayName
        self.constructor = constructor


class ComfyFactory:
    def __init__(self, socketStyles: SocketStyles) -> None:
        self._nodeDefinitions: ComfySpec = {}
        self._specialNodes: Dict[str, Callable[["ComfyFactory", Any], Node]] = {}
        self._menuStructure: MenuData = MenuData("")
        self.socketStyles = socketStyles
        self.activeScene: NodeScene | None = None
        self._menu: QWgt.QMenu | None = None
        self._onCreate: Callable[[Node], None] | None = None

    def GenerateMenu(
        self, onCreate: Callable[[Node], None] | None = None
    ) -> QWgt.QMenu:
        if self._menu is None:
            self._menu = self._buildSubMenu(self._menuStructure)
        self._onCreate = onCreate
        return self._menu

    def _buildSubMenu(self, menuData: MenuData) -> QWgt.QMenu:
        menu = QWgt.QMenu(menuData.name)

        subMenus = list(menuData.subMenus.values())
        subMenus.sort(key=lambda x: x.name)
        for subMenu in subMenus:
            menu.addMenu(self._buildSubMenu(subMenu))
        items = list(menuData.items.values())
        items.sort(key=lambda x: x.displayName)
        for item in items:
            action = menu.addAction(item.displayName)
            action.triggered.connect(item.constructor)

        return menu

    def setTypeInfo(self) -> None:
        ...

    def getTypeInfo(self, name: str) -> None:
        ...

    def setSpecialNode(
        self, id: str, constructor: Callable[["ComfyFactory", Any], Node]
    ) -> None:
        self._specialNodes[id] = constructor

    def loadNodeDefinitions(self, jsonString: str) -> None:
        self._menuStructure = MenuData("")
        nodeDefinitions = json.loads(
            jsonString, object_pairs_hook=collections.OrderedDict, parse_float=Decimal
        )
        self._nodeDefinitions = nodeDefinitions
        for key, value in self._nodeDefinitions.items():
            categories = value["category"].split("/")
            self._menuStructure.addItem(
                categories,
                value["display_name"],
                key,
                partial(self._loadNode, name=key),
            )
        for customNode in loadCustomNodes():
            custom_categories = customNode.getCategory()
            assert custom_categories is not None
            className = customNode.getClassName()
            displayName = customNode.getDisplayName()
            self._menuStructure.addItem(
                custom_categories.split("/"),
                displayName,
                className,
                partial(self._loadNode, name=className),
            )
            self.setSpecialNode(className, customNode.createNode)

    def _loadNode(self, name: str) -> Node:
        assert self.activeScene is not None
        # self.activeScene.sceneCollection.ntm.startTransaction()
        node = self.loadNode(name)
        if self._onCreate is not None:
            self._onCreate(node)
        self._onCreate = None
        # self.activeScene.sceneCollection.ntm.finalizeTransaction()
        return node

    def loadNode(self, name: str) -> Node:
        assert self.activeScene is not None
        nodeDef = self._nodeDefinitions.get(name, None)
        if name in self._specialNodes:
            node = self._specialNodes[name](self, nodeDef)
        elif nodeDef is None:
            raise KeyError(f"No node definition found for {name}")
        else:
            node = Node(
                self.activeScene,
                name,
                nodeDef["output_node"],
                nodeDef["description"],
                nodeDef["display_name"],
            )
            # create inputs
            if "input" in nodeDef.keys():
                if "required" in nodeDef["input"].keys():
                    for ind, (key, item) in enumerate(
                        nodeDef["input"]["required"].items()
                    ):
                        self.loadInputSlot(node, key, ind, item, False)
                if "optional" in nodeDef["input"].keys():
                    assert nodeDef["input"]["optional"] is not None
                    requiredCount = (
                        len(nodeDef["input"]["required"])
                        if "required" in nodeDef["input"]
                        else 0
                    )
                    for ind, (key, item) in enumerate(
                        nodeDef["input"]["optional"].items()
                    ):
                        self.loadInputSlot(node, key, ind + requiredCount, item, True)
                # create outputs
                if "output" in nodeDef.keys():
                    for i in range(len(nodeDef["output"])):
                        self.loadNamedOutputSlot(node, i, nodeDef)
        return node

    def loadInputSlot(
        self,
        node: Node,
        name: str,
        ind: int,
        slotDef: ComfyNodeInputSpec,
        optional: bool,
    ) -> NodeSlot:
        slotTypes = loadSlots()

        for slotType in slotTypes:
            slot = slotType.fromSpec(
                self.socketStyles,
                node,
                name,
                ind,
                slotDef,
                SlotType.INPUT,
                "node",
                optional,
            )
            if slot is not None:
                return slot

        raise KeyError("No such slot type found")

    def loadNamedOutputSlot(
        self, node: Node, ind: int, nodeDef: ComfyNodeSpec
    ) -> NamedSlot:
        name = nodeDef["output_name"][ind]
        socketTypeName = nodeDef["output"][ind]
        visualHint = "array" if nodeDef["output_is_list"][ind] else "node"

        return cast(
            NamedSlot,
            NamedSlot.fromSpec(
                self.socketStyles,
                node,
                name,
                ind,
                [socketTypeName],
                SlotType.OUTPUT,
                visualHint,
                False,
            ),
        )
