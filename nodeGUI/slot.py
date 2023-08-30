from __future__ import annotations

from typing import TYPE_CHECKING, Any

from constants import SLOT_MIN_HEIGHT, SlotType
from customWidgets.QSlotContentGraphicsItem import QSlotContentGraphicsItem
from customWidgets.elidedGraphicsItem import QGraphicsElidedTextItem

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

if TYPE_CHECKING:
    from nodeSlots.nodeSlot import NodeSlot


class GrNodeSlot(QWgt.QGraphicsItem):
    @property
    def showContent(self) -> bool:
        return self._showContent

    @showContent.setter
    def showContent(self, value: bool) -> None:
        self._showContent = value
        if self._content is not None:
            self._content.setVisible(self.showContent)
        self._label.setVisible((not self.showContent) or self._content is None)
        self._height = self._base_height if self.showContent else SLOT_MIN_HEIGHT
        self.resize(self._width, True)
        self.nodeSlot.node.grNode.updateSlots()

    def setShowContent(self, value: bool) -> None:
        self.showContent = value

    def remove(self) -> None:
        if self._content is not None:
            self.nodeSlot.node.nodeScene.grScene.removeItem(self._content)
        self.nodeSlot.node.nodeScene.grScene.removeItem(self)

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float) -> None:
        self._width = value
        self.resize(self._width, True)

    def __init__(
        self,
        nodeSlot: "NodeSlot",
        content: QSlotContentGraphicsItem | None,
        name: str,
        slotType: SlotType,
        height: float = SLOT_MIN_HEIGHT,
        padding: float = 15.0,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._padding = padding
        self._width = 200
        self._base_height = height
        self._height = height
        self._name = name
        self._content: Any | None = content
        self._showContent = True
        self._slotType = slotType
        self.nodeSlot: NodeSlot = nodeSlot

        self.initUI()

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._label.rawText = self._name

    def initUI(self) -> None:
        # label
        self._label: QGraphicsElidedTextItem = QGraphicsElidedTextItem(
            self._name,
            self._width - 2 * self._padding,
            self._height,
            elidedMode=QGui.Qt.TextElideMode.ElideRight
            if self._slotType == SlotType.INPUT
            else QGui.Qt.TextElideMode.ElideLeft,
            alignLeft=self._slotType == SlotType.INPUT,
        )
        self._label.setParentItem(self)
        self._label.setAlignedPos(self._padding, 0)

        # content
        if self._content is not None:
            self._label.setVisible(False)
            self._content.setParentItem(self)
            self._content.setPos(self._padding, 0)

    def resize(self, x: float, force: bool = False) -> None:
        if x != self._width or force:
            self.prepareGeometryChange()
            self._width = x
            self._label.resize(self._width - 2 * self._padding)
            if self._content is not None:
                self._content.resize(self._width - 2 * self._padding)

    def boundingRect(self) -> QCor.QRectF:
        return QCor.QRectF(0, 0, self._width, self._height)

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        pass
