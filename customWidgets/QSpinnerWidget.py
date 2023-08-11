from typing import Any, Callable

import PySide6.QtCore as QCor
import PySide6.QtGui as QGui
import PySide6.QtWidgets as QWgt
from PySide6.QtCore import QPointF, QRectF

from customWidgets import QGraphicsElidedTextItem
from customWidgets import QSlotContentGraphicsItem
from constants import SLOT_MIN_HEIGHT


class QCUndoCommand(QGui.QUndoCommand):
    """Undo Command for the QSpinnerWidget"""

    def __init__(
        self, spinner: "QGraphicsSpinnerItem", previous: Any, current: Any
    ) -> None:
        self.spinner = spinner
        self.previous = previous
        self.current = current
        super().__init__()

    def undo(self) -> None:
        old = self.spinner._undoRedoEnabled
        self.spinner._undoRedoEnabled = False

        self.spinner.value = self.previous

        self.spinner._undoRedoEnabled = old

    def redo(self) -> None:
        old = self.spinner._undoRedoEnabled
        self.spinner._undoRedoEnabled = False

        self.spinner.value = self.current

        self.spinner._undoRedoEnabled = old


class Spinner(QSlotContentGraphicsItem):
    """
    A GraphicsItem that functions as a spinner widget.
    When holding the right mouse button and moving left and right, the value will in or decrease.

    """

    @property
    def spinning(self) -> bool:
        return self._spinning

    def __init__(
        self,
        name: str,
        width: float,
        height: float,
        spinnerItem: "QGraphicsSpinnerItem",
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._spinnerItem = spinnerItem
        self._width = width
        self._height = height
        self._name = name
        self.shouldBlock = False

        self._clicked = False
        self._spinning = False

        self._click_location = QPointF(0, 0)
        self._delta = QPointF(0, 0)
        self.spinSensitivity = 10
        self._spin_ticks = 0

        self.initUI()

    def initUI(self) -> None:
        self.nameLabel = QGraphicsElidedTextItem(
            self._name,
            self._width / 2,
            self._height,
            elidedMode=QGui.Qt.TextElideMode.ElideRight,
            alignLeft=True,
        )
        self._nameLabelWidth = float(self.nameLabel.textWidth)
        nameWidth = min(self._nameLabelWidth, self._width / 2)
        self.nameLabel.resize(nameWidth)

        self.nameLabel.setParentItem(self)
        self.nameLabel.setAlignedPos(0, 0)

        self.valueLabel = QGraphicsElidedTextItem(
            "",
            self._width - nameWidth,
            self._height,
            elidedMode=QGui.Qt.TextElideMode.ElideLeft,
            alignLeft=False,
        )
        self.valueLabel.setParentItem(self)
        self.valueLabel.setAlignedPos(nameWidth, 0)

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = ...,
    ) -> None:
        pass

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    def resize(self, width: float) -> None:
        """Resize the widget to fit within given width."""
        self.prepareGeometryChange()
        self._width = width
        nameWidth = min(self._nameLabelWidth, self._width / 2)
        self.nameLabel.resize(nameWidth)

        self.valueLabel.resize(self._width - nameWidth)
        self.valueLabel.setAlignedPos(nameWidth, 0)

    def mousePressEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        if event.button() == QGui.Qt.MouseButton.LeftButton and not self.shouldBlock:
            self._click_location = QPointF(QGui.QCursor.pos())
            QWgt.QApplication.setOverrideCursor(QGui.Qt.CursorShape.BlankCursor)
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        # ignore spinning function when shouldBlock is true
        if self.shouldBlock:
            return super().mousePressEvent(event)
        self._delta += QCor.QPointF(QGui.QCursor.pos()) - self._click_location
        # enter "spinning" mode after moving a certain distance
        if not self.spinning and abs(self._delta.x()) > 5:
            self._delta = QPointF(0, 0)
            self._spinning = True
            self._spin_ticks = 0
            self._valueBeforeSpinning = self._spinnerItem.value
            self._spinnerItem._undoRedoEnabled = False
        # spinning
        if self.spinning:
            dx = round(self._delta.x() / self.spinSensitivity) - self._spin_ticks
            if dx != 0:
                self._spinnerItem.makeStep(dx)
                self._spin_ticks += dx
                QGui.QCursor.setPos(self._click_location.toPoint())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        QWgt.QApplication.restoreOverrideCursor()
        # update value on mouse release
        if event.button() == QCor.Qt.MouseButton.LeftButton and not self.shouldBlock:
            if self.spinning:
                self._delta = QPointF(0, 0)
                self._spinning = False
                self._spinnerItem._undoRedoEnabled = True
                self._spinnerItem._onValueChanged(
                    QCUndoCommand(
                        self._spinnerItem,
                        self._valueBeforeSpinning,
                        self._spinnerItem.value,
                    )
                )
            else:
                self._spinnerItem.onSpinnerClick()
        super().mouseReleaseEvent(event)


