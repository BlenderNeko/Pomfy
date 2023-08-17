from __future__ import annotations
from typing import TYPE_CHECKING, List

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from graphOps import GraphOp, GR_OP_STATUS, registerOp
from node.edge import NodeEdge
from nodeGUI import BaseGrNode

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView

MouseButton = QGui.Qt.MouseButton
KeyboardModifier = QGui.Qt.KeyboardModifier


class QStraightLine(QWgt.QGraphicsPathItem):
    """GraphicsItem class for drawing a line on the scene at a given `resolution`"""

    def __init__(
        self,
        start: QCor.QPointF,
        color: QGui.QColor,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self.start: QCor.QPointF = start
        self._brush = QGui.QBrush(color)
        self._pen = QGui.QPen(color)
        self._pen.setWidth(4)
        self.updatePath(self.start)

    def updatePath(self, end: QCor.QPointF) -> None:
        path = QGui.QPainterPath(self.start)
        self.end = end
        path.lineTo(self.end)
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

        pathBulbs = QGui.QPainterPath()
        pathBulbs.addEllipse(self.start, 6.0, 6.0)
        pathBulbs.addEllipse(self.end, 6.0, 6.0)

        painter.setPen(QGui.Qt.PenStyle.NoPen)
        painter.setBrush(self._brush)
        painter.drawPath(pathBulbs.simplified())


@registerOp
class OpSmartConnect(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__([], 1, False)
        self.line: QStraightLine | None = None
        self.startNode: BaseGrNode | None = None

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if (
            event.button() == MouseButton.RightButton
            and event.modifiers() == KeyboardModifier.AltModifier
        ):
            obj = nodeView.itemAt(event.pos())
            while obj is not None and not isinstance(obj, BaseGrNode):
                obj = obj.parentItem()
            if obj is not None:
                self.startNode = obj
                self.line = QStraightLine(
                    nodeView.mapToScene(event.pos()), QGui.QColor("#999999")
                )

                nodeView.nodeScene.grScene.addItem(self.line)
                return GR_OP_STATUS.START | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.NOTHING

    def onMouseMove(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.line is not None:
            self.line.updatePath(nodeView.mapToScene(event.pos()))
        return GR_OP_STATUS.NOTHING

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if (
            event.button() == MouseButton.RightButton
            and self.line is not None
            and self.startNode is not None
        ):
            objs_at = nodeView.items(event.pos())
            objs = [x for x in objs_at if isinstance(x, BaseGrNode)]
            obj = objs[0] if len(objs) > 0 else None
            if obj is not None:
                swap = self.line.start.x() > self.line.end.x()
                startNode = obj if swap else self.startNode
                endNode = obj if not swap else self.startNode
                for startSlot in startNode.node.outputs:
                    nodeView.nodeScene.activateSockets(
                        startSlot.socket, startSlot.socket.isCompatible
                    )
                    for endSlot in endNode.node.inputs:
                        if endSlot.socket.active and len(endSlot.socket.edges) == 0:
                            with nodeView.nodeScene.sceneCollection.ntm:
                                edge = NodeEdge(
                                    nodeView.nodeScene,
                                    startSlot.socket,
                                    endSlot.socket,
                                )
                            edge.updateConnections()
                            nodeView.nodeScene.deactivateSockets()
                            self.startNode = None
                            nodeView.nodeScene.grScene.removeItem(self.line)
                            self.line = None
                            return GR_OP_STATUS.FINISH | GR_OP_STATUS.BLOCK
            self.startNode = None
            nodeView.nodeScene.grScene.removeItem(self.line)
            self.line = None
            return GR_OP_STATUS.FINISH | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.FINISH
