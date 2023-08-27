import collections
from functools import partial
from itertools import permutations
from decimal import Decimal
import json
from typing import Dict, Callable, Any, Type, Tuple, List, TypedDict, Literal, cast
from events import Event

import PySide6.QtCore
import PySide6.QtGui
import PySide6.QtWidgets
from constants import SlotType, SocketShape
from customWidgets.QSearchableList import QSearchableMenu
from node import Node, NodeScene
from nodeSlots import NodeSlot, loadSlots
from nodeSlots.slots.namedSlot import NamedSlot
from style.socketStyle import SocketStyles
from specialNodes.nodes import *
from specialNodes.customNode import loadCustomNodes, CustomNode

import PySide6.QtWidgets as QWgt
import PySide6.QtGui as QGui
import PySide6.QtCore as QCor

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

    def flat(self) -> List["MenuItem"]:
        items: list[MenuItem] = []
        for sub in self.subMenus.values():
            items.extend(sub.flat())
        items.extend(self.items.values())
        return items


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


class AddNodePopup:
    def __init__(
        self,
        factory: "ComfyFactory",
        search: QSearchableMenu,
        searchAction: QGui.QAction,
        onSuccess: Callable[[Node], None],
        onFail: Callable[[], None],
    ) -> None:
        self._factory = factory
        self._search = search
        self._search.abort.connect(self._searchAbort)
        self._search.finished.connect(self._searchSuccess)

        self._searchAction = searchAction
        self._searchAction.triggered.connect(self._onSearch)

        self._onSuccess = onSuccess
        self._onFail = onFail

        self._success = False
        self._performSearch = False

    def _cleanup(self) -> None:
        self._search.abort.disconnect(self._searchAbort)
        self._search.finished.disconnect(self._searchSuccess)
        self._searchAction.triggered.disconnect(self._onSearch)

    def _searchAbort(self) -> None:
        self._cleanup()
        self._onFail()

    def _searchSuccess(self, ind: int) -> None:
        node = self._search.items[ind].constructor()

    def _menuSuccess(self, node: Node) -> None:
        self._cleanup()
        self._success = True
        self._onSuccess(node)

    def show(self) -> None:
        menu = self._factory.GenerateMenu(self._menuSuccess)
        menu.move(QGui.QCursor.pos() + QCor.QPoint(5, -5))
        menu.exec()
        if not self._success and not self._performSearch:
            self._cleanup()
            self._onFail()

    def _onSearch(self) -> None:
        self._performSearch = True
        self._search.move(QGui.QCursor.pos() + QCor.QPoint(5, -5))
        self._search.clearText()
        self._search.show()


class _SlotInfo:
    def __init__(
        self,
        className: str,
        displayName: str,
        socketType: str,
        slotType: SlotType,
        slotName: str,
        slotInd: int,
    ) -> None:
        self.className = className
        self.displayName = displayName
        self.socketType = socketType
        self.slotType = slotType
        self.slotName = slotName
        self.slotInd = slotInd

    def nodeNameCheck(self, s: str) -> bool:
        return (
            s.lower() in self.className.lower() or s.lower() in self.displayName.lower()
        )

    def slotNameCheck(self, s: str) -> bool:
        return s.lower() in self.slotName

    def match(self, searchString: str) -> bool:
        words = searchString.split(" ")
        for i in range(len(words)):
            a = " ".join(words[i:])
            b = " ".join(words[:i])

            if (self.nodeNameCheck(a) and self.slotNameCheck(b)) or (
                self.nodeNameCheck(b) and self.slotNameCheck(a)
            ):
                return True
        return False


