from typing import Any, List, Callable

from customWidgets.QSearchableList import QSearchableMenu
from customWidgets.QSpinnerWidget import QGraphicsSpinnerItem
import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt
import PySide6.QtCore as QCor


class QComboSpinner(QGraphicsSpinnerItem):
    """
    A GraphicsItem that functions as a categorical spinner widget.
    When holding the right mouse button over the name or value and moving left and right, the value will in or decrease.

    The buttons on the side decrease/increase the value by one step per click.
    Clicking on the spinner will instead show an filterable list of categories to pick from directly.
    """

    def __init__(
        self,
        name: str,
        width: float,
        height: float,
        onValueChanged: Callable[[QGui.QUndoCommand], None],
        items: List[str],
        selected: str,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        self.items = items
        self.num_items = len(self.items)
        self.renderFunc = lambda x: x
        self.FilterFunc = lambda x, y: y.lower() in x.lower()
        super().__init__(name, selected, width, height, onValueChanged, parent)

    def initUI(self) -> None:
        super().initUI()
        self.initSpinner()

    def initSpinner(self) -> None:
        self._combobox = QSearchableMenu(self.items, self.renderFunc, self.FilterFunc)
        self._combobox.finished.connect(self.comboFinished)
        self._combobox.hide()
        self._combobox.setWindowFlags(
            QGui.Qt.WindowType.Popup | QGui.Qt.WindowType.BypassGraphicsProxyWidget
        )
        self.spinner.spinSensitivity = 200

    def getDisplayValue(self) -> str:
        return self.value

    def updateItems(self, items: List[str]) -> None:
        self.items = items
        self.num_items = len(self.items)
        self.undoRedoEnabled = False
        self.value = self.items[0] if self.num_items > 0 else ""
        self.undoRedoEnabled = True
        self._combobox.finished.disconnect(self.comboFinished)
        self.initSpinner()

    def changeValue(self, value: Any) -> Any:
        return value

    def toCombo(self) -> None:
        if self.num_items > 0:
            self._combobox.move(QGui.QCursor.pos() + QCor.QPoint(5, -5))
            self._combobox.clearText()
            self._combobox.indToTop(self.items.index(self.value))
            self._combobox.show()

    def comboFinished(self, ind: int) -> None:
        self.value = self.items[ind]

    def makeStep(self, x: int) -> None:
        if self.num_items > 0:
            ind = self.items.index(self.value)
            ind = max(0, min(ind + x, len(self.items) - 1))
            self.value = self.items[ind]

    def onSpinnerClick(self) -> None:
        self.toCombo()
