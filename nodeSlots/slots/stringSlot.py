from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict
from customWidgets.QSlotContentGraphicsItem import (
    QSlotContentGraphicsItem,
    QSlotContentProxyGraphicsItem,
)


from PySide6.QtGui import Qt
import PySide6.QtWidgets as QWgt

from style.socketStyle import SocketPainter, SocketStyles
from constants import SlotType

if TYPE_CHECKING:
    from node import Node


from nodeSlots.nodeSlot import NodeSlot, registerSlot


@registerSlot
class MultiLineTextSlot(NodeSlot):
    SocketTypeName = "STRING"

    def __init__(
        self,
        node: Node,
        placeholderText: str,
        name: str,
        ind: int,
        socketPainter: SocketPainter,
        slotType: SlotType,
        default: str = "",
        isOptional: bool = False,
        height: int = 100,
    ) -> None:
        self.placeholder = placeholderText
        self.default = default
        super().__init__(
            node,
            default,
            name,
            ind,
            self.SocketTypeName,
            socketPainter,
            slotType,
            isOptional,
            height,
        )

    def initContent(self, height: float) -> QSlotContentGraphicsItem | None:
        self.widget = QWgt.QPlainTextEdit(self.content)
        self.widget.setPlainText(self.default)
        self.widget.textChanged.connect(self._textChanged)
        self.widget.setPlaceholderText(self.placeholder)
        self.widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.proxy = QSlotContentProxyGraphicsItem(self.widget, 100, height)
        return self.proxy

    @classmethod
    def constructableFromSpec(cls, spec: Any) -> bool:
        return (
            isinstance(spec, list)
            and len(spec) == 2
            and spec[0] == cls.SocketTypeName
            and isinstance(spec[1], dict)
            and "multiline" in spec[1]
            and spec[1]["multiline"]
        )

    @classmethod
    def socketTypeFromSpec(cls, spec: Any) -> str | None:
        if cls.constructableFromSpec(spec):
            return cls.SocketTypeName
        return None

    @classmethod
    def fromSpec(
        cls,
        socketStyles: SocketStyles,
        node: Node,
        name: str,
        ind: int,
        spec: Any,
        slotType: SlotType,
        visualHint: str,
        isOptional: bool,
    ) -> NodeSlot | None:
        if not cls.constructableFromSpec(spec):
            return None
        default = spec[1]["default"] if "default" in spec[1] else ""
        painter = socketStyles.getSocketPainter(
            cls.SocketTypeName, visualHint, isOptional
        )
        return MultiLineTextSlot(node, name, name, ind, painter, slotType, default)

    def _textChanged(self) -> None:
        self.content = self.widget.toPlainText()

    def saveState(self) -> Dict[str, Any]:
        return {"value": self.content}

    def loadState(self, state: Dict[str, Any]) -> None:
        if "value" in state:
            self.widget.setPlainText(state["value"])


@registerSlot
class TextSlot(NodeSlot):
    SocketTypeName = "STRING"

    def __init__(
        self,
        node: Node,
        placeholderText: str,
        name: str,
        ind: int,
        socketPainter: SocketPainter,
        slotType: SlotType,
        default: str = "",
        isOptional: bool = False,
    ) -> None:
        self.placeholder = placeholderText
        self.default = default
        super().__init__(
            node,
            default,
            name,
            ind,
            self.SocketTypeName,
            socketPainter,
            slotType,
            isOptional,
        )

    def initContent(self, height: float) -> QSlotContentGraphicsItem | None:
        self.widget = QWgt.QLineEdit(self.content)
        self.widget.setText(self.default)
        self.widget.textChanged.connect(self._textChanged)
        self.widget.setPlaceholderText(self.placeholder)
        self.widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.proxy = QSlotContentProxyGraphicsItem(self.widget, 100, height)
        return self.proxy

    @classmethod
    def constructableFromSpec(cls, spec: Any) -> bool:
        return (
            isinstance(spec, list)
            and len(spec) == 2
            and spec[0] == cls.SocketTypeName
            and isinstance(spec[1], dict)
            and ("multiline" not in spec[1] or not spec[1]["multiline"])
        )

    @classmethod
    def socketTypeFromSpec(cls, spec: Any) -> str | None:
        if cls.constructableFromSpec(spec):
            return cls.SocketTypeName
        return None

    @classmethod
    def fromSpec(
        cls,
        socketStyles: SocketStyles,
        node: Node,
        name: str,
        ind: int,
        spec: Any,
        slotType: SlotType,
        visualHint: str,
        isOptional: bool,
    ) -> NodeSlot | None:
        if not cls.constructableFromSpec(spec):
            return None
        default = spec[1]["default"] if "default" in spec[1] else ""
        painter = socketStyles.getSocketPainter(
            cls.SocketTypeName, visualHint, isOptional
        )
        return TextSlot(node, name, name, ind, painter, slotType, default)

    def _textChanged(self) -> None:
        self.content = self.widget.text()

    def saveState(self) -> Dict[str, Any]:
        return {"value": self.content}

    def loadState(self, state: Dict[str, Any]) -> None:
        if "value" in state:
            self.widget.setText(state["value"])
