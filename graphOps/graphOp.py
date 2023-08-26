from __future__ import annotations
from typing import List, TYPE_CHECKING, Any, List, Type, Set

if TYPE_CHECKING:
    from gui.view import QNodeGraphicsView

import PySide6.QtGui as QGui
from enum import Flag


class GR_OP_STATUS(Flag):
    NOTHING = 0
    START = 1
    FINISH = 2
    BLOCK = 4


class GraphOp:
    @property
    def shortcuts(self) -> List[QGui.QKeySequence]:
        return self._shortcuts

    @shortcuts.setter
    def shortcuts(self, value: List[QGui.QKeySequence]) -> None:
        self._shortcuts = value

    @property
    def priority(self) -> int:
        return self._priority

    @priority.setter
    def priority(self, value: int) -> None:
        self._priority = value

    @property
    def action(self) -> QGui.QAction | None:
        return self._action

    @property
    def isAction(self) -> bool:
        return self._isAction

    def __init__(
        self, shortcuts: List[QGui.QKeySequence], priority: int, isAction: bool = True
    ) -> None:
        self._shortcuts = shortcuts
        self._priority = priority
        self._action = None
        self._isAction = isAction
        if len(self.shortcuts) != 0 and self.isAction:
            self._action = QGui.QAction()
            self._action.setShortcuts(self.shortcuts)
            # self.action.triggered.connect(self.doAction)

    def ProcessAction(self, nodeView: QNodeGraphicsView) -> None:
        if nodeView.activeOp is not None and nodeView.activeOp == self:
            return
        result = self.doAction(nodeView)
        if GR_OP_STATUS.START in result:
            self.grabView(nodeView)
        elif GR_OP_STATUS.FINISH in result and nodeView.activeOp == self:
            self.releaseView(nodeView)

    def grabView(self, nodeView: QNodeGraphicsView) -> None:
        nodeView.activeOp = self

    def releaseView(self, nodeView: QNodeGraphicsView) -> None:
        nodeView.activeOp = None

    def doAction(self, nodeView: QNodeGraphicsView) -> GR_OP_STATUS:
        return GR_OP_STATUS.NOTHING

    def onMouseDown(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        return GR_OP_STATUS.NOTHING

    def onMouseMove(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        return GR_OP_STATUS.NOTHING

    def onMouseUp(
        self, event: QGui.QMouseEvent, nodeView: QNodeGraphicsView
    ) -> GR_OP_STATUS:
        return GR_OP_STATUS.NOTHING


_opsToLoad: Set[Any] = set()


def registerOp(opCls: Type[GraphOp]) -> Type[GraphOp]:
    _opsToLoad.add(opCls)
    return opCls


def loadOps() -> List[GraphOp]:
    ops: List[GraphOp] = [x() for x in _opsToLoad]
    ops.sort(key=lambda x: x.priority)
    return ops
