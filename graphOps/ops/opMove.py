from __future__ import annotations
from typing import TYPE_CHECKING, List

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor

from graphOps import GraphOp, GR_OP_STATUS, registerOp

if TYPE_CHECKING:
    from nodeGUI import BaseGrNode
    from gui.view import QNodeGraphicsView

MouseButton = QGui.Qt.MouseButton
KeyboardModifier = QGui.Qt.KeyboardModifier


@registerOp
class OpMove(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__([QGui.QKeySequence(QGui.Qt.Key.Key_G)], 1, True)
        self.moving = False
        self.selection: List[BaseGrNode] = []
        self.positions: List[QCor.QPointF] = []
        self.cursorPosition: QCor.QPointF = QCor.QPointF(0.0, 0.0)
        self.scale = 1.0

    def doAction(self, nodeView: QNodeGraphicsView) -> GR_OP_STATUS:
        if self.moving:
            return GR_OP_STATUS.NOTHING
        self.selection = nodeView.getSelected()
        if len(self.selection) == 0:
            return GR_OP_STATUS.NOTHING
        self.moving = True
        self.selection = nodeView.getSelected()
        self.positions = [x.pos() for x in self.selection]
        self.cursorPosition = nodeView.mapToScene(
            nodeView.mapFromGlobal(QGui.QCursor.pos())
        )
        # nodeView.setMouseTracking(True)
        return GR_OP_STATUS.START | GR_OP_STATUS.BLOCK

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        # nodeView.setMouseTracking(False)
        if self.moving:
            if event.button() == MouseButton.LeftButton:
                self.moving = False
                with nodeView.nodeScene.sceneCollection.ntm:
                    offset = (
                        nodeView.mapToScene(nodeView.mapFromGlobal(event.globalPos()))
                        - self.cursorPosition
                    )
                    for item, pos in zip(self.selection, self.positions):
                        nodeView.nodeScene.sceneCollection.ntm.doStep(
                            lambda: item.setPos(pos + offset), lambda: item.setPos(pos)
                        )
                return GR_OP_STATUS.FINISH | GR_OP_STATUS.BLOCK
            elif event.button() == MouseButton.RightButton:
                self.moving = False
                for item, pos in zip(self.selection, self.positions):
                    item.setPos(pos)
                return GR_OP_STATUS.FINISH | GR_OP_STATUS.BLOCK
            else:
                return GR_OP_STATUS.NOTHING | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.NOTHING

    def onMouseMove(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if self.moving:
            offset = (
                nodeView.mapToScene(nodeView.mapFromGlobal(event.globalPos()))
                - self.cursorPosition
            )
            for item, pos in zip(self.selection, self.positions):
                item.setPos(pos + offset)
            return GR_OP_STATUS.NOTHING | GR_OP_STATUS.BLOCK
        return GR_OP_STATUS.NOTHING