class ComfyFactory:
    def __init__(self, socketStyles: SocketStyles) -> None:
        self._nodeDefinitions: ComfySpec = {}
        self._specialNodes: Dict[str, Callable[["ComfyFactory", Any], Node]] = {}
        self._menuStructure: MenuData = MenuData("")
        self.socketStyles = socketStyles
        self.activeScene: NodeScene | None = None
        self._menu: QWgt.QMenu | None = None
        self._flatMenu: List[MenuItem] | None = None
        self._ExpandSearchList: List[_SlotInfo] = []
        self._DetailedSearch: QSearchableMenu | None = None
        self._onCreate: Callable[[Node], None] | None = None

    def GenerateMenu(
        self, onCreate: Callable[[Node], None] | None = None
    ) -> QWgt.QMenu:
        self._generateMenu()
        assert self._menu is not None
        self._onCreate = onCreate
        return self._menu

    def _generateMenu(self) -> None:
        if self._menu is None:
            self._menu = self._buildSubMenu(self._menuStructure)
            self._flatMenu = self._menuStructure.flat()
            self._searchAction = QGui.QAction("search")
            self._SimpleSearch = QSearchableMenu(
                self._flatMenu,
                lambda x: x.displayName,
                lambda x, y: y.lower() in x.displayName.lower()
                or y.lower() in x.name.lower(),
                maxRows=10,
            )
            self._SimpleSearch.hide()
            self._SimpleSearch.setWindowFlags(
                QGui.Qt.WindowType.Popup | QGui.Qt.WindowType.BypassGraphicsProxyWidget
            )

            self._menu.insertAction(self._menu.actions()[0], self._searchAction)

    def requestAddNode(
        self, onSuccess: Callable[[Node], None], onFail: Callable[[], None]
    ) -> None:
        self._generateMenu()
        assert self._flatMenu is not None
        popup = AddNodePopup(
            self,
            self._SimpleSearch,
            self._searchAction,
            onSuccess,
            onFail,
        )
        popup.show()

    def getDetailedSearch(self) -> QSearchableMenu:
        if self._DetailedSearch is None:
            self._DetailedSearch = QSearchableMenu(
                self._ExpandSearchList,
                lambda x: f"{x.displayName} > {x.slotName}",
                lambda x, y: x.match(y),
                maxRows=10,
            )
            self._DetailedSearch.hide()
            self._DetailedSearch.setWindowFlags(
                QGui.Qt.WindowType.Popup | QGui.Qt.WindowType.BypassGraphicsProxyWidget
            )
        self._DetailedSearch.setFilter(lambda x, y: x.match(y))
        return self._DetailedSearch

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

    def setSpecialNode(
        self, id: str, constructor: Callable[["ComfyFactory", Any], Node]
    ) -> None:
        self._specialNodes[id] = constructor

    def expandSearchInfoFromDef(self, name: str, nodeDef: ComfyNodeSpec) -> None:
        slotTypes = loadSlots()

        def getSocketType(spec: Any) -> str:
            for s in slotTypes:
                typeName = s.socketTypeFromSpec(spec)
                if typeName is not None:
                    return typeName
            return "UNDEFINED"

        if "input" in nodeDef:
            inputs = nodeDef["input"]
            if "required" in inputs:
                for i, (key, value) in enumerate(inputs["required"].items()):
                    self._ExpandSearchList.append(
                        _SlotInfo(
                            name,
                            nodeDef["display_name"],
                            getSocketType(value),
                            SlotType.INPUT,
                            key,
                            i,
                        )
                    )
            if "optional" in inputs:
                assert inputs["optional"] is not None
                offset = len(inputs["required"]) if "required" in inputs else 0
                for i, (key, value) in enumerate(inputs["optional"].items()):
                    self._ExpandSearchList.append(
                        _SlotInfo(
                            name,
                            nodeDef["display_name"],
                            getSocketType(value),
                            SlotType.INPUT,
                            key,
                            i + offset,
                        )
                    )
        for i, (slotName, typeName) in enumerate(
            zip(nodeDef["output_name"], nodeDef["output"])
        ):
            self._ExpandSearchList.append(
                _SlotInfo(
                    name,
                    nodeDef["display_name"],
                    typeName,
                    SlotType.OUTPUT,
                    slotName,
                    i,
                )
            )

    def expandSearchInfoFromCustom(self, node: Type[CustomNode]) -> None:
        for i, (name, typeName) in enumerate(node.searchableInputs()):
            self._ExpandSearchList.append(
                _SlotInfo(
                    node.getClassName(),
                    node.getDisplayName(),
                    typeName,
                    SlotType.INPUT,
                    name,
                    i,
                )
            )
        for i, (name, typeName) in enumerate(node.searchableOutputs()):
            self._ExpandSearchList.append(
                _SlotInfo(
                    node.getClassName(),
                    node.getDisplayName(),
                    typeName,
                    SlotType.OUTPUT,
                    name,
                    i,
                )
            )

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
            self.expandSearchInfoFromDef(key, value)
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
            self.expandSearchInfoFromCustom(customNode)

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
