from __future__ import annotations
from typing import TYPE_CHECKING, List, Any

import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt
import PySide6.QtCore as QCor
from constants import SlotType

from graphOps import GraphOp, GR_OP_STATUS, registerOp

from graphOps.ops.opMove import OpMove
from nodeGUI import GrNodeSocket, PreviewEdge
from node import NodeEdge

if TYPE_CHECKING:
    from gui import QNodeGraphicsView


MouseButton = QGui.Qt.MouseButton
KeyboardModifier = QGui.Qt.KeyboardModifier


@registerOp
class OpAddEdge(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__([], 1, False)
        self.dragged_edge: PreviewEdge | None = None
        self.stored_edge: NodeEdge | None = None
        self.startPos: QCor.QPointF
        self.dragging = False

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if (
            event.button() == MouseButton.LeftButton
            and event.modifiers() == KeyboardModifier.NoModifier
        ):
            obj = nodeView.itemAt(event.pos())
            # if user pressed a a socket
            if obj is not None and isinstance(obj, GrNodeSocket):
                self.startPos = event.position()
                nodeView.nodeScene.sceneCollection.ntm.startTransaction()
                # get preview edge, and potentially already connected edge in case of input sockets
                self.dragged_edge, self.stored_edge = obj.nodeSocket.getEdge()
                # temp hide connected edge
                if self.stored_edge is not None:
                    nodeView.grScene.removeItem(self.stored_edge.grEdge)
                # look for potential target sockets
                nodeView.nodeScene.activateSockets(
                    self.dragged_edge.socket.nodeSocket,
                    self.dragged_edge.socket.nodeSocket.isCompatible,
                )
                self.dragged_edge.toMouse(nodeView.mapToScene(event.pos()))
                return GR_OP_STATUS.START
        return GR_OP_STATUS.NOTHING

    def findSocket(self, items: List[QWgt.QGraphicsItem]) -> GrNodeSocket | None:
        for ele in items:
            if isinstance(ele, GrNodeSocket):
                return ele
        return None

    # does moving and snapping
    def onMouseMove(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.dragged_edge is not None:
            if not self.dragging:
                if (self.startPos - event.position()).manhattanLength() > 20:
                    self.dragging = True
                    nodeView.grScene.addItem(self.dragged_edge)
            else:
                obj = self.findSocket(nodeView.items(event.pos()))
                pos = nodeView.mapToScene(event.pos())
                if obj is not None and obj.nodeSocket.active:
                    pos = obj.nodeSocket.scenePosition
                self.dragged_edge.toMouse(pos)
        return GR_OP_STATUS.NOTHING

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.dragged_edge is None:
            return GR_OP_STATUS.NOTHING

        if self.stored_edge is not None:
            nodeView.grScene.addItem(self.stored_edge.grEdge)

        if not self.dragging:
            nodeView.nodeScene.sceneCollection.ntm.abortTransaction()
            self.stored_edge = None
            self.cleanupOp(nodeView)
            return GR_OP_STATUS.FINISH

        obj = self.findSocket(nodeView.items(event.pos()))
        if obj is not None and obj.nodeSocket.active:
            # we had an existing edge
            if self.stored_edge is not None:
                # nothing changed, abort
                if self.stored_edge.inputSocket == obj.nodeSocket:
                    nodeView.nodeScene.sceneCollection.ntm.abortTransaction()
                # existing edge has new target
                else:
                    self.stored_edge.remove()
                    edge = NodeEdge(
                        nodeView.nodeScene,
                        self.dragged_edge.socket.nodeSocket,
                        obj.nodeSocket,
                    )
                    edge.updateConnections()
                    nodeView.nodeScene.sceneCollection.ntm.finalizeTransaction()
                self.stored_edge = None
            # no existing edge, create new edge
            else:
                # in case either of the sockets is in or output socket, put them in the correct spot
                outputSocket = (
                    obj.nodeSocket
                    if obj.nodeSocket.nodeSlot.slotType == SlotType.OUTPUT
                    or self.dragged_edge.socket.nodeSocket.nodeSlot.slotType
                    == SlotType.INPUT
                    else self.dragged_edge.socket.nodeSocket
                )
                inputSocket = (
                    self.dragged_edge.socket.nodeSocket
                    if outputSocket == obj.nodeSocket
                    else obj.nodeSocket
                )

                edge = NodeEdge(nodeView.nodeScene, outputSocket, inputSocket)
                edge.updateConnections()
                nodeView.nodeScene.sceneCollection.ntm.finalizeTransaction()
            self.cleanupOp(nodeView)
            return GR_OP_STATUS.NOTHING
        # no valid target found, prompt node creation

        if self.stored_edge is not None:
            # don't set it to none just yet, we need to know if it existed
            self.stored_edge.remove()
        self.showSearchMenu(nodeView)

        return GR_OP_STATUS.NOTHING

    def cleanupOp(self, nodeView: QNodeGraphicsView) -> None:
        assert self.dragged_edge is not None
        if self.dragging:
            nodeView.grScene.removeItem(self.dragged_edge)
            self.dragging = False
        self.stored_edge = None
        self.dragged_edge = None
        nodeView.nodeScene.deactivateSockets()
        self.releaseView(nodeView)

    def showSearchMenu(self, nodeView: QNodeGraphicsView) -> None:
        assert self.dragged_edge is not None
        factory = nodeView.nodeScene.sceneCollection.nodeFactory
        searchMenu = factory.getDetailedSearch()
        slotype = self.dragged_edge.socket.nodeSocket.nodeSlot.slotType
        typeName = self.dragged_edge.socket.nodeSocket.socketType
        searchMenu.setFilter(
            lambda x, y: x.match(y)
            and x.slotType != slotype
            and x.socketType == typeName
        )

        def searchFinish(ind: int) -> None:
            assert self.dragged_edge is not None
            info: Any = searchMenu.items[ind]
            nodeName: str = info.className
            slotName: str = info.slotName
            slotInd: int = info.slotInd

            node = factory.loadNode(nodeName)
            selected = nodeView.getSelected()
            for item in selected:
                item.setSelected(False)
            node.grNode.setSelected(True)
            node.grNode.setPos(
                nodeView.mapToScene(nodeView.mapFromGlobal(QGui.QCursor.pos()))
            )
            if slotype == SlotType.INPUT:
                socket = node.outputs[slotInd].socket
                edge = NodeEdge(
                    nodeView.nodeScene, socket, self.dragged_edge.socket.nodeSocket
                )
            else:
                socket = [x for x in node.inputs if x.name == slotName][0].socket
                edge = NodeEdge(
                    nodeView.nodeScene, self.dragged_edge.socket.nodeSocket, socket
                )

            edge.updateConnections()

            cleanup()

            for op in nodeView._graphOps:
                if isinstance(op, OpMove):
                    op.ProcessAction(nodeView)
            nodeView.nodeScene.sceneCollection.ntm.finalizeTransaction()

        def searchAbort() -> None:
            if self.stored_edge is not None:
                # if we had a stored edge, finalize its deletion, otherwise abort
                self.stored_edge = None
                nodeView.nodeScene.sceneCollection.ntm.finalizeTransaction()
            else:
                nodeView.nodeScene.sceneCollection.ntm.abortTransaction()
            cleanup()

        def cleanup() -> None:
            assert self.dragged_edge is not None
            searchMenu.abort.disconnect(searchAbort)
            searchMenu.finished.disconnect(searchFinish)
            self.cleanupOp(nodeView)

        searchMenu.abort.connect(searchAbort)
        searchMenu.finished.connect(searchFinish)
        searchMenu.move(QGui.QCursor.pos() + QCor.QPoint(5, -5))
        searchMenu.show()
