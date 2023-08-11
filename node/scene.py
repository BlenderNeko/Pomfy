from __future__ import annotations
from typing import TYPE_CHECKING, Callable, List, Set, Dict, Any

from node import NodeEdge

if TYPE_CHECKING:
    from node import Node, NodeSocket, SceneCollection
    from node.factory import ComfyFactory

from nodeGUI import QNodeGraphicsScene


class NodeScene:
    def __init__(self, sceneCollection: SceneCollection):
        self.nodes: List[Node] = []
        self.edges: List[NodeEdge] = []
        self.nodeIds: Dict[str, List[int]] = {}

        self.sceneCollection = sceneCollection

        self.scene_width = 64000
        self.scene_height = 64000

        self.initUI()

    def initUI(self) -> None:
        self.grScene = QNodeGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scene_height)

    def registerNode(self, node: Node) -> None:
        if node.nodeClass not in self.nodeIds:
            self.nodeIds[node.nodeClass] = [0]
            node.nodeID = 0
            return
        ids = self.nodeIds[node.nodeClass]
        for i, id in enumerate(ids):
            if i != id:
                node.nodeID = i
                ids.insert(i, i)
                return
        id = len(ids)
        node.nodeID = id
        ids.append(id)

    def deregisterNode(self, node: Node) -> None:
        self.nodeIds[node.nodeClass].remove(node.nodeID)

    def undo(self) -> None:
        self.sceneCollection.undoStack.undo()

    def redo(self) -> None:
        self.sceneCollection.undoStack.redo()

    # TODO: write functions to do graph traversal?
    def activateSockets(
        self, socket: NodeSocket, check: Callable[[NodeSocket], bool]
    ) -> None:
        for n in self.nodes:
            n.activateSockets(socket, check)
        # deactivate sockets that cause loops
        visited: Set[Node] = set()
        remaining: Set[Node] = set()
        remaining.add(socket.nodeSlot.node)

        while len(remaining) > 0:
            current = remaining.pop()
            current.deactivateSockets()
            visited.add(current)
            slots = []

            slots = current.travelFrom(socket.nodeSlot.slotType)
            for slot in slots:
                for n in slot.socket.getConnectedForDeactivation():
                    if n not in visited:
                        remaining.add(n)

    def deactivateSockets(self) -> None:
        for n in self.nodes:
            n.deactivateSockets()

    def addNode(self, node: Node) -> None:
        self.sceneCollection.ntm.doStep(
            lambda: self._addNode(node), lambda: self._removeNode(node)
        )

    def _addNode(self, node: Node) -> None:
        self.nodes.append(node)
        self.registerNode(node)
        self.grScene.addItem(node.grNode)

    def addEdge(self, edge: NodeEdge) -> None:
        self.sceneCollection.ntm.doStep(
            lambda: self._addEdge(edge), lambda: self._removeEdge(edge)
        )

    def _addEdge(self, edge: NodeEdge) -> None:
        self.edges.append(edge)
        self.grScene.addItem(edge.grEdge)

    def removeNode(self, node: Node) -> None:
        self.sceneCollection.ntm.doStep(
            lambda: self._removeNode(node), lambda: self._addNode(node)
        )

    def _removeNode(self, node: Node) -> None:
        self.nodes.remove(node)
        self.deregisterNode(node)
        self.grScene.removeItem(node.grNode)

    def removeEdge(self, edge: NodeEdge) -> None:
        self.sceneCollection.ntm.doStep(
            lambda: self._removeEdge(edge), lambda: self._addEdge(edge)
        )

    def _removeEdge(self, edge: NodeEdge) -> None:
        self.edges.remove(edge)
        self.grScene.removeItem(edge.grEdge)

    def loadState(self, state: Dict[str, Any], factory: ComfyFactory) -> List[Node]:
        nodes: List[Node] = []
        for nodeState in state["nodes"]:
            node = factory.loadNode(nodeState["nodeClass"])
            node.loadState(nodeState)
            nodes.append(node)
        for edgeState in state["edges"]:
            edge = NodeEdge.loadState(self, edgeState, nodes)
            if edge is not None:
                edge.updateConnections()

        return nodes

    def saveState(self, fromSelected: bool = False) -> Dict[str, Any]:
        savedNodes = []
        nodesToSave = self.nodes
        for node in nodesToSave:
            savedNodes.append(node.saveState())
        nodeMapping = {n: i for i, n in enumerate(nodesToSave)}
        savedEdges = []
        for edge in self.edges:
            savedEdge = edge.saveState(nodeMapping)
            if savedEdge is not None:
                savedEdges.append(savedEdge)
        return {"nodes": savedNodes, "edges": savedEdges}