class SpinnerButton(QSlotContentGraphicsItem):
    """The buttons on the side of the spinning widget"""

    def __init__(
        self,
        width: float,
        height: float,
        onClick: Callable[[], None],
        isLeftButton: bool = True,
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._width = width
        self._height = height
        self._onClick = onClick
        self._isLeftButton = isLeftButton
        self.pen = QGui.Qt.PenStyle.NoPen
        self.brush = QGui.QBrush(QGui.QColor("#828282"))
        self.brushPressed = QGui.QBrush(QGui.QColor("#414141"))
        self._isPressed = False
        self.buttonPath = self.createButtonPath()

    def boundingRect(self) -> QCor.QRectF:
        return QCor.QRectF(0, 0, self._width, self._height)

    def createButtonPath(self) -> QGui.QPainterPath:
        buttonPath = QGui.QPainterPath()
        buttonPath.setFillRule(QGui.Qt.FillRule.WindingFill)
        if self._isLeftButton:
            buttonPath.addPolygon(
                [
                    QPointF(self._width, 0),
                    QPointF(self._width, self._height),
                    QPointF(0, self._height / 2),
                ]
            )
        else:
            buttonPath.addPolygon(
                [
                    QPointF(0, 0),
                    QPointF(0, self._height),
                    QPointF(self._width, self._height / 2),
                ]
            )

        return buttonPath

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        painter.setPen(self.pen)
        painter.setBrush(self.brushPressed if self._isPressed else self.brush)
        painter.drawPath(self.buttonPath)

    def resize(self, width: float) -> None:
        pass

    def mousePressEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        self._isPressed = True
        self.update(self.boundingRect())
        pass

    def mouseReleaseEvent(self, event: QWgt.QGraphicsSceneMouseEvent) -> None:
        if self.boundingRect().contains(event.pos()):
            self._onClick()
        self._isPressed = False
        self.update(self.boundingRect())
        super().mouseReleaseEvent(event)


class QGraphicsSpinnerItem(QSlotContentGraphicsItem):
    """
    A GraphicsItem that functions as a spinner widget.
    When holding the right mouse button over the name or value and moving left and right, the value will in or decrease.

    The buttons on the side decrease/increase the value by one step per click.

    Subclasses should implement `changeValue` which is run after the value changes,
    `getDisplayValue` which converts the value to a string, and `makeStep` defining how steps are to be made.

    Subclasses can also override `onSpinnerClick` which fires when the spinner is clicked instead of spun.
    """

    @property
    def spinning(self) -> bool:
        """wether the user is currently spinning or not"""
        return self.spinner.spinning

    @property
    def value(self) -> Any:
        """the current value hold by the widget"""
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        value = self.changeValue(value)
        if value == self._value:
            return
        old = self._value
        self._value: Any | None = value
        display_value = self.getDisplayValue()
        self.spinner.valueLabel.rawText = display_value
        if self.undoRedoEnabled:
            self._onValueChanged(QCUndoCommand(self, old, value))

    @property
    def undoRedoEnabled(self) -> bool:
        return self._undoRedoEnabled

    @undoRedoEnabled.setter
    def undoRedoEnabled(self, value: bool) -> None:
        self._undoRedoEnabled = value

    def __init__(
        self,
        name: str,
        default: Any,
        width: float,
        height: float,
        onValueChanged: Callable[[QGui.QUndoCommand], None],
        parent: QWgt.QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._width = width
        self._height = height
        self._onValueChanged = onValueChanged
        self._buttonWidth = 25
        self._name = name
        self._undoRedoEnabled = False

        self.initUI()

        self._value = None
        self.value = default
        self._undoRedoEnabled = True

    def initUI(self) -> None:
        self.spinner = Spinner(
            self._name,
            self._width - 2 * self._buttonWidth - 10,
            self._height,
            self,
            self,
        )
        self.spinner.setPos(self._buttonWidth + 5, 0)
        self.buttonLeft = SpinnerButton(
            self._buttonWidth, self._height, lambda: self.makeStep(-1), True, self
        )
        self.buttonRight = SpinnerButton(
            self._buttonWidth, self._height, lambda: self.makeStep(1), False, self
        )
        self.buttonRight.setPos(self._width - self._buttonWidth, 0)

    def paint(
        self,
        painter: QGui.QPainter,
        option: QWgt.QStyleOptionGraphicsItem,
        widget: QWgt.QWidget | None = None,
    ) -> None:
        pass

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    def resize(self, width: float) -> None:
        self.prepareGeometryChange()
        self._width = width
        self.spinner.resize(self._width - 2 * self._buttonWidth - 10)
        self.buttonRight.setPos(self._width - self._buttonWidth, 0)

    def changeValue(self, value: Any) -> Any:
        """Is ran after the value is set to allow for final adjustments."""
        raise NotImplementedError()

    def getDisplayValue(self) -> str:
        """converts the value to a string representation."""
        raise NotImplementedError()

    def makeStep(self, amount: int) -> None:
        """is called whenever the widget is spun or the buttons are pressed. `amount` reflect the number of steps made by the user"""
        raise NotImplementedError()

    def onSpinnerClick(self) -> None:
        """is called when the spinner is clicked instead of spun"""
        pass
