from __future__ import annotations
from typing import TYPE_CHECKING, List

import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt
from constants import SlotType

from graphOps import GraphOp, GR_OP_STATUS, registerOp
from nodeGUI import GrNodeSocket

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView
    from node import NodeEdge

MouseButton = QGui.Qt.MouseButton
KeyboardModifier = QGui.Qt.KeyboardModifier


@registerOp
class OpAddEdge(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__([], 1, False)
        self.dragged_edge: NodeEdge | None = None
        self.stored_socket: GrNodeSocket | None = None

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if (
            event.button() == MouseButton.LeftButton
            and event.modifiers() == KeyboardModifier.NoModifier
        ):
            obj = nodeView.itemAt(event.pos())
            if obj is not None and isinstance(obj, GrNodeSocket):
                if obj.nodeSocket.nodeSlot.slotType == SlotType.INPUT:
                    self.stored_socket = obj
                nodeView.nodeScene.sceneCollection.ntm.startTransaction()
                self.dragged_edge = obj.nodeSocket.getEdge()
                assert (
                    self.dragged_edge is not None
                    and self.dragged_edge.nonEmpty is not None
                )
                nodeView.nodeScene.activateSockets(
                    self.dragged_edge.nonEmpty, self.dragged_edge.canConnect
                )
                self.dragged_edge.grEdge.toMouse(nodeView.mapToScene(event.pos()))
                return GR_OP_STATUS.START
        return GR_OP_STATUS.NOTHING

    def findSocket(self, items: List[QWgt.QGraphicsItem]) -> GrNodeSocket | None:
        for ele in items:
            if isinstance(ele, GrNodeSocket):
                return ele
        return None

    def onMouseMove(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.dragged_edge is not None:
            obj = self.findSocket(nodeView.items(event.pos()))
            pos = nodeView.mapToScene(event.pos())
            if obj is not None and obj.nodeSocket.active:
                pos = obj.nodeSocket.scenePosition
            self.dragged_edge.grEdge.toMouse(pos)
        return GR_OP_STATUS.NOTHING

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.dragged_edge is None:
            return GR_OP_STATUS.NOTHING

        obj = self.findSocket(nodeView.items(event.pos()))
        if obj is not None and obj.nodeSocket.active:
            self.dragged_edge.connect(obj.nodeSocket)
            assert self.dragged_edge.inputSocket is not None
            if self.dragged_edge.inputSocket.grNodeSocket == self.stored_socket:
                nodeView.nodeScene.sceneCollection.ntm.abortTransaction()
            else:
                nodeView.nodeScene.sceneCollection.ntm.finalizeTransaction()
        else:
            if self.stored_socket is not None and self.dragged_edge.inputSocket is None:
                self.dragged_edge.remove()
                nodeView.nodeScene.sceneCollection.ntm.finalizeTransaction()
            else:
                self.dragged_edge.remove()
                nodeView.nodeScene.sceneCollection.ntm.abortTransaction()
        self.dragged_edge = None
        self.stored_socket = None
        nodeView.nodeScene.deactivateSockets()
        return GR_OP_STATUS.FINISH
