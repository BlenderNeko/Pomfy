from __future__ import annotations
from typing import TYPE_CHECKING, List

import PySide6.QtGui as QGui
import PySide6.QtCore as QCor

from graphOps import GraphOp, GR_OP_STATUS, registerOp
from graphOps.ops.opMove import OpMove

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView
    from node import Node

MouseButton = QGui.Qt.MouseButton
KeyboardModifier = QGui.Qt.KeyboardModifier


@registerOp
class OpAddNode(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            [
                QGui.QKeySequence(
                    QCor.QKeyCombination(
                        QGui.Qt.KeyboardModifier.ShiftModifier, QGui.Qt.Key.Key_A
                    )
                )
            ],
            1,
            True,
        )
        self.NodeName: str | None = None

    def doAction(self, nodeView: QNodeGraphicsView) -> GR_OP_STATUS:
        self.nodeView: QNodeGraphicsView | None = nodeView
        menu = nodeView.nodeScene.sceneCollection.nodeFactory.GenerateMenu(
            self.onCreate
        )
        with nodeView.nodeScene.sceneCollection.ntm:
            menu.exec(QGui.QCursor.pos())

        return GR_OP_STATUS.FINISH

    def onCreate(self, node: Node) -> None:
        assert self.nodeView is not None
        selected = self.nodeView.getSelected()
        for item in selected:
            item.setSelected(False)
        node.grNode.setSelected(True)
        node.grNode.setPos(
            self.nodeView.mapToScene(self.nodeView.mapFromGlobal(QGui.QCursor.pos()))
        )
        for op in self.nodeView._graphOps:
            if isinstance(op, OpMove):
                op.ProcessAction(self.nodeView)
        self.nodeView = None
