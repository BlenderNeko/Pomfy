from __future__ import annotations
from typing import TYPE_CHECKING, Any


import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt
from PySide6.QtCore import QRectF, QPointF

from enum import Flag, auto

from constants import SLOT_MIN_HEIGHT
from customWidgets.elidedGraphicsItem import QGraphicsElidedTextItem

if TYPE_CHECKING:
    from node import Node
    from nodeSlots.nodeSlot import NodeSlot


class ResizeEnum(Flag):
    NONE = 0
    LEFT = auto()
    RIGHT = auto()


class ResizeState:
    def __init__(self) -> None:
        self.resizeState = ResizeEnum.NONE


class resizeBound(QWgt.QGraphicsItem):
    def __init__(
        self,
        width: float,
        height: float,
        resizeState: ResizeState,
        resizeType: ResizeEnum,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._width = width
        self._height = height
        self._resizeType = resizeType
        self._resizeState = resizeState
        self.setAcceptHoverEvents(True)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        pass

    def hoverEnterEvent(self, event: QWgt.QGraphicsSceneHoverEvent) -> None:
        self.setCursor(QGui.Qt.CursorShape.SizeHorCursor)
        self._resizeState.resizeState = self._resizeState.resizeState | self._resizeType

    def hoverLeaveEvent(self, event: QWgt.QGraphicsSceneHoverEvent) -> None:
        self.setCursor(QGui.Qt.CursorShape.ArrowCursor)
        self._resizeState.resizeState = (
            self._resizeState.resizeState & ~self._resizeType
        )

    def resize(self, y: float) -> None:
        old_h = self._height
        self._height = y
        self.update(QRectF(0, old_h, self._width, self._height - y).normalized())


class BaseGrNode(QWgt.QGraphicsItem):
    @property
    def width(self) -> float:
        return self._width

    def __init__(self, node: Node, parent: QWgt.QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.node = node
        self._pen_default = QGui.QPen(QGui.QColor("#7F000000"))
        self._pen_selected = QGui.QPen(QGui.QColor("#FFA637"))
        self._pen_selected.setWidthF(2.0)
        self._pen_active = QGui.QPen(QGui.QColor("#F6E300"))
        self._pen_active.setWidthF(2.0)
        self._width: float = 100.0
        self._active = False

    def resize(self, width: float) -> None:
        pass

    def setSlots(self) -> None:
        pass

    def unsetSlot(self, slot: NodeSlot) -> None:
        pass

    def updateSlots(self) -> None:
        pass

    def changeTitle(self, title: str) -> None:
        pass

    @property
    def activeNode(self) -> bool:
        return self._active

    @activeNode.setter
    def activeNode(self, value: bool) -> None:
        self._active = value


class GrNode(BaseGrNode):
    def __init__(self, node: Node, parent: QWgt.QGraphicsItem | None = None) -> None:
        super().__init__(node, parent)

        self._title_color = QGui.QColor("#ffffff")
        self._title_font = QGui.QFont("Sans Serif", 10)

        self._StoredState = (0.0, 0.0, 0.0)  # x y w

        self._width = 180.0
        self.height: float = 100.0
        self.edge_size = 10.0
        self.title_height = 24.0
        self._padding = 20.0

        self._resizing = ResizeState()
        self._resize_bounds = 5.0
        self._lBound = resizeBound(
            self._resize_bounds, self.height, self._resizing, ResizeEnum.LEFT, self
        )
        self._rBound = resizeBound(
            self._resize_bounds, self.height, self._resizing, ResizeEnum.RIGHT, self
        )
        self._rBound.setPos(self.width - 5, 0)

        # self.setAcceptHoverEvents(True)
        self.initUI()

        self._brush_title = QGui.QBrush(QGui.QColor("#5ECE2A"))
        self._brush_background = QGui.QBrush(QGui.QColor("#E3212121"))

    def initUI(self) -> None:
        self.initTitle()
        self.setFlag(QWgt.QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QWgt.QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QWgt.QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def updatePaint(self) -> None:
        titlePath = QGui.QPainterPath()
        titlePath.setFillRule(QGui.Qt.FillRule.WindingFill)
        titlePath.addRoundedRect(
            0, 0, self.width, self.title_height, self.edge_size, self.edge_size
        )
        titlePath.addRect(
            0, self.title_height - self.edge_size, self.width, self.edge_size
        )
        self._titlePath = titlePath.simplified()

        contentPath = QGui.QPainterPath()
        contentPath.setFillRule(QGui.Qt.FillRule.WindingFill)
        contentPath.addRoundedRect(
            0,
            self.title_height,
            self.width,
            self.height - self.title_height,
            self.edge_size,
            self.edge_size,
        )
        contentPath.addRect(0, self.title_height, self.width, self.edge_size)
        self._contentPath = contentPath.simplified()

        outlinePath = QGui.QPainterPath()
        outlinePath.addRoundedRect(
            0, 0, self.width, self.height, self.edge_size, self.edge_size
        )
        self._outlinePath = outlinePath.simplified()

    def updateEdges(self) -> None:
        for slot in self.node.inputs:
            slot.socket.updateEdges()
        for slot in self.node.outputs:
            slot.socket.updateEdges()

    def setSlots(self) -> None:
        for slot in self.node.outputs:
            slot.grNodeSlot.setParentItem(self)
            slot.grNodeSlot.width = self.width
            slot.socket.grNodeSocket.setParentItem(self)
        for slot in self.node.inputs:
            slot.grNodeSlot.setParentItem(self)
            slot.grNodeSlot.width = self.width
            slot.socket.grNodeSocket.setParentItem(self)
        self.updateSlots()

    def unsetSlot(self, slot: NodeSlot) -> None:
        self.node.nodeScene.grScene.removeItem(slot.grNodeSlot)
        self.node.nodeScene.grScene.removeItem(slot.socket.grNodeSocket)

    def updateSlots(self) -> None:
        pos = 30.0
        for slot in self.node.outputs:
            slot.grNodeSlot.setPos(0, pos)
            slot.socket.grNodeSocket.setPos(self.width - SLOT_MIN_HEIGHT / 2, pos)
            pos += slot.grNodeSlot._height + 10
        pos += 15
        for slot in self.node.inputs:
            slot.grNodeSlot.setPos(0, pos)
            slot.socket.grNodeSocket.setPos(-SLOT_MIN_HEIGHT / 2, pos)
            pos += slot.grNodeSlot._height + 10
        self.height = pos + 15
        self._lBound.resize(self.height)
        self._rBound.resize(self.height)
        self.updatePaint()

    def initTitle(self) -> None:
        self.title_label = QGraphicsElidedTextItem(
            self.node.title,
            self.width - 2 * self._padding,
            self.title_height,
            parent=self,
        )
        self.title_label.setAlignedPos(self._padding, 0)

    def changeTitle(self, title: str) -> None:
        self.title_label.rawText = title

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height).normalized()

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        # title
        painter.setPen(QGui.Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(self._titlePath)

        # content
        painter.setPen(QGui.Qt.PenStyle.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(self._contentPath)

        # outline
        outlinePen = self._pen_default
        if self.isSelected():
            outlinePen = self._pen_selected
        if self.activeNode:
            outlinePen = self._pen_active
        painter.setPen(outlinePen)
        painter.setBrush(QGui.Qt.BrushStyle.NoBrush)
        painter.drawPath(self._outlinePath)

    # ===================
    # node resizing logic

    def resize(self, width: float, force: bool = False) -> None:
        if width != self.width or force:
            self._width = width
            self.title_label.resize(self.width - 2 * self._padding)
            self.update(self.width - self._resize_bounds, 0, 10, self.height)
            self._rBound.setPos(self.width - 5, 0)
            for slot in self.node.inputs:
                slot.grNodeSlot.resize(self.width)
            for slot in self.node.outputs:
                slot.grNodeSlot.resize(self.width)
                pos_y = slot.socket.grNodeSocket.pos().y()
                slot.socket.grNodeSocket.setPos(self.width - SLOT_MIN_HEIGHT / 2, pos_y)
            self.updatePaint()
            self.updateEdges()

    def itemChange(
        self, change: QWgt.QGraphicsItem.GraphicsItemChange, value: Any
    ) -> Any:
        if change == QWgt.QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self.updateEdges()
        return value

    def mousePressEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        if event.button() != QGui.Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        pos = self.pos()
        self._StoredState = (pos.x(), pos.y(), self.width)
        if self._resizing.resizeState != ResizeEnum.NONE:
            self.setFlag(QWgt.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        if self._resizing.resizeState == ResizeEnum.NONE:
            return super().mouseMoveEvent(event)
        x = 0.0
        if ResizeEnum.RIGHT in self._resizing.resizeState:
            x = event.pos().x() - event.lastPos().x()
        if ResizeEnum.LEFT in self._resizing.resizeState:
            p = self.pos()
            x = event.lastPos().x() - event.pos().x()
            self.setPos(p.x() - x, p.y())
        self.resize(self.width + x)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        self.setFlag(QWgt.QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        with self.node.nodeScene.sceneCollection.ntm:
            pos = self.pos()
            if pos.x() != self._StoredState[0] or pos.y() != self._StoredState[1]:
                previousPos = QPointF(self._StoredState[0], self._StoredState[1])
                self.node.nodeScene.sceneCollection.ntm.doStep(
                    lambda: self.setPos(pos), lambda: self.setPos(previousPos)
                )
            if self.width != self._StoredState[2]:
                previousW = self._StoredState[2]
                currentW = self.width
                self.node.nodeScene.sceneCollection.ntm.doStep(
                    lambda: self.resize(currentW),
                    lambda: self.resize(previousW),
                )
        return super().mouseReleaseEvent(event)

    @property
    def title(self) -> str:
        return self.node.title

    @title.setter
    def title(self, value: str) -> None:
        self.node.title = value
        # self.title_item.setPlainText(self.node.title)
