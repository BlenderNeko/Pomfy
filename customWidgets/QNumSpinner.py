from typing import Callable, Any
import decimal
from decimal import Decimal
import PySide6.QtCore as QCor
import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt

from customWidgets.QSpinnerWidget import QGraphicsSpinnerItem


class QNumSpinner(QGraphicsSpinnerItem):
    """
    A GraphicsItem that functions as a numerical spinner widget.
    When holding the right mouse button over the name or value and moving left and right, the value will in or decrease.

    The buttons on the side decrease/increase the value by one step per click.
    Clicking on the spinner will instead show an Edit box to change the value directly.
    """

    def __init__(
        self,
        name: str,
        width: float,
        height: float,
        onValueChanged: Callable[[QGui.QUndoCommand], None],
        isFloat: bool,
        default: int | Decimal = 0,
        min: int | Decimal | None = None,
        max: int | Decimal | None = None,
        step: int | Decimal | None = None,
        valid: int | Decimal | None = None,
        validOffset: int | Decimal | None = None,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        self._isFloat = isFloat
        self._valid = valid
        self._validOffset = validOffset
        self._value = default
        self._step: int | Decimal | None = None
        if step is None:
            if self._isFloat:
                self._step = Decimal("0.1")
            else:
                self._step = 1
        else:
            self._step = step
        self._min = min
        self._max = max

        super().__init__(name, default, width, height, onValueChanged, parent)

    def initUI(self) -> None:
        super().initUI()
        self._editBox = CustomLineEdit()
        self._editBox.setText(str(self.value))
        self._editBox.setAlignment(QGui.Qt.AlignmentFlag.AlignRight)
        self._editBox.focus_out.connect(self.toSpin)
        self._editBoxProxy = QWgt.QGraphicsProxyWidget(self)
        self._editBoxProxy.setWidget(self._editBox)
        self._editBoxProxy.setGeometry(0, 0, self._width, self._height)
        self._editBoxProxy.hide()

    def getDisplayValue(self) -> str:
        if self._isFloat:
            assert isinstance(self._value, Decimal)
            value = f"{self._value}"
        else:
            assert isinstance(self._value, int)
            value = f"{self._value:d}"
        return value

    def changeValue(self, value: int | Decimal) -> int | Decimal:
        if self._min is not None:
            value = max(self._min, value)
        if self._max is not None:
            value = min(self._max, value)
        if self._valid is not None:
            if self._validOffset is not None:
                value = (
                    round((value - self._validOffset) / self._valid) * self._valid
                    + self._validOffset
                )
            else:
                value = round(value / self._valid) * self._valid
        return value if self._isFloat else int(value)

    def updateEditBox(self) -> None:
        self._editBox.setText(self.getDisplayValue())

    def toEdit(self) -> None:
        self.updateEditBox()
        self.shouldBlock = True
        self.spinner.hide()
        self._editBoxProxy.show()

    def toSpin(self) -> None:
        self.shouldBlock = False
        self.value = Decimal(self._editBox.text())
        self._editBox.hide()
        self.spinner.show()

    def makeStep(self, x: int) -> None:
        if self._isFloat:
            assert isinstance(self._step, Decimal)
            self.value += Decimal(x) * self._step
        else:
            assert isinstance(self._step, int)
            self.value += x * self._step

    def onSpinnerClick(self) -> None:
        self.toEdit()
        self._editBox.setFocus()


class CustomLineEdit(QWgt.QLineEdit):
    """used internally to limit valid keys, and monitor when to close and change the value"""

    focus_out = QCor.Signal()

    def __init__(self, parent: QWgt.QWidget | None = None):
        super().__init__(parent)
        self.setFocusPolicy(QGui.Qt.FocusPolicy.NoFocus)

    def focusOutEvent(self, event: QGui.QFocusEvent) -> None:
        self.focus_out.emit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event: QGui.QKeyEvent) -> None:
        if (
            event.key() == QGui.Qt.Key.Key_Enter
            or event.key() == QGui.Qt.Key.Key_Return
        ):
            self.clearFocus()
            self.focus_out.emit()
            return
        if (
            event.key()
            not in [
                QGui.Qt.Key.Key_Backspace,
                QGui.Qt.Key.Key_Left,
                QGui.Qt.Key.Key_Right,
            ]
            and event.text() not in "1234567890."
        ):
            return
        return super().keyPressEvent(event)
