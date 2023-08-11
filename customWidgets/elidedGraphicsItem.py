from typing import Sequence
from PySide6.QtWidgets import QGraphicsSimpleTextItem, QGraphicsItem
from PySide6.QtGui import QFontMetrics, QFont
from PySide6.QtCore import Qt


class QGraphicsElidedTextItem(QGraphicsSimpleTextItem):
    """A QGraphicTextItem that automatically elids text to fit within a certain width"""

    @property
    def alignLeft(self) -> bool:
        """Wether the text should align left or not."""
        return self._alignLeft

    @alignLeft.setter
    def alignLeft(self, value: bool) -> None:
        self._alignLeft = value

    @property
    def elidedMode(self) -> Qt.TextElideMode:
        """Wether to elid left or right or both"""
        return self._elidedMode

    @elidedMode.setter
    def elidedMode(self, value: Qt.TextElideMode) -> None:
        self._elidedMode = value
        self.resize(self._width)

    @property
    def rawText(self) -> str:
        """The unelided text."""
        return self._raw_text

    @rawText.setter
    def rawText(self, value: str) -> None:
        self._raw_text = value
        self.resize(self._width)

    @property
    def textWidth(self) -> int:
        """The width of the text."""
        return self._metrics.horizontalAdvance(self._raw_text)

    def setFont(self, font: QFont | str | Sequence[str]) -> None:
        """Sets the Text font."""
        super().setFont(font)
        self._metrics = QFontMetrics(self.font())

    def __init__(
        self,
        text: str,
        width: float,
        height: float,
        font: QFont | None = None,
        elidedMode: Qt.TextElideMode = Qt.TextElideMode.ElideRight,
        alignLeft: bool = True,
        parent: QGraphicsItem | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._raw_text = text
        if font is not None:
            self.setFont(font)
        self._metrics = QFontMetrics(self.font())
        self._width = width
        self._alignLeft = alignLeft
        self._elidedMode = elidedMode
        self._boxHeight = height
        self._x = 0.0
        self._y = 0.0
        self._offset()
        self.resize(self._width)

    def setAlignedPos(self, x: float, y: float) -> None:
        """Set position of item"""
        self._x = x
        self._y = y
        self.setPos(self._wOffset + x, self._hOffset + y)

    def _offset(self) -> None:
        bbox = self.boundingRect()
        height = bbox.height()
        width = bbox.width()
        self._hOffset = (self._boxHeight - height) / 2
        if self._alignLeft:
            self._wOffset = 0.0
        else:
            self._wOffset = self._width - width

    def resize(self, width: float) -> None:
        """Resizes the text area to the new width."""
        self._width = width
        text = self._metrics.elidedText(self._raw_text, self._elidedMode, int(width))
        self.setText(text)
        self._offset()
        self.setAlignedPos(self._x, self._y)
