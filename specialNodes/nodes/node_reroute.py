from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple, TYPE_CHECKING, cast
from customWidgets.elidedGraphicsItem import QGraphicsElidedTextItem
from node.socket import SocketTyping
from nodeGUI.edge import PreviewEdge
from server import ComfyPromptManager, NodeAddress, NodeResult, PartialPrompt

from nodeGUI import GrNodeSocket

if TYPE_CHECKING:
    from node.factory import ComfyFactory

from PySide6.QtWidgets import QGraphicsItem

from constants import SLOT_MIN_HEIGHT, SOCKET_RADIUS, ConnectionChangedType, SocketShape
from customWidgets.QSlotContentGraphicsItem import QSlotContentGraphicsItem

from nodeGUI import BaseGrNode
from constants import SlotType
from node import Node, NodeEdge, NodeSocket, NodeScene
from nodeSlots.nodeSlot import NodeSlot

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt

from specialNodes.customNode import CustomNode, registerCustomNode
from style.socketStyle import SocketPainter


@registerCustomNode
class RerouteNode(Node, CustomNode):
    def __init__(self, nodeScene: NodeScene, socketPainter: SocketPainter) -> None:
        super().__init__(nodeScene, "Reroute", False, "", "")
        self.rerouteSlot = RerouteSlot(self, socketPainter)
        self.rerouteSlot.socket.grNodeSocket.setParentItem(self.grNode)
        self.rerouteSlot.socket.grNodeSocket.setPos(
            -SLOT_MIN_HEIGHT / 2, -SLOT_MIN_HEIGHT / 2
        )

    @property
    def inputs(self) -> List[NodeSlot]:
        return [self.rerouteSlot]

    @property
    def outputs(self) -> List[NodeSlot]:
        return [self.rerouteSlot]

    @classmethod
    def getCategory(cls) -> str | None:
        return "Layout"

    @classmethod
    def getClassName(cls) -> str:
        return "Reroute"

    @classmethod
    def getDisplayName(cls) -> str:
        return "Reroute Node"

    @classmethod
    def createNode(cls, factory: ComfyFactory, nodeDef: Any) -> Node:
        painter = factory.socketStyles.getSocketPainter("reroute", "reroute", False)
        assert factory.activeScene is not None
        return cls(factory.activeScene, painter)

    def createGUI(self) -> "GrRerouteNode":
        return GrRerouteNode(self)

    def travelFrom(self, slotType: SlotType) -> List[NodeSlot]:
        return [self.rerouteSlot]

    def activateSockets(
        self, socket: NodeSocket, check: Callable[[NodeSocket], bool]
    ) -> None:
        self.rerouteSlot.socket.activateSocket(check)

    def deactivateSockets(self) -> None:
        self.rerouteSlot.socket.deactivateSocket()

    def remove(self) -> None:
        self.rerouteSlot.socket.remove()
        super().remove()

    def saveState(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        state["position"] = self.grNode.pos().toTuple()
        state["nodeClass"] = self.nodeClass
        state["title"] = self.title
        return state

    def loadState(self, state: Dict[str, Any]) -> None:
        self.grNode.setPos(QCor.QPointF(*state["position"]))
        if "title" in state:
            self.setTitle(state["title"])

    def execute(
        self, promptManager: ComfyPromptManager
    ) -> Tuple[PartialPrompt, Dict[int, NodeAddress | NodeResult]] | None:
        cashed = self.getCashedExecute(promptManager)
        if cashed is not None:
            return cashed
        rerouteSlotResult = self.rerouteSlot.execute(promptManager)
        if rerouteSlotResult is None:
            return None
        return (PartialPrompt.empty(), {0: rerouteSlotResult})


# responsible for selection outline
class GrRerouteNode(BaseGrNode):
    def __init__(self, node: RerouteNode, parent: QGraphicsItem | None = None) -> None:
        super().__init__(node, parent)
        self._outlinePath = QGui.QPainterPath()
        # centerPoint = QPointF(SLOT_MIN_HEIGHT/2,SLOT_MIN_HEIGHT/2)
        self._outlinePath.addPolygon(
            [
                QCor.QPointF(0, SOCKET_RADIUS),
                QCor.QPointF(SOCKET_RADIUS, 0),
                QCor.QPointF(0, -SOCKET_RADIUS),
                QCor.QPointF(-SOCKET_RADIUS, 0),
                QCor.QPointF(0, SOCKET_RADIUS),
            ]
        )
        self.initUI()
        self.initTitle()

    def initTitle(self) -> None:
        self.title_label = QGraphicsElidedTextItem(
            self.node.title,
            200,
            20,
            parent=self,
        )
        self.title_label.setAlignedPos(-self.title_label.textWidth / 2, -30)

    def changeTitle(self, title: str) -> None:
        self.title_label.rawText = title
        self.title_label.setAlignedPos(-self.title_label.textWidth / 2, -30)

    def initUI(self) -> None:
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def boundingRect(self) -> QCor.QRectF:
        return QCor.QRectF(
            -SLOT_MIN_HEIGHT / 2, -SLOT_MIN_HEIGHT / 2, SLOT_MIN_HEIGHT, SLOT_MIN_HEIGHT
        ).normalized()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            assert isinstance(self.node, RerouteNode)
            self.node.rerouteSlot.socket.updateEdges()
        return value

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        # outline
        if self.isSelected():
            painter.setPen(self._pen_selected)
            painter.setBrush(QGui.Qt.BrushStyle.NoBrush)
            painter.drawPath(self._outlinePath)


class RerouteSlot(NodeSlot):
    def __init__(self, node: Node, socketPainter: SocketPainter):
        super().__init__(
            node,
            None,
            "Reroute",
            0,
            SocketTyping(),
            socketPainter,
            SlotType.BI,
        )

    def createGUI(self) -> None:  # type: ignore
        return None

    def createSocket(
        self, socketTyping: SocketTyping, socketPainter: SocketPainter
    ) -> "RerouteSocket":
        return RerouteSocket(self, socketPainter)

    def initContent(self, height: float) -> None:
        return None
    
    @property
    def isOutput(self) -> bool:
        return cast(RerouteSocket, self.socket).outputConnection is not None

    def execute(
        self, promptManager: ComfyPromptManager
    ) -> NodeAddress | NodeResult | None:
        socket = cast(RerouteSocket, self.socket)
        if socket.outputConnection is None:
            raise ValueError("slot content can not be None")
        target = socket.outputConnection.outputSocket
        assert target is not None
        if target.nodeSlot.node not in promptManager.idMap:
            promptManager.executeNode(target.nodeSlot.node)
            return None
        id = promptManager.idMap[target.nodeSlot.node]
        return promptManager.outputMap[id][target.nodeSlot.ind]

#TODO: can probably refactor get rid of this?
class ConInfo:
    '''container for the edge and oposite socket'''
    def __init__(self, edge: NodeEdge, socket: NodeSocket | None) -> None:
        self.edge = edge
        self.socket = socket


# holds type info
class RerouteSocket(NodeSocket):
    @property
    def outputConnection(self) -> NodeEdge | None:
        return self._outputConnection

    @outputConnection.setter
    def outputConnection(self, value: NodeEdge | None) -> None:
        current = self.outputConnection
        self.ntm.doStep(
            lambda: self._setOutputConnection(value),
            lambda: self._setOutputConnection(current),
        )

    def __init__(self, nodeSlot: NodeSlot, socketPainter: SocketPainter) -> None:
        super().__init__(nodeSlot, SocketTyping(), socketPainter)
        self._outputConnection: NodeEdge | None = None
        self.rerouteConnections: List[ConInfo] = []
        self.typeSources: List[NodeEdge] = []

    def createGUI(self, socketPainter: SocketPainter) -> GrNodeSocket:
        return GrRerouteSocket(self, socketPainter)

    def _setOutputConnection(self, value: NodeEdge | None) -> None:
        self._outputConnection = value

        # update edge colors
        socketSelf = cast(GrRerouteSocket, self.grNodeSocket)
        if value is None:
            socketSelf.setEdgeColor(None)
        else:
            socket = value.travelFrom(self)
            if socket is not None:
                if isinstance(socket, GrRerouteNode):
                    col = cast(GrRerouteSocket, socket).getEdgeColor()
                else:
                    col = socket.grNodeSocket.color
                socketSelf.setEdgeColor(col)
        for e in self.rerouteConnections:
            e.edge.grEdge.update_color()

    def addTypeSource(self, edge: NodeEdge) -> None:
        self.ntm.doStep(
            lambda: self.typeSources.append(edge), lambda: self.typeSources.remove(edge)
        )

    def removeTypeSource(self, edge: NodeEdge) -> None:
        self.ntm.doStep(
            lambda: self.typeSources.remove(edge), lambda: self.typeSources.append(edge)
        )

    def createConInfo(self, edge: NodeEdge) -> ConInfo:
        info = ConInfo(edge, None)
        self.ntm.doStep(
            lambda: self.rerouteConnections.append(info),
            lambda: self.rerouteConnections.remove(info),
        )
        return info

    def removeConInfo(self, edge: NodeEdge) -> ConInfo | None:
        ind = -1
        for i, ele in enumerate(self.rerouteConnections):
            if ele.edge == edge:
                ind = i
        if ind == -1:
            return None
        info = self.rerouteConnections[ind]
        self.ntm.doStep(
            lambda: self.rerouteConnections.remove(info),
            lambda: self.rerouteConnections.append(info),
        )
        return info

    def setInfoSocket(self, info: ConInfo, value: NodeSocket) -> None:
        current = info.socket
        self.ntm.doStep(
            lambda: self._setInfoSocket(info, value),
            lambda: self._setInfoSocket(info, current),
        )

    def _setInfoSocket(self, info: ConInfo, value: NodeSocket | None) -> None:
        info.socket = value

    def getConnectedForDeactivation(self) -> List[Node]:
        nodes = []
        if self.outputConnection is None:
            for con in self.rerouteConnections:
                socket = con.edge.travelFrom(self)
                if (
                    socket is not None
                    and socket.active
                    and isinstance(socket, RerouteSocket)
                ):
                    nodes.append(socket.nodeSlot.node)
        elif self.outputConnection is not None:
            nodes.append(self.outputConnection.outputSocket.nodeSlot.node)
        return nodes

    def resolveConnected(self, origin: SlotType) -> List[NodeSocket]:
        if self.outputConnection is None:
            return []
        if origin == SlotType.INPUT:
            return self.outputConnection.travelFrom(self).resolveConnected(origin)
        sockets: List[NodeSocket] = []
        for con in self.rerouteConnections:
            if con.edge is not self.outputConnection:
                sockets.extend(con.edge.travelFrom(self).resolveConnected(origin))
        return sockets

    def triggerConnectionChange(
        self, edge: NodeEdge | None, cType: ConnectionChangedType
    ) -> None:
        if self.outputConnection is not None:
            # If we're directional, simply figure out which way to send event
            if edge == self.outputConnection:
                for con in self.rerouteConnections:
                    if con.edge is not edge:
                        con.edge.travelFrom(self).triggerConnectionChange(
                            con.edge, cType
                        )
            else:
                self.outputConnection.travelFrom(self).triggerConnectionChange(
                    self.outputConnection, cType
                )
            return
        # If we're not directional, find out if we used to be
        if cType != ConnectionChangedType.REMOVED or edge is None:
            return
        target = edge.travelFrom(self)
        if (isinstance(target, RerouteSocket) and target.outputConnection is None) or (
            not isinstance(target, RerouteSocket)
            and target.nodeSlot.slotType == SlotType.INPUT
        ):
            # target is either an input socket or an undirected reroute, edge wasn't an output connection
            # we weren't directional
            return
        # edge used to be our output connection, send things forwards
        for con in self.rerouteConnections:
            con.edge.travelFrom(self).triggerConnectionChange(con.edge, cType)

    def getEdge(self) -> Tuple[PreviewEdge, NodeEdge | None]:
        return (PreviewEdge(self.grNodeSocket), None)

    def propagateTypeChange(self, origin: NodeEdge, add: bool) -> None:
        if add:
            if len(self.typeSources) == 0:
                opposite = origin.travelFrom(self)
                assert opposite is not None
                self.socketType = opposite.socketType
            self.addTypeSource(origin)
        else:
            self.removeTypeSource(origin)
            if len(self.typeSources) == 0:
                self.socketType = SocketTyping()
        for ele in self.rerouteConnections:
            if isinstance(ele.socket, RerouteSocket) and ele.edge != origin:
                ele.socket.propagateTypeChange(ele.edge, add)

    def _propagateOutputConnectionChange(self, origin: NodeEdge, add: bool) -> None:
        for ele in self.rerouteConnections:
            if isinstance(ele.socket, RerouteSocket) and ele.edge != origin:
                if add and ele.edge.inputSocket != ele.socket:
                    ele.edge.swap()
                ele.socket.propagateOutputConnectionChange(ele.edge, add)

    def propagateOutputConnectionChange(self, origin: NodeEdge, add: bool) -> None:
        if add:
            self.outputConnection = origin
        else:
            self.outputConnection = None
        self._propagateOutputConnectionChange(origin, add)

    def _getOutputSocket(self, socket: NodeSocket) -> NodeSocket | None:
        '''simply returns the socket if it is an output socket, the socket pointing towards the output if it is a directional reroute socket, or None'''
        if socket.nodeSlot.slotType == SlotType.OUTPUT:
            return socket
        if (
            socket.nodeSlot.slotType == SlotType.BI
            and isinstance(socket, RerouteSocket)
            and socket.outputConnection is not None
        ):
            return socket.outputConnection.travelFrom(socket)
        return None

    def addEdge(self, edge: NodeEdge) -> None:
        '''adds an edge to the socket'''
        opposite = edge.travelFrom(self)

        rerouteConnection = self.createConInfo(edge)
        
        # get rid of potential duplicate
        dupe = [x for x in self.rerouteConnections if x.socket == opposite and x.edge != edge]
        for d in dupe:
            d.edge.remove()

        outputSocket = None #remains None if we are not connected to an output socket somewhere
        if opposite.nodeSlot.slotType == SlotType.OUTPUT: # set it to the oposite socket if that is an output socket
            outputSocket = opposite
        elif (
            opposite.nodeSlot.slotType == SlotType.BI 
            and isinstance(opposite, RerouteSocket)
            and opposite.outputConnection is not None
        ):
            # if it is a reroute socket set it to the output socket of the output connection of the reroute (may or may not be self)
            outputSocket = opposite.outputConnection.travelFrom(opposite)

        # if not None we are directional
        if outputSocket is not None:
            # remove previous directional info if it existed
            if self.outputConnection is not None:
                self.outputConnection.remove()
            self.outputConnection = edge
            #swap edge if the direction is wrong (we're currently in the input spot, but are the output socket)
            if edge.inputSocket == self and outputSocket == self:
                edge.swap()
            self._propagateOutputConnectionChange(edge, True)
        
        if len(opposite.socketType.types) > 0:
            self.propagateTypeChange(edge, True)

        rerouteConnection.socket = opposite

    def removeEdge(self, edge: NodeEdge) -> None:
        rerouteConnection = self.removeConInfo(edge)

        if self.outputConnection == edge:
            self.outputConnection = None
            self._propagateOutputConnectionChange(edge, False)
        if edge in self.typeSources:
            self.propagateTypeChange(edge, False)

    def remove(self) -> None:
        self.outputConnection = None
        connections = self.rerouteConnections.copy()
        for con in connections:
            con.edge.remove()

    def updateEdges(self) -> None:
        for con in self.rerouteConnections:
            if con.edge.inputSocket == self:
                con.edge.grEdge.end = self.grNodeSocket.centerPos()
            else:
                con.edge.grEdge.start = self.grNodeSocket.centerPos()


class GrRerouteSocket(GrNodeSocket):
    def __init__(
        self,
        nodeSocket: NodeSocket,
        socketPainter: SocketPainter,
        parent: QGraphicsItem | None = None,
    ) -> None:
        super().__init__(nodeSocket, socketPainter, parent)
        self._reroute_color: QGui.QColor | None = None

    def setEdgeColor(self, QColor: QGui.QColor | None) -> None:
        self._reroute_color = QColor

    def getEdgeColor(self) -> QGui.QColor | None:
        return self._reroute_color

    @property
    def color(self) -> QGui.QColor:
        if self._reroute_color is None:
            return super().color
        return self._reroute_color
