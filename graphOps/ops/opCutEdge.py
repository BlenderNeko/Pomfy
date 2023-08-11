from __future__ import annotations
from typing import TYPE_CHECKING, List

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from graphOps import GraphOp, GR_OP_STATUS, registerOp
from nodeGUI import GrNodeEdge

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView

MouseButton = QGui.Qt.MouseButton
KeyboardModifier = QGui.Qt.KeyboardModifier


class QLineDrawingItem(QWgt.QGraphicsPathItem):
    """GraphicsItem class for drawing a line on the scene at a given `resolution`"""

    def __init__(
        self,
        start: QCor.QPointF,
        color: QGui.QColor,
        resolution: float = 20,
        dashed: bool = False,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self.points: List[QCor.QPointF] = [start, QCor.QPointF(start)]
        self._pen = QGui.QPen(color)
        self._pen.setWidth(2)
        self._resolution = resolution
        if dashed:
            self._pen.setDashPattern([3, 3])
        self.updatePath()

    def drawPoint(self, point: QCor.QPointF) -> bool:
        """Extends line, Returns `True` when a new point on the line is introduced, and `False` when the last point was extended"""
        self.points[-1] = point
        if (self.points[-1] - self.points[-2]).manhattanLength() > self._resolution:
            self.points.append(QCor.QPointF(point))
            self.updatePath()
            return True
        self.updatePath()
        return False

    def updatePath(self) -> None:
        path = QGui.QPainterPath()
        path.addPolygon(self.points)
        self.setPath(path)

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        painter.setPen(self._pen)
        painter.setBrush(QGui.Qt.BrushStyle.NoBrush)
        painter.drawPath(self.path())


@registerOp
class OpCutEdge(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__([], 1, False)
        self.line: QLineDrawingItem | None = None

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if (
            event.button() == MouseButton.RightButton
            and event.modifiers() == KeyboardModifier.ControlModifier
        ):
            self.line = QLineDrawingItem(
                nodeView.mapToScene(event.pos()), QGui.QColor("#999999"), dashed=True
            )

            nodeView.nodeScene.grScene.addItem(self.line)
            return GR_OP_STATUS.START | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.NOTHING

    def onMouseMove(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.line is not None:
            self.line.drawPoint(nodeView.mapToScene(event.pos()))
        return GR_OP_STATUS.NOTHING

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if event.button() == MouseButton.RightButton and self.line is not None:
            items: List[GrNodeEdge] = [
                x for x in self.line.collidingItems() if isinstance(x, GrNodeEdge)
            ]
            with nodeView.nodeScene.sceneCollection.ntm:
                for i in items:
                    i.nodeEdge.remove()
            nodeView.nodeScene.grScene.removeItem(self.line)
            self.line = None
            return GR_OP_STATUS.FINISH | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.FINISH
