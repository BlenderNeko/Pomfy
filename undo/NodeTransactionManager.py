from typing import Callable, List, Type, Any
from PySide6.QtGui import QUndoStack, QUndoCommand
from enum import Enum

# TODO: test multi level enter/exit?


class NTMUndoCommand(QUndoCommand):
    def __init__(
        self,
        redoOps: List[Callable[[], None]],
        undoOps: List[Callable[[], None]],
        performRedo: bool = False,
    ) -> None:
        super().__init__()
        self.performRedo = performRedo
        self.redoOps = redoOps
        self.undoOps = undoOps

    def redo(self) -> None:
        if self.performRedo:
            for op in self.redoOps:
                op()
        self.performRedo = True

    def undo(self) -> None:
        for op in self.undoOps:
            op()


class OPTYPE(Enum):
    NONE = 0
    REDO = 1
    UNDO = 2


# should this become a singleton?
class NTM:
    def __init__(self, undoStack: QUndoStack) -> None:
        self.undoStack = undoStack
        self._redoOps: List[List[Callable[[], None]]] = []
        self._undoOps: List[List[Callable[[], None]]] = []

    def undo(self) -> None:
        if len(self._redoOps) == 0:
            self.undoStack.undo()

    def redo(self) -> None:
        if len(self._redoOps) == 0:
            self.undoStack.redo()

    def startTransaction(self) -> None:
        self._redoOps.append([])
        self._undoOps.append([])

    def abortTransaction(self, performOps: OPTYPE = OPTYPE.NONE) -> None:
        redoOps = self._redoOps.pop()
        undoOps = self._undoOps.pop()
        if performOps == OPTYPE.UNDO:
            undoOps.reverse()
            for op in undoOps:
                op()
        elif performOps == OPTYPE.REDO:
            for op in redoOps:
                op()

    def finalizeTransaction(self) -> None:
        print(len(self._redoOps))
        redoOps = self._redoOps.pop()
        undoOps = self._undoOps.pop()

        if len(self._redoOps) == 0:
            undoOps.reverse()
            undoCom = NTMUndoCommand(redoOps, undoOps)
            self.undoStack.push(undoCom)
            return
        self._redoOps[-1].extend(redoOps)
        self._undoOps[-1].extend(undoOps)

    def doStep(self, redo: Callable[[], None], undo: Callable[[], None]) -> None:
        if len(self._redoOps) == 0:
            return redo()
        redo()
        self._redoOps[-1].append(redo)
        self._undoOps[-1].append(undo)

    def __enter__(self) -> None:
        self.startTransaction()

    def __exit__(self, type: Type, value: Any, traceback: Any) -> None:
        self.finalizeTransaction()
