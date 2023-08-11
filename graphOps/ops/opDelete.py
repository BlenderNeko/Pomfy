from __future__ import annotations
from typing import TYPE_CHECKING

from graphOps.graphOp import GR_OP_STATUS

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from graphOps import GraphOp, registerOp
from PySide6.QtGui import *
from nodeGUI.node import GrNode


@registerOp
class OpDelete(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            [QKeySequence(Qt.Key.Key_X), QKeySequence(Qt.Key.Key_Delete)], 1, True
        )

    def doAction(self, nodeView: QNodeGraphicsView) -> GR_OP_STATUS:
        selection = nodeView.getSelected()
        if len(selection) == 0:
            return GR_OP_STATUS.NOTHING
        with nodeView.nodeScene.sceneCollection.ntm:
            for item in selection:
                if isinstance(item, GrNode):
                    item.node.remove()

        return GR_OP_STATUS.FINISH
