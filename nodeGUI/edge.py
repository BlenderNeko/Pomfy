from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from node import NodeEdge

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from PySide6.QtCore import QPointF


class EdgeType(Enum):
    STRAIGHT = 0
    MANHATTAN = 1
    BEZIER = 2


class GrNodeEdge(QWgt.QGraphicsPathItem):
    @property
    def nodeEdge(self) -> "NodeEdge":
        return self._nodeEdge

    @property
    def start(self) -> QPointF:
        """starting point of the edge"""
        return self._start

    @start.setter
    def start(self, value: QPointF) -> None:
        self._start = value
        self.updatePath()

    @property
    def end(self) -> QPointF:
        """ending point of the edge"""
        return self._end

    @end.setter
    def end(self, value: QPointF) -> None:
        self._end = value
        self.updatePath()

    def __init__(
        self, nodeEdge: "NodeEdge", parent: QWgt.QGraphicsItem | None = None
    ) -> None:
        super().__init__(parent)
        self._nodeEdge = nodeEdge
        self._start = QPointF(0, 0)
        self._end = QPointF(0, 0)
        self._edgeType = EdgeType.BEZIER
        self._color = self._get_color()
        self._pen = QGui.QPen(self._color)
        self._pen.setWidth(2)

        self.updatePath()

    def update_color(self) -> None:
        self._color = self._get_color()
        self._pen.setColor(self._color)

    def _get_color(self) -> QGui.QColor:
        if self.nodeEdge.outputSocket is not None:
            return self.nodeEdge.outputSocket.grNodeSocket.color
        elif self.nodeEdge.inputSocket is not None:
            return self.nodeEdge.inputSocket.grNodeSocket.color
        return QGui.QColor()

    def toMouse(self, scenePos: QPointF) -> None:
        if self.nodeEdge.inputSocket is None:
            self.end = scenePos
        elif self.nodeEdge.outputSocket is None:
            self.start = scenePos

    def updatePath(self) -> None:
        if self.nodeEdge.inputSocket is None or self.nodeEdge.outputSocket is None:
            self.setZValue(1)
        else:
            self.setZValue(-1)
        if self._edgeType == EdgeType.STRAIGHT:
            path = self.straightPath()
        elif self._edgeType == EdgeType.BEZIER:
            path = self.bezierPath()
        else:
            path = self.straightPath()
        self.setPath(path)

    def straightPath(self) -> QGui.QPainterPath:
        path = QGui.QPainterPath(self.start)
        path.lineTo(self.end)
        return path

    def bezierPath(self) -> QGui.QPainterPath:
        easing = 1.0
        path = QGui.QPainterPath(self.start)
        p_x = (self.end.x() - self.start.x()) * 0.5 * easing

        p1 = QPointF(self.start.x() + p_x, self.start.y())
        p2 = QPointF(self.end.x() - p_x, self.end.y())
        path.cubicTo(p1, p2, self.end)
        return path

    def manhattanPath(self) -> QGui.QPainterPath:
        raise NotImplementedError()

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        painter.setPen(self._pen)
        painter.setBrush(QGui.Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())

        if self.nodeEdge.inputSocket is None or self.nodeEdge.outputSocket is None:
            pathBulbs = QGui.QPainterPath()
            pathBulbs.setFillRule(QGui.Qt.FillRule.WindingFill)
            pathBulbs.addEllipse(self.start, 3.0, 3.0)
            pathBulbs.addEllipse(self.end, 3.0, 3.0)

            painter.setPen(QGui.Qt.PenStyle.NoPen)
            painter.setBrush(QGui.QBrush(self._color))
            painter.drawPath(pathBulbs.simplified())
