from __future__ import annotations
from typing import TYPE_CHECKING

import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt

from graphOps import GraphOp, GR_OP_STATUS, registerOp
from nodeGUI import BaseGrNode, GrNode

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView

MouseButton = QGui.Qt.MouseButton
KeyboardModifier = QGui.Qt.KeyboardModifier

# TODO: actual active items


@registerOp
class OpActive(GraphOp):
    def __init__(
        self,
    ) -> None:
        super().__init__([], -1, False)

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if (
            event.button() == MouseButton.LeftButton
            and event.modifiers() == KeyboardModifier.ControlModifier
        ):
            nodeView.setDragMode(QWgt.QGraphicsView.DragMode.RubberBandDrag)
        if (
            event.button() == MouseButton.LeftButton
            and event.modifiers() == KeyboardModifier.NoModifier
        ):
            nodeView.setDragMode(QWgt.QGraphicsView.DragMode.RubberBandDrag)
            item = nodeView.itemAt(event.pos())
            if not isinstance(item, BaseGrNode):
                while item is not None:
                    item = item.parentItem()
                    if isinstance(item, BaseGrNode):
                        break
            if item is not None:
                selected = nodeView.getSelected()
                for s in selected:
                    s.setSelected(False)
                item.setSelected(True)
            # TODO: why does mypy complain?
            nodeView.activeNode = item  # type: ignore

            return GR_OP_STATUS.FINISH
        return GR_OP_STATUS.NOTHING

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        if event.button() != MouseButton.LeftButton:
            return GR_OP_STATUS.NOTHING
        nodeView.setDragMode(QWgt.QGraphicsView.DragMode.NoDrag)
        selected = nodeView.getSelected()
        if len(selected) == 0:
            return GR_OP_STATUS.NOTHING
        return GR_OP_STATUS.FINISH
