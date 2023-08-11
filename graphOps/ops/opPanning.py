from __future__ import annotations
from typing import TYPE_CHECKING

import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt

from graphOps import GraphOp, GR_OP_STATUS, registerOp

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView

MouseButton = QGui.Qt.MouseButton


@registerOp
class OpPanning(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__([], 1, False)

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if event.button() != MouseButton.MiddleButton:
            return GR_OP_STATUS.NOTHING
        nodeView.disableMouseEvents()
        nodeView.setDragMode(QWgt.QGraphicsView.DragMode.ScrollHandDrag)
        fakeEvent = QGui.QMouseEvent(
            event.type(),
            event.localPos(),
            event.screenPos(),
            MouseButton.LeftButton,
            event.buttons() | MouseButton.LeftButton,
            event.modifiers(),
        )

        super(type(nodeView), nodeView).mousePressEvent(fakeEvent)
        return GR_OP_STATUS.START | GR_OP_STATUS.BLOCK

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if event.button() != MouseButton.MiddleButton:
            return GR_OP_STATUS.NOTHING
        nodeView.enableMouseEvents()
        fakeEvent = QGui.QMouseEvent(
            event.type(),
            event.localPos(),
            event.screenPos(),
            MouseButton.LeftButton,
            event.buttons() & ~MouseButton.LeftButton,
            event.modifiers(),
        )
        super(type(nodeView), nodeView).mouseReleaseEvent(fakeEvent)
        nodeView.setDragMode(QWgt.QGraphicsView.DragMode.NoDrag)
        nodeView.releaseMouse()
        return GR_OP_STATUS.FINISH | GR_OP_STATUS.BLOCK
