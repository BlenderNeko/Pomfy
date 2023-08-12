from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Tuple, Any, cast

import PySide6.QtCore as QCore
import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt

from graphOps import GraphOp, GR_OP_STATUS, registerOp
from graphOps.ops.opCutEdge import QLineDrawingItem
from node import NodeEdge, NodeSocket
from specialNodes.nodes.node_reroute import RerouteNode, RerouteSocket
from nodeGUI import GrNodeEdge

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView


class CollisionSquare(QWgt.QGraphicsItem):
    def __init__(self, size: float, parent: QWgt.QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.size = size

    def boundingRect(self) -> QCore.QRectF:
        return QCore.QRectF(-self.size, -self.size, 2 * self.size, 2 * self.size)

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        pass


@registerOp
class OpInsertReroute(GraphOp):
    def __init__(self) -> None:
        super().__init__([], 1, False)
        self.line: QLineDrawingItem | None = None
        self.square: CollisionSquare | None = None
        self.intersectionCandidates: Dict[NodeEdge, List[Tuple[int, float, float]]] = {}

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if (
            event.button() == QGui.Qt.MouseButton.RightButton
            and event.modifiers() == QGui.Qt.KeyboardModifier.ShiftModifier
        ):
            self.line = QLineDrawingItem(
                nodeView.mapToScene(event.pos()),
                QGui.QColor("#999999"),
                resolution=20,
                dashed=False,
            )
            nodeView.nodeScene.grScene.addItem(self.line)
            self.intersectionCandidates = {}
            return GR_OP_STATUS.START | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.NOTHING

    def addEdges(self, step: int, edges: List[NodeEdge], x: float, y: float) -> None:
        for edge in edges:
            if edge not in self.intersectionCandidates:
                self.intersectionCandidates[edge] = []
            self.intersectionCandidates[edge].append((step, x, y))

    def onMouseMove(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.line is not None:
            self.line.drawPoint(nodeView.mapToScene(event.pos()))
        return GR_OP_STATUS.NOTHING

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if event.button() == QGui.Qt.MouseButton.RightButton and self.line is not None:
            self.square = CollisionSquare(5)
            nodeView.nodeScene.grScene.addItem(self.square)
            length = 0.0
            step = 0
            linePath = self.line.path()
            totalLength = linePath.length()
            while length < totalLength:
                pos = linePath.pointAtPercent(linePath.percentAtLength(length))
                self.square.setPos(pos)
                items: List[NodeEdge] = [
                    x.nodeEdge
                    for x in self.square.collidingItems()
                    if isinstance(x, GrNodeEdge)
                ]
                self.addEdges(step, items, pos.x(), pos.y())
                length += self.square.size - 1
                step += 1
            self.processIntersections(nodeView)
            self.intersectionCandidates = {}
            nodeView.nodeScene.grScene.removeItem(self.line)
            nodeView.nodeScene.grScene.removeItem(self.square)
            self.line = None
            self.square = None
            return GR_OP_STATUS.FINISH | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.FINISH

    def processIntersections(self, nodeView: QNodeGraphicsView) -> None:
        intersections: Dict[NodeEdge, Tuple[float, float]] = {}
        # get mean of intersection points happening close together in time
        for edge, points in self.intersectionCandidates.items():
            current = [(points[0][1], points[0][2])]
            for p1, p2 in zip(points, points[1:]):
                if p2[0] - p1[0] > 2:
                    break
                current.append((p2[1], p2[2]))
            x = sum([p[0] for p in current]) / len(current)
            y = sum([p[1] for p in current]) / len(current)
            intersections[edge] = (x, y)

        grouping: Dict[NodeSocket, Any] = {}
        remaining: List[Tuple[NodeEdge, Tuple[float, float]]] = []
        # merge intersections coming from the same output socket
        for edge, point in intersections.items():
            # don't do anything smart for un-directional reroute edges
            if (
                isinstance(edge.inputSocket, RerouteSocket)
                and isinstance(edge.outputSocket, RerouteSocket)
                and edge.inputSocket.outputConnection is None
            ):
                remaining.append((edge, point))
            else:
                # directional
                if edge.outputSocket not in grouping:
                    grouping[edge.outputSocket] = [[], []]
                grouping[edge.outputSocket][0].append(edge)
                grouping[edge.outputSocket][1].append(point)
        # deselect everything so we can select the reroutes after creation
        for ele in nodeView.getSelected():
            ele.setSelected(False)
        with nodeView.nodeScene.sceneCollection.ntm:
            for edge, point in remaining:
                reroute: RerouteNode = cast(
                    RerouteNode,
                    nodeView.nodeScene.sceneCollection.nodeFactory.loadNode("Reroute"),
                )
                reroute.grNode.setPos(QCore.QPointF(point[0], point[1]))
                reroute.grNode.setSelected(True)

                inputSocket = edge.inputSocket
                outputSocket = edge.outputSocket
                edge.remove()

                NodeEdge(nodeView.nodeScene, outputSocket, reroute.rerouteSlot.socket)
                NodeEdge(nodeView.nodeScene, reroute.rerouteSlot.socket, inputSocket)
                inputSocket.updateEdges()
                outputSocket.updateEdges()
                reroute.rerouteSlot.socket.updateEdges()

            for outputSocket, values in grouping.items():
                edges: List[NodeEdge] = values[0]
                points = values[1]
                x = sum([p[0] for p in points]) / len(points)
                y = sum([p[1] for p in points]) / len(points)

                reroute = cast(
                    RerouteNode,
                    nodeView.nodeScene.sceneCollection.nodeFactory.loadNode("Reroute"),
                )
                reroute.grNode.setPos(QCore.QPointF(x, y))
                reroute.grNode.setSelected(True)

                for edge in edges:
                    inputSocket = edge.inputSocket
                    edge.remove()
                    NodeEdge(
                        nodeView.nodeScene, outputSocket, reroute.rerouteSlot.socket
                    )
                    NodeEdge(
                        nodeView.nodeScene, reroute.rerouteSlot.socket, inputSocket
                    )
                    inputSocket.updateEdges()

                reroute.rerouteSlot.socket.updateEdges()
                outputSocket.updateEdges()
