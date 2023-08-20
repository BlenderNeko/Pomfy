# TODO: somehow disable pageup pagedown navigation stuff

from __future__ import annotations

from typing import TYPE_CHECKING, List, Callable

import PySide6.QtGui

from style.socketStyle import SocketStyles

if TYPE_CHECKING:
    from graphOps import GraphOp
    from node import NodeEdge, NodeScene

from graphOps import loadOps, GR_OP_STATUS


from functools import partial

from nodeGUI import BaseGrNode

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor
import PySide6.QtWidgets as QWgt


class QNodeGraphicsView(QWgt.QGraphicsView):
    @property
    def activeOp(self) -> GraphOp | None:
        return self._activeOp

    @activeOp.setter
    def activeOp(self, value: GraphOp | None) -> None:
        self._activeOp = value

    def __init__(
        self, nodeScene: NodeScene, parent: QWgt.QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.grScene = nodeScene.grScene
        self.nodeScene = nodeScene

        # used to temporarily disable mouse events of items
        self._node_mouse_states: List[QGui.Qt.MouseButton] = []
        self._mouse_state_at_cursor = QGui.Qt.MouseButton.NoButton
        self._item_at_cursor: QWgt.QGraphicsItem | None = None

        # used when dragging edges
        self._dragged_edge: NodeEdge | None = None

        # zoom settings
        self.zoomInFac = 1.25
        self.zoom = 8
        self.zoomStep = 1
        self.zoomRange = (0, 12)

        self._activeOp = None

        self.setScene(self.grScene)
        self.initUI()
        self.initActions()
        self.initGraphOps()

    def initUI(self) -> None:
        self.setRenderHints(
            QGui.QPainter.RenderHint.Antialiasing
            | QGui.QPainter.RenderHint.TextAntialiasing
            | QGui.QPainter.RenderHint.SmoothPixmapTransform
        )

        self.setViewportUpdateMode(
            QWgt.QGraphicsView.ViewportUpdateMode.FullViewportUpdate
        )

        self.setHorizontalScrollBarPolicy(QGui.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QGui.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.horizontalScrollBar().blockSignals(True)
        self.verticalScrollBar().blockSignals(True)
        self.setTransformationAnchor(QWgt.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def disableMouseEvents(self) -> None:
        self._node_mouse_states = []
        for item in self.nodeScene.nodes:
            self._node_mouse_states.append(item.grNode.acceptedMouseButtons())
            item.grNode.setAcceptedMouseButtons(QGui.Qt.MouseButton.NoButton)
        self._item_at_cursor = self.itemAt(self.mapFromGlobal(QGui.QCursor.pos()))
        if self._item_at_cursor is not None:
            self._mouse_state_at_cursor = self._item_at_cursor.acceptedMouseButtons()
            self._item_at_cursor.setAcceptedMouseButtons(QGui.Qt.MouseButton.NoButton)

    def enableMouseEvents(self) -> None:
        if self._item_at_cursor is not None:
            self._item_at_cursor.setAcceptedMouseButtons(self._mouse_state_at_cursor)
        for item, buttons in zip(self.nodeScene.nodes, self._node_mouse_states):
            item.grNode.setAcceptedMouseButtons(buttons)

    def initGraphOps(self) -> None:
        self._graphOps = loadOps()
        for op in self._graphOps:
            if op.isAction and op.action is not None:
                op.action.triggered.connect(partial(op.ProcessAction, self))
                self.addAction(op.action)

    def initActions(self) -> None:
        self.undoAction = QGui.QAction()
        self.undoAction.setShortcut(
            QCor.QKeyCombination(
                QGui.Qt.KeyboardModifier.ControlModifier, QGui.Qt.Key.Key_Z
            )
        )
        self.undoAction.triggered.connect(self.performUndo)
        self.addAction(self.undoAction)

        self.redoAction = QGui.QAction()
        self.redoAction.setShortcut(
            QCor.QKeyCombination(
                QGui.Qt.KeyboardModifier.ControlModifier
                | QGui.Qt.KeyboardModifier.ShiftModifier,
                QGui.Qt.Key.Key_Z,
            )
        )
        self.redoAction.triggered.connect(self.performRedo)
        self.addAction(self.redoAction)

        self.promptAction = QGui.QAction()
        self.promptAction.setShortcut(
            QCor.QKeyCombination(
                QGui.Qt.KeyboardModifier.ShiftModifier,
                QGui.Qt.Key.Key_F5,
            )
        )
        self.promptAction.triggered.connect(self.performPrompt)
        self.addAction(self.promptAction)

    def save(self) -> None:
        self.nodeScene.sceneCollection.toJSON()

    def performPrompt(self) -> None:
        self.nodeScene.sceneCollection.prompt()

    def performUndo(self) -> None:
        self.nodeScene.undo()

    def performRedo(self) -> None:
        self.nodeScene.redo()

    def getSelected(self) -> List[BaseGrNode]:
        return [x for x in self.items() if x.isSelected() and isinstance(x, BaseGrNode)]

    def keyPressEvent(self, event: QGui.QKeyEvent) -> None:
        super().keyPressEvent(event)

    def processMouseOps(self, func: Callable[[GraphOp], GR_OP_STATUS]) -> GR_OP_STATUS:
        # print(self.activeOp)
        if self.activeOp is not None:
            result = func(self.activeOp)
            if GR_OP_STATUS.FINISH in result:
                self.activeOp = None
            return result
        else:
            should_block = False
            for op in self._graphOps:
                result = func(op)
                if GR_OP_STATUS.BLOCK in result:
                    should_block = True
                if GR_OP_STATUS.START in result:
                    self.activeOp = op
                    return result
            if should_block:
                return result | GR_OP_STATUS.BLOCK
            else:
                return result

    def mousePressEvent(self, event: QGui.QMouseEvent) -> None:
        result = self.processMouseOps(lambda x: x.onMouseDown(event, self))
        if GR_OP_STATUS.BLOCK not in result:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QGui.QMouseEvent) -> None:
        result = self.processMouseOps(lambda x: x.onMouseMove(event, self))
        if GR_OP_STATUS.BLOCK not in result:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QGui.QMouseEvent) -> None:
        result = self.processMouseOps(lambda x: x.onMouseUp(event, self))
        if GR_OP_STATUS.BLOCK not in result:
            return super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QGui.QWheelEvent) -> None:
        if self.activeOp is None:
            isZoomIn = event.angleDelta().y() > 0

            if ((not isZoomIn) and self.zoom <= self.zoomRange[0]) or (
                isZoomIn and self.zoom >= self.zoomRange[1]
            ):
                return

            zoomFac = self.zoomInFac if isZoomIn else 1 / self.zoomInFac
            self.zoom += self.zoomStep if isZoomIn else -self.zoomStep

            self.scale(zoomFac, zoomFac)
