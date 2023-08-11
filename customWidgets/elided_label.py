from PySide6.QtWidgets import QWidget, QLabel
from PySide6.QtGui import QFontMetrics, QFont
from PySide6.QtCore import Qt


class QElidedLabel(QLabel):
    def __init__(
        self,
        text: str,
        font: QFont,
        elided_mode: Qt.TextElideMode = Qt.TextElideMode.ElideRight,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._raw_text = text
        self._font = font
        self._metrics = QFontMetrics(self._font)
        self._elided_mode = elided_mode

    def resizeToWidth(self, width: int) -> None:
        self.setFixedWidth(width)
        text = self._metrics.elidedText(self._raw_text, self._elided_mode, width)
        self.setText(text)
